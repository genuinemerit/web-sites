"""taiji - Louise Sebra's "Taiji for Balance" class. See
design/taiji.md for the confirmed MVP scope and planning/
site-build-checklist.md for the build template this follows.

Locale-parameterized routes (/<locale>/...) rather than separate
freeze() runs per locale: a single Frozen-Flask pass naturally produces
both locale trees from one app instance, since locale is just a URL
segment the route handlers read - simpler than re-running freeze() with
different global state per locale. Refines (doesn't contradict)
planning/architecture.md's "freeze once per locale" decision; see that
doc for why.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from websites.common.content import load_page
from websites.common.i18n import load_site_catalogs, translate

SITE = "taiji"
LOCALES = ["en-US", "es-ES"]
REPO_ROOT = Path(__file__).resolve().parents[3]


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(REPO_ROOT / "sites" / SITE / "templates"),
        static_folder=str(REPO_ROOT / "sites" / SITE / "static"),
    )
    # Site templates first, falling back to sites/_shared/templates/ for
    # any future shared Jinja macros - see planning/design-aesthetics.md's
    # "shared core, per-site skin" model. Shared CSS (sites/_shared/
    # static/tokens.css), not Jinja template inheritance, carries the
    # cross-site look - see design/taiji.md's 2026-10-02 decision. Every
    # page template here is a standalone document (no shared base.html).
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(REPO_ROOT / "sites" / SITE / "templates")),
            FileSystemLoader(str(REPO_ROOT / "sites" / "_shared" / "templates")),
        ]
    )
    catalogs = load_site_catalogs(SITE, LOCALES)

    def t(locale: str, tag: str) -> str:
        return translate(catalogs, locale, tag)

    @app.context_processor
    def inject_globals():
        return {"locales": LOCALES, "site": SITE}

    @app.route("/<locale>/")
    def splash(locale: str):
        if locale not in LOCALES:
            abort(404)
        return render_template("splash.html", locale=locale, t=t)

    @app.route("/<locale>/taiji-for-balance/")
    def taiji_for_balance(locale: str):
        if locale not in LOCALES:
            abort(404)
        meta, body_html = load_page(SITE, locale, "taiji-for-balance")
        return render_template(
            "page.html", locale=locale, t=t, meta=meta, body_html=body_html
        )

    return app
