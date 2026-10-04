"""comunidad - community projects (comunidad.genuinemerit.com). A
collection of collections: the Sandwich Open Mic (built 2026-10-04
from David's prototype), later the UAH / Alcalingua material and the
Intercambio de Idiomas. See design/comunidad.md.

Routes: /<locale>/ is the collections index (shared hub layout);
/<locale>/openmic/ is the Open Mic page. Images are listed in
sites/comunidad/static/img/openmic/manifest.json (WebP variants with
their dimensions), read once here so templates can build srcset.
"""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, abort, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from websites.common.i18n import load_site_catalogs, translate

SITE = "comunidad"
LOCALES = ["en-US", "es-ES"]
REPO_ROOT = Path(__file__).resolve().parents[3]
SITE_DIR = REPO_ROOT / "sites" / SITE

# Collections on the index: (catalog tag, relative URL, live) - same
# shape as the hub pages' LINKS; live=False shows "coming soon".
COLLECTIONS = [
    ("site.openmic", "openmic/", True),
    ("site.uah", "uah/", False),
    ("site.intercambio", "intercambio/", False),
]


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(SITE_DIR / "static"))
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(SITE_DIR / "templates")),
            FileSystemLoader(str(REPO_ROOT / "sites" / "_shared" / "templates")),
        ]
    )
    catalogs = load_site_catalogs(SITE, LOCALES)
    manifest = SITE_DIR / "static" / "img" / "openmic" / "manifest.json"
    openmic_images = json.loads(manifest.read_text())

    def t(locale: str, tag: str) -> str:
        return translate(catalogs, locale, tag)

    @app.context_processor
    def inject_globals():
        return {"locales": LOCALES, "site": SITE, "t": t}

    @app.route("/<locale>/")
    def index(locale: str):
        if locale not in LOCALES:
            abort(404)
        return render_template(
            "index.html",
            locale=locale,
            links=COLLECTIONS,
            image_variants=[
                {**v, "file": f"img/openmic/{v['file']}"}
                for v in openmic_images["opening-sticker"]
            ],
        )

    @app.route("/<locale>/openmic/")
    def openmic(locale: str):
        if locale not in LOCALES:
            abort(404)
        return render_template("openmic.html", locale=locale, images=openmic_images)

    return app
