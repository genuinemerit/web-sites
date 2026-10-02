"""Internal link check over every site's Frozen-Flask build output.

For each sites/<site>/build/**/*.html (and *.css), every internal
reference - <a href>, <link href>, src/srcset/poster on media elements,
and CSS url(...) in <style> blocks and stylesheets - must resolve to a
real file, the same way the server will resolve it:

  - /media/...  -> sites/<site>/media/...  (gitignored large media,
                   served by its own location block, never frozen -
                   see tools/dev/nginx-site.conf.template)
  - /anything   -> sites/<site>/build/anything
  - relative    -> resolved against the referring file's directory
  - a directory -> must contain index.html

External links (http:, https:, mailto:, tel:, data:, protocol-relative
//) are not checked: their availability isn't ours to gate a build on.
Fragment-only links (#top) are skipped.

Exit 0 when every internal reference resolves, 1 otherwise. Stdlib
only. Run after the Frozen-Flask build (tools/dev/pre-build-check.sh
does both, in that order).
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
SITES_DIR = REPO_ROOT / "sites"

_URL_ATTRS = {"href", "src", "poster", "data"}
_CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)")
_EXTERNAL_PREFIXES = ("http:", "https:", "mailto:", "tel:", "data:", "//")


class _RefCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == "style":
            self._in_style = True
        for name, value in attrs:
            if value is None:
                continue
            if name in _URL_ATTRS:
                self.refs.append(value)
            elif name == "srcset":
                self.refs.extend(
                    part.strip().split()[0] for part in value.split(",") if part.strip()
                )
            elif name == "style":
                self.refs.extend(m.group(2) for m in _CSS_URL_RE.finditer(value))

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style:
            self.refs.extend(m.group(2) for m in _CSS_URL_RE.finditer(data))


def _is_checkable(ref: str) -> bool:
    ref = ref.strip()
    return (
        bool(ref) and not ref.startswith("#") and not ref.startswith(_EXTERNAL_PREFIXES)
    )


def _resolve(ref: str, referrer: Path, build_dir: Path, media_dir: Path) -> Path:
    path = unquote(urlsplit(ref.strip()).path)
    if path.startswith("/media/"):
        return media_dir / path.removeprefix("/media/")
    if path.startswith("/"):
        return build_dir / path.lstrip("/")
    return referrer.parent / path


def _exists(target: Path) -> bool:
    if target.is_dir():
        return (target / "index.html").is_file()
    return target.is_file()


def check_site(site_dir: Path) -> list[str]:
    build_dir = site_dir / "build"
    media_dir = site_dir / "media"
    errors: list[str] = []
    for page in sorted(build_dir.rglob("*")):
        if page.suffix == ".html":
            collector = _RefCollector()
            collector.feed(page.read_text(encoding="utf-8"))
            refs = collector.refs
        elif page.suffix == ".css":
            text = page.read_text(encoding="utf-8")
            refs = [m.group(2) for m in _CSS_URL_RE.finditer(text)]
        else:
            continue
        for ref in refs:
            if not _is_checkable(ref):
                continue
            target = _resolve(ref, page, build_dir, media_dir)
            if not _exists(target):
                rel_page = page.relative_to(REPO_ROOT)
                errors.append(f"ERROR: {rel_page}: broken link {ref!r}")
    return errors


def main() -> int:
    # Only sites with real build output - setup-local-nginx.sh creates an
    # empty build/ placeholder for every site, built or not.
    site_dirs = sorted(
        p.parent for p in SITES_DIR.glob("*/build") if any(p.rglob("*.html"))
    )
    if not site_dirs:
        print("ERROR: no sites/*/build/ output found - run the build first.")
        return 1
    errors: list[str] = []
    for site_dir in site_dirs:
        errors.extend(check_site(site_dir))
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    names = ", ".join(d.name for d in site_dirs)
    print(f"All internal links resolve ({names}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
