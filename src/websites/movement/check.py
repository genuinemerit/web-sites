"""Check the qigong catalog and its translations (websites.movement.catalog).

    python -m websites.movement.check            # exit 1 on problems
    python -m websites.movement.check --status   # the fingerprints to record

Run by tools/dev/pre-build-check.sh before the build, so a broken catalog
is a clear list of problems, not a traceback from the build.
"""

from __future__ import annotations

import sys

from websites.movement import LOCALES
from websites.movement.catalog import (
    BASE_LOCALE,
    CONTENT_DIR,
    CatalogError,
    check_page_translations,
    english_pages,
    expected_sources,
    load_catalog,
    page_fingerprint,
    read_catalog,
)


def print_status() -> None:
    data = read_catalog()
    print("Fingerprints of the English each translation block must record:")
    for kind, sources in expected_sources(data).items():
        for ident, source in sources.items():
            print(f"  [{kind}.{ident}] source = {source!r}")
    print("Fingerprints each translated page records (translated_from):")
    for english in english_pages():
        rel = english.relative_to(CONTENT_DIR / BASE_LOCALE).as_posix()
        print(f"  {rel}: {page_fingerprint(english)}")


def main(argv: list[str]) -> int:
    try:
        if "--status" in argv:
            print_status()
            return 0
        for locale in LOCALES:
            load_catalog(locale)
    except CatalogError as exc:
        print(f"Qigong catalog problems:\n{exc}", file=sys.stderr)
        return 1
    problems = [
        p for loc in LOCALES if loc != BASE_LOCALE for p in check_page_translations(loc)
    ]
    if problems:
        print("Qigong page translations:", *problems, sep="\n", file=sys.stderr)
        return 1
    others = [loc for loc in LOCALES if loc != BASE_LOCALE]
    print(f"Qigong catalog OK ({BASE_LOCALE}{''.join(', ' + o for o in others)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
