"""Smoke test every site in ansible/vhosts.yml over real HTTP/HTTPS.

    python3 tools/ops/smoke_test.py                  # live, via public DNS
    python3 tools/ops/smoke_test.py --only taiji     # just some sites
    python3 tools/ops/smoke_test.py --staging        # accept staging certs

Also run by tools/dev/test-nginx-local.sh against a local nginx built
from the same templates (--resolve/--http-port/--https-port/--cafile).

Checks per site: a trusted certificate covering every hostname with at
least --min-days left; HTTP -> HTTPS; the ACME challenge path served
over plain HTTP (renewals depend on it); aliases 301 to the canonical
name, path and query preserved; "/" follows Accept-Language (302 +
Vary, unknown languages -> en-US) or serves a page; every locale's home
page and listed sub-pages (vhosts.yml `pages`); every listed redirect, and that its target really loads; the
security headers; the custom 404 page. Once per run: an unknown
hostname is refused at the TLS handshake, and a bare-IP visit gets the
default page (`--only default` checks just that).

Exit 0 when everything passes, 1 otherwise. Stdlib + PyYAML (installed
alongside Ansible); certificate details read with the openssl CLI.
"""

from __future__ import annotations

import argparse
import http.client
import socket
import ssl
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required (it comes with Ansible): apt install python3-yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
VHOSTS_FILE = REPO_ROOT / "ansible" / "vhosts.yml"
DEFAULT_LOCALE = "en-US"


