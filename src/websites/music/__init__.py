"""music - music.davidstitt.net. The workbench (from David's 2026-10-10
prototype, heirloom/music-workbench-refined-v2/) built as static pages
from sites/music/content/catalog.toml: a welcome/index page and one page
per piece. Small optional JavaScript (step 5) only enhances them -
search, filters, the welcome page's recently opened pieces, status and
checklist kept in the visitor's browser. See design/music.md for the decisions and dev plan.

Routes:
  /<locale>/                    the music hub (shared hub layout)
  /<locale>/workbench/          welcome page + the piece index
  /<locale>/workbench/<piece>/  one page per catalog piece

English and Spanish: interface strings in config/i18n/music/, content
from catalog.toml plus its Spanish counterpart catalog.es-ES.toml (see
websites.music.catalog for the translation fingerprints).
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import cache
from pathlib import Path

from flask import Flask, abort, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from websites.common.i18n import load_site_catalogs, translate
from websites.music.catalog import MEDIA_TYPES, load_catalog, localize

SITE = "music"
LOCALES = ["en-US", "es-ES"]
REPO_ROOT = Path(__file__).resolve().parents[3]
SITE_DIR = REPO_ROOT / "sites" / SITE

# Resource type -> icon (decorative, aria-hidden in the template).
ICONS = {"audio": "♫", "video": "▷", "link": "↗"}
FILTER_GROUPS = ("activity", "instrument", "genre")

# Hub entries: (catalog tag, relative URL, live) - same shape as the
# other hubs' LINKS. Only the workbench so far.
HUB_LINKS = [("site.workbench", "workbench/", True)]
HUB_IMAGE = [{"file": "img/david-suspicious-529.webp", "w": 529, "h": 587}]


@cache
def catalogs() -> dict[str, dict]:
    """The catalog as seen in each locale, loaded and checked once, on
    first use - not at import, so `python -m websites.music.check` can
    report a broken catalog as a clean list instead of a traceback."""
    base = load_catalog()
    return {locale: localize(base, locale) for locale in LOCALES}


def freeze_urls(locale: str):
    """Piece pages for websites.common.freeze (they have a second URL
    parameter, so the generic locale-only generator can't list them)."""
    for p in catalogs()[locale]["piece"]:
        yield "piece", {"locale": locale, "piece": p["id"]}


def _resource_view(r: dict) -> dict:
    """Normalise a catalog resource for the templates."""
    if "file" in r:
        kind = MEDIA_TYPES[Path(r["file"]).suffix.lower()]
        return {**r, "type": kind, "href": f"/media/{r['file']}", "hosted": True}
    return {**r, "href": r["url"], "hosted": False}


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(SITE_DIR / "static"))
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(SITE_DIR / "templates")),
            FileSystemLoader(str(REPO_ROOT / "sites" / "_shared" / "templates")),
        ]
    )
    ui = load_site_catalogs(SITE, LOCALES)
    data = catalogs()
    by_id = {loc: {p["id"]: p for p in data[loc]["piece"]} for loc in LOCALES}
    built = datetime.now(UTC).strftime("%Y-%m")  # footer "Working collection" date

    def t(locale: str, tag: str, **values) -> str:
        text = translate(ui, locale, tag)
        return text.format(**values) if values else text

    def label(locale: str, group: str, key: str) -> str:
        return data[locale]["vocabulary"][group][key]

    def fmt_date(locale: str, value: str) -> str:
        if len(value) == 4:
            return value
        year, month = value.split("-")
        return t(
            locale, "date.month_year", month=t(locale, f"month.m{month}"), year=year
        )

    def resources_count(locale: str, n: int) -> str:
        return t(
            locale,
            "workbench.resources_one" if n == 1 else "workbench.resources_other",
            n=n,
        )

    def status_labels(locale: str) -> dict[str, str]:
        return dict(data[locale]["vocabulary"]["status"])

    def search_text(locale: str, p: dict) -> str:
        parts = [p["title"], label(locale, "kind", p["kind"]), p["summary"]]
        parts += [r["title"] + " " + r.get("desc", "") for r in p["resource"]]
        return " ".join(parts).lower()

    def page(template: str, locale: str, **context):
        """Render with this locale's pieces and vocabulary."""
        return render_template(
            template,
            locale=locale,
            pieces=data[locale]["piece"],
            vocab=data[locale]["vocabulary"],
            **context,
        )

    @app.context_processor
    def inject_globals():
        return {
            "locales": LOCALES,
            "site": SITE,
            "t": t,
            "label": label,
            "fmt_date": fmt_date,
            "resources_count": resources_count,
            "search_text": search_text,
            "status_labels": status_labels,
            "filter_groups": FILTER_GROUPS,
            "icons": ICONS,
            "built": built,
        }

    @app.route("/<locale>/")
    def index(locale: str):
        if locale not in LOCALES:
            abort(404)
        return page("hub_index.html", locale, links=HUB_LINKS, image_variants=HUB_IMAGE)

    @app.route("/<locale>/workbench/")
    def workbench(locale: str):
        if locale not in LOCALES:
            abort(404)
        return page("workbench_index.html", locale)

    @app.route("/<locale>/workbench/<piece>/")
    def piece(locale: str, piece: str):
        if locale not in LOCALES or piece not in by_id[locale]:
            abort(404)
        p = by_id[locale][piece]
        return page(
            "workbench_piece.html",
            locale,
            p=p,
            current=piece,
            resources=[_resource_view(r) for r in p["resource"]],
            checklist=p.get("checklist", data[locale]["default_checklist"]),
            status=p.get("status", "not-started"),
        )

    return app
