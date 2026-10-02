"""Validate i18n completeness for every site - adapted from sask's
tools/dev/validate_i18n.py (DD-0022), extended for this repo's per-site
layout (config/i18n/<site>/<locale>.toml, sites/<site>/content/<locale>/)
and for long-form content, which sask's version doesn't cover.

A "site" here is any src/websites/<site>/ package (not common/). Its
LOCALES list is the source of truth for which locales must exist.

Checks, per site:

  1. Every declared locale has a catalog file, and there are no catalog
     files for undeclared locales.
  2. Malformed tag (not dotted-lowercase; hyphens allowed in the final
     segment so locale codes like lang.en-US work).
  3. Missing base content: a tag in a non-base locale but absent from
     en-US, the completeness floor.
  4. Missing translation: a tag in en-US absent from a declared locale.
  5. Long-form content parity: every declared locale has the same set
     of sites/<site>/content/<locale>/*.md pages (only when the site
     has a content/ folder).

All five are hard errors. sask treats check 4 as a warning except at
deploy time (--strict); this project has a single gate, run before any
build, push, or deploy, so a missing translation fails it - the runtime
fallback to en-US (src/websites/common/i18n.py) is a safety net, not a
way to ship untranslated pages.

Run via `poetry run` (imports each site package to read LOCALES).
Exit 0 when clean, 1 otherwise.
"""

from __future__ import annotations

import importlib
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src" / "websites"
I18N_DIR = REPO_ROOT / "config" / "i18n"
SITES_DIR = REPO_ROOT / "sites"
BASE_LOCALE = "en-US"

_TAG_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*\.[a-zA-Z][a-zA-Z0-9_-]*$")


def site_packages() -> list[str]:
    return sorted(
        p.name
        for p in SRC_DIR.iterdir()
        if p.is_dir() and p.name != "common" and (p / "__init__.py").is_file()
    )


def check_site(site: str) -> list[str]:
    errors: list[str] = []
    module = importlib.import_module(f"websites.{site}")
    locales: list[str] = list(getattr(module, "LOCALES", []))
    if BASE_LOCALE not in locales:
        return [f"{site}: LOCALES {locales} does not include {BASE_LOCALE}"]

    # Check 1: catalog files match the declared locale list exactly.
    catalog_dir = I18N_DIR / site
    present = {p.stem for p in catalog_dir.glob("*.toml")}
    for locale in sorted(set(locales) - present):
        errors.append(f"{site}: missing catalog {catalog_dir.name}/{locale}.toml")
    for locale in sorted(present - set(locales)):
        errors.append(f"{site}: catalog {locale}.toml for undeclared locale")
    if errors:
        return errors

    catalogs: dict[str, set[str]] = {}
    for locale in locales:
        with (catalog_dir / f"{locale}.toml").open("rb") as f:
            catalogs[locale] = set(tomllib.load(f).get("tags", {}))

    # Check 2: tag naming.
    for locale, tags in catalogs.items():
        for tag in sorted(tags):
            if not _TAG_RE.match(tag):
                errors.append(f"{site}/{locale}.toml: malformed tag {tag!r}")

    # Checks 3 and 4: floor and completeness.
    base = catalogs[BASE_LOCALE]
    for locale, tags in catalogs.items():
        if locale == BASE_LOCALE:
            continue
        for tag in sorted(tags - base):
            errors.append(
                f"{site}/{BASE_LOCALE}.toml: missing base content for {tag!r} "
                f"(present in {locale}.toml)"
            )
        for tag in sorted(base - tags):
            errors.append(f"{site}/{locale}.toml: missing translation for {tag!r}")

    # Check 5: long-form content parity.
    content_dir = SITES_DIR / site / "content"
    if content_dir.is_dir():
        pages = {
            locale: {p.name for p in (content_dir / locale).glob("*.md")}
            for locale in locales
        }
        base_pages = pages[BASE_LOCALE]
        for locale, names in pages.items():
            for name in sorted(base_pages - names):
                errors.append(f"{site}: content/{locale}/{name} missing")
            for name in sorted(names - base_pages):
                errors.append(
                    f"{site}: content/{locale}/{name} has no {BASE_LOCALE} original"
                )
    return errors


def main() -> int:
    sites = site_packages()
    if not sites:
        print("ERROR: no site packages found under src/websites/.")
        return 1
    errors: list[str] = []
    for site in sites:
        errors.extend(f"ERROR: {e}" for e in check_site(site))
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"i18n complete ({', '.join(sites)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