class _SNIConnection(http.client.HTTPSConnection):
    """HTTPS to a chosen IP while presenting `sni` - like curl --resolve."""

    def __init__(self, sni: str, ip: str, port: int, context: ssl.SSLContext):
        super().__init__(ip, port, context=context, timeout=10)
        self._sni = sni

    def connect(self) -> None:
        raw = socket.create_connection((self.host, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw, server_hostname=self._sni)


class Checker:
    def __init__(self, args: argparse.Namespace, hsts_max_age: int):
        self.args = args
        self.hsts_max_age = hsts_max_age
        self.failures = 0
        self.context = ssl.create_default_context(cafile=args.cafile)
        if args.staging:
            # Staging certificates aren't publicly trusted; identity is
            # still checked below via the certificate's names and issuer.
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE

    # --- plumbing -----------------------------------------------------

    def ip_for(self, name: str) -> str:
        return self.args.resolve or socket.gethostbyname(name)

    def get(self, scheme: str, name: str, path: str, headers=None):
        if scheme == "https":
            conn = _SNIConnection(
                name, self.ip_for(name), self.args.https_port, self.context
            )
        else:
            conn = http.client.HTTPConnection(
                self.ip_for(name), self.args.http_port, timeout=10
            )
        try:
            conn.request("GET", path, headers={"Host": name, **(headers or {})})
            resp = conn.getresponse()
            return resp.status, resp.headers, resp.read()
        finally:
            conn.close()

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        print(
            f"{'PASS' if ok else 'FAIL'}  {label}"
            + (f" - {detail}" if detail and not ok else "")
        )
        if not ok:
            self.failures += 1
        return ok

    def peer_cert(self, name: str) -> str:
        raw = socket.create_connection((self.ip_for(name), self.args.https_port), 10)
        with self.context.wrap_socket(raw, server_hostname=name) as tls:
            der = tls.getpeercert(binary_form=True)
        out = subprocess.run(
            [
                "openssl",
                "x509",
                "-inform",
                "DER",
                "-noout",
                "-enddate",
                "-issuer",
                "-ext",
                "subjectAltName",
            ],
            input=der,
            capture_output=True,
            check=True,
        )
        return out.stdout.decode()

    # --- checks -------------------------------------------------------

    def certificate(self, vhost: dict, names: list[str]) -> None:
        label = f"{vhost['name']}: certificate"
        try:
            text = self.peer_cert(vhost["canonical"])
        except (OSError, ssl.SSLError, subprocess.CalledProcessError) as exc:
            self.check(False, label, str(exc))
            return
        end = text.split("notAfter=", 1)[1].splitlines()[0].strip()
        expires = datetime.strptime(end, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)
        days = (expires - datetime.now(UTC)).days
        self.check(
            days >= self.args.min_days,
            f"{label} valid {days} more days",
            f"needs >= {self.args.min_days}",
        )
        missing = [n for n in names if f"DNS:{n}" not in text]
        self.check(
            not missing, f"{label} covers {', '.join(names)}", f"missing {missing}"
        )
        staging = "STAGING" in text
        self.check(
            staging == self.args.staging,
            f"{label} is {'staging' if staging else 'production'}",
            "re-run with --staging" if staging else "expected staging",
        )

    def redirect(
        self,
        label: str,
        scheme: str,
        name: str,
        path: str,
        status: int,
        host: str,
        target: str,
        headers=None,
    ) -> str | None:
        try:
            got, hdrs, _ = self.get(scheme, name, path, headers)
        except (OSError, ssl.SSLError) as exc:
            self.check(False, label, str(exc))
            return None
        loc = urlsplit(hdrs.get("Location", ""))
        loc_target = loc.path + (f"?{loc.query}" if loc.query else "")
        # A relative Location (absolute_redirect off) stays on the host
        # that was asked.
        loc_host = loc.hostname or name
        self.check(
            got == status and loc_host == host and loc_target == target,
            label,
            f"got {got} -> {hdrs.get('Location')}",
        )
        return hdrs.get("Vary", "")

    def page(
        self,
        label: str,
        name: str,
        path: str,
        status: int = 200,
        must_contain: bytes = b"<html",
        scheme: str = "https",
    ):
        try:
            got, hdrs, body = self.get(scheme, name, path)
        except (OSError, ssl.SSLError) as exc:
            self.check(False, label, str(exc))
            return None
        self.check(got == status and must_contain in body, label, f"got {got}")
        return hdrs

    def loads(self, label: str, name: str, path: str) -> None:
        """Target exists - fetches one byte (206), not a whole video."""
        try:
            got, _, _ = self.get("https", name, path, {"Range": "bytes=0-0"})
        except (OSError, ssl.SSLError) as exc:
            self.check(False, label, str(exc))
            return
        self.check(got in (200, 206), label, f"got {got}")

    def site(self, vhost: dict) -> None:
        canonical = vhost["canonical"]
        aliases = vhost.get("aliases") or []
        locales = vhost.get("locales") or []
        n = vhost["name"]
        self.certificate(vhost, [canonical, *aliases])

        self.redirect(
            f"{n}: http -> https",
            "http",
            canonical,
            "/a/b?c=1",
            301,
            canonical,
            "/a/b?c=1",
        )
        try:
            got, _, _ = self.get("http", canonical, "/.well-known/acme-challenge/x")
            self.check(
                got == 404,
                f"{n}: ACME path answered over plain HTTP",
                f"got {got}, expected 404",
            )
        except OSError as exc:
            self.check(False, f"{n}: ACME path over plain HTTP", str(exc))

        for alias in aliases:
            self.redirect(
                f"{n}: {alias} -> {canonical}",
                "https",
                alias,
                "/a/b?c=1",
                301,
                canonical,
                "/a/b?c=1",
            )

        if locales:
            default = DEFAULT_LOCALE if DEFAULT_LOCALE in locales else locales[0]
            cases = [
                (f"{loc.split('-')[0]}-XX,{loc.split('-')[0]};q=0.9", loc)
                for loc in locales
            ]
            cases.append(("fr-FR,fr;q=0.9", default))
            for accept, expected in cases:
                vary = self.redirect(
                    f"{n}: / with Accept-Language {accept} -> /{expected}/",
                    "https",
                    canonical,
                    "/",
                    302,
                    canonical,
                    f"/{expected}/",
                    {"Accept-Language": accept},
                )
                if vary is not None:
                    self.check(
                        "Accept-Language" in vary, f"{n}: / sends Vary: Accept-Language"
                    )
            home = None
            for loc in locales:
                home = self.page(f"{n}: /{loc}/ loads", canonical, f"/{loc}/")
                for sub in vhost.get("pages") or []:
                    self.page(f"{n}: /{loc}/{sub} loads", canonical, f"/{loc}/{sub}")
        else:
            home = self.page(f"{n}: / loads", canonical, "/")

        for r in vhost.get("redirects") or []:
            target = r["to"].replace("{lang}", DEFAULT_LOCALE)
            status = 302 if "{lang}" in r["to"] else 301
            self.redirect(
                f"{n}: {r['from']} -> {target}",
                "https",
                canonical,
                r["from"],
                status,
                canonical,
                target,
                {"Accept-Language": "en-US,en;q=0.9"},
            )
            self.loads(f"{n}: {target} loads", canonical, target)

        if home is not None:
            for header, value in [
                ("X-Content-Type-Options", "nosniff"),
                ("Content-Security-Policy", "default-src 'self'"),
            ]:
                self.check(value in home.get(header, ""), f"{n}: {header} header")
            if self.hsts_max_age > 0:
                self.check(
                    f"max-age={self.hsts_max_age}"
                    in home.get("Strict-Transport-Security", ""),
                    f"{n}: HSTS header",
                )

        self.page(f"{n}: custom 404 page", canonical, "/no-such-page/", 404, b"404")

    def default_page(self, default_site: dict, sample: str) -> None:
        """The port-80 default server, reached the way a stray visitor
        would: by bare IP, so no hostname we serve."""
        ip = self.ip_for(sample)
        n = f"{default_site['name']} (http://{ip}/)"
        locales = default_site["locales"]
        fallback = DEFAULT_LOCALE if DEFAULT_LOCALE in locales else locales[0]
        cases = [(f"{loc.split('-')[0]}-XX", loc) for loc in locales]
        cases.append(("fr-FR", fallback))
        for accept, expected in cases:
            vary = self.redirect(
                f"{n}: / with Accept-Language {accept} -> /{expected}/",
                "http",
                ip,
                "/",
                302,
                ip,
                f"/{expected}/",
                {"Accept-Language": accept},
            )
            if vary is not None:
                self.check("Accept-Language" in vary, f"{n}: / sends Vary")
        for loc in locales:
            hdrs = self.page(f"{n}: /{loc}/ loads", ip, f"/{loc}/", scheme="http")
        if hdrs is not None:
            self.check(
                "default-src 'self'" in hdrs.get("Content-Security-Policy", ""),
                f"{n}: Content-Security-Policy header",
            )
        self.page(f"{n}: custom 404 page", ip, "/nope/", 404, b"404", "http")

    def unknown_host_rejected(self, sample: str) -> None:
        try:
            raw = socket.create_connection(
                (self.ip_for(sample), self.args.https_port), 10
            )
            ctx = ssl.create_default_context()
            ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
            with ctx.wrap_socket(raw, server_hostname="unknown.invalid"):
                rejected = False
        except ssl.SSLError:
            rejected = True
        self.check(rejected, "unknown hostname refused at TLS handshake")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only", nargs="+", metavar="SITE", help="vhost names to check"
    )
    parser.add_argument(
        "--staging",
        action="store_true",
        help="expect Let's Encrypt staging certificates",
    )
    parser.add_argument("--min-days", type=int, default=21)
    parser.add_argument(
        "--resolve", metavar="IP", help="connect here for every hostname"
    )
    parser.add_argument("--http-port", type=int, default=80)
    parser.add_argument("--https-port", type=int, default=443)
    parser.add_argument("--cafile", help="extra trusted CA (local test only)")
    args = parser.parse_args()

    config = yaml.safe_load(VHOSTS_FILE.read_text())
    vhosts = [v for v in config["vhosts"] if not args.only or v["name"] in args.only]
    if not vhosts and args.only and config["default_site"]["name"] in args.only:
        vhosts = config["vhosts"][:1]  # only to locate the droplet's IP
        args.skip_sites = True
    if not vhosts:
        print(f"No matching sites in {VHOSTS_FILE.name}.")
        return 1

    checker = Checker(args, int(config.get("hsts_max_age", 0)))
    if not getattr(args, "skip_sites", False):
        for vhost in vhosts:
            checker.site(vhost)
    if not args.only or config["default_site"]["name"] in args.only:
        checker.default_page(config["default_site"], vhosts[0]["canonical"])
    checker.unknown_host_rejected(vhosts[0]["canonical"])

    print(
        f"\n{checker.failures} failure(s)."
        if checker.failures
        else "\nAll smoke tests passed."
    )
    return 1 if checker.failures else 0


if __name__ == "__main__":
    sys.exit(main())
