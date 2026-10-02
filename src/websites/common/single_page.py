"""Factory for one-page, multi-locale sites: the bare-domain hubs
(genuinemerit, davidstitt) and the droplet's default page (default).
Each serves a single template at /<locale>/; nginx sends "/" to the
visitor's language (design/domains.md). Freezing works unchanged via
websites.common.freeze, since the route is locale-parameterized.

Templates resolve from sites/<site>/templates/ first, then
sites/_shared/templates/ (e.g. hub.html); static files from
sites/<site>/static/.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from websites.common.i18n import load_site_catalogs, translate

REPO_ROOT = Path(__file__).resolve().parents[3]


def create_single_page_app(
    site: str, locales: list[str], template: str, **context
) -> Flask:
    site_dir = REPO_ROOT / "sites" / site
    app = Flask(f"websites.{site}", static_folder=str(site_dir / "static"))
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(site_dir / "templates")),
            FileSystemLoader(str(REPO_ROOT / "sites" / "_shared" / "templates")),
        ]
    )
    catalogs = load_site_catalogs(site, locales)

    def t(locale: str, tag: str) -> str:
        return translate(catalogs, locale, tag)

    @app.context_processor
    def inject_globals():
        return {"locales": locales, "site": site, "t": t, **context}

    @app.route("/<locale>/")
    def index(locale: str):
        if locale not in locales:
            abort(404)
        return render_template(template, locale=locale)

    return app
