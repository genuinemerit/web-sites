"""Shared Frozen-Flask freeze orchestration, generic across sites - see
src/websites/taiji/__init__.py's docstring for why this project freezes
once per site (locale-parameterized routes), not once per locale, and
planning/architecture.md's Internationalization section for the
original per-locale framing this refines.

Any route with a `<locale>` URL segment is frozen once per entry in the
site module's LOCALES list - Frozen-Flask can't infer those values on
its own, since they're not discoverable by crawling rendered HTML alone
(the locale switcher only ever links to the *other* locale, never
enumerates all of them from one page).

Also copies two kinds of shared, non-templated files straight into every
site's build output, since neither needs i18n or Jinja rendering:

- sites/_shared/error-pages/ -> build root. nginx's error_page directive
  resolves 404.html/50x.html relative to each site's own root, so every
  site needs its own copy at the top of its build output - see
  design/taiji.md's note that these are shared hosting infrastructure,
  not taiji-specific, despite taiji being first to need them.
- sites/_shared/static/ -> build/shared/ (whole tree, sub-folders
  included). Shared CSS (tokens.css), self-hosted fonts and other shared
  static assets, one canonical source rather than a
  per-site copy that could drift - templates link it at the plain
  root-relative path /shared/<file>, same convention as content's
  /media/ links. See design/taiji.md's 2026-10-02 decision to sunset
  each legacy site's own styles.css in favor of this.

Usage: python -m websites.common.freeze <site>
"""

from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from flask_frozen import Freezer

REPO_ROOT = Path(__file__).resolve().parents[3]
ERROR_PAGES_SRC = REPO_ROOT / "sites" / "_shared" / "error-pages"
SHARED_STATIC_SRC = REPO_ROOT / "sites" / "_shared" / "static"


def freeze_site(site: str) -> None:
    module = importlib.import_module(f"websites.{site}")
    app = module.create_app()
    locales = getattr(module, "LOCALES", None)

    build_dir = REPO_ROOT / "sites" / site / "build"
    app.config["FREEZER_DESTINATION"] = str(build_dir)
    freezer = Freezer(app)

    if locales:

        @freezer.register_generator
        def locale_urls():
            # Routes whose only parameter is the locale: one page each.
            for rule in app.url_map.iter_rules():
                if rule.arguments == {"locale"}:
                    for locale in locales:
                        yield rule.endpoint, {"locale": locale}
            # Routes with more parameters (e.g. music's
            # /<locale>/workbench/<piece>/) come from the site module's
            # optional freeze_urls(locale) -> (endpoint, values) pairs.
            extra = getattr(module, "freeze_urls", None)
            if extra:
                for locale in locales:
                    yield from extra(locale)

    freezer.freeze()

    for error_page in ERROR_PAGES_SRC.iterdir():
        shutil.copy2(error_page, build_dir / error_page.name)

    # Whole tree, sub-folders included (fonts/<family>/ since 2026-10-10).
    shutil.copytree(SHARED_STATIC_SRC, build_dir / "shared", dirs_exist_ok=True)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m websites.common.freeze <site>", file=sys.stderr)
        raise SystemExit(2)
    freeze_site(sys.argv[1])


if __name__ == "__main__":
    main()
