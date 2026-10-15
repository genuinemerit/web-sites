"""movement - movement.davidstitt.net. A hub for David's movement
practices; the first sub-site is Qigong, built from his 2026-10-15
prototype (sites/movement/heirloom/qigong/). See design/movement.md for
the decisions and dev plan.

Routes:
  /<locale>/                the movement hub (shared hub layout)
  /<locale>/qigong/         the qigong index: categories, exercise sets,
                            references and "About the class", built from
                            sites/movement/content/qigong.toml
  /<locale>/qigong/<id>/    one page per set or reference, from
                            sites/movement/content/<locale>/qigong/<id>.md
                            (transcribed from the prototype's PDFs)

English only until design step 4 adds Spanish (the i18n check requires
every declared locale to be complete). No JavaScript.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from flask import Flask, abort, render_template
from jinja2 import ChoiceLoader, FileSystemLoader

from websites.common.content import load_page
from websites.common.i18n import load_site_catalogs, translate
from websites.movement.catalog import load_catalog

SITE = "movement"
LOCALES = ["en-US"]
REPO_ROOT = Path(__file__).resolve().parents[3]
SITE_DIR = REPO_ROOT / "sites" / SITE

# Hub entries: (catalog tag, relative URL, live) - same shape as the
# other hubs' LINKS; live=False shows "coming soon". Taiji here is
# David's own future sub-site, not Louise's taiji.genuinemerit.com.
HUB_LINKS = [
    ("site.qigong", "qigong/", True),
    ("site.taiji", "taiji/", False),
    ("site.xingyi", "xingyi/", False),
    ("site.pilates", "pilates/", False),
    ("site.stretching", "stretching/", False),
]
HUB_IMAGE = [{"file": "img/taiji_tree.jpg", "w": 1500, "h": 994}]


@cache
def catalog() -> dict:
    """Loaded and checked once, on first use."""
    return load_catalog()


def pages_in_order() -> list[dict]:
    """Every set (in category order), then every reference - the order
    of the previous/next links on the pages."""
    data = catalog()
    sets = [s for c in data["category"] for s in c["sets"]]
    return sets + data["reference"]


def freeze_urls(locale: str):
    """Set and reference pages for websites.common.freeze - only those
    written so far."""
    for p in pages_in_order():
        if page_exists(locale, p["id"]):
            yield "qigong_page", {"locale": locale, "page_id": p["id"]}


def page_exists(locale: str, page_id: str) -> bool:
    """A set or reference is linked only once its page is written
    (design step 3)."""
    return (SITE_DIR / "content" / locale / "qigong" / f"{page_id}.md").is_file()


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(SITE_DIR / "static"))
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(SITE_DIR / "templates")),
            FileSystemLoader(str(REPO_ROOT / "sites" / "_shared" / "templates")),
        ]
    )
    ui = load_site_catalogs(SITE, LOCALES)
    data = catalog()

    def t(locale: str, tag: str, **values) -> str:
        text = translate(ui, locale, tag)
        return text.format(**values) if values else text

    @app.context_processor
    def inject_globals():
        # The sidebar (qigong_base.html) lists the categories on every page.
        return {
            "locales": LOCALES,
            "site": SITE,
            "t": t,
            "page_exists": page_exists,
            "categories": data["category"],
            "references": data["reference"],
        }

    @app.route("/<locale>/")
    def index(locale: str):
        if locale not in LOCALES:
            abort(404)
        return render_template(
            "hub_index.html", locale=locale, links=HUB_LINKS, image_variants=HUB_IMAGE
        )

    @app.route("/<locale>/qigong/")
    def qigong(locale: str):
        if locale not in LOCALES:
            abort(404)
        _, about = load_page(SITE, locale, "qigong-about")
        return render_template(
            "qigong_index.html", locale=locale, set_count=len(data["set"]), about=about
        )

    @app.route("/<locale>/qigong/<page_id>/")
    def qigong_page(locale: str, page_id: str):
        order = [p for p in pages_in_order() if page_exists(locale, p["id"])]
        ids = [p["id"] for p in order]
        if locale not in LOCALES or page_id not in ids:
            abort(404)
        i = ids.index(page_id)
        item = order[i]
        category = next(
            (c for c in data["category"] if c["id"] == item.get("category")), None
        )
        _, body = load_page(SITE, locale, f"qigong/{page_id}")
        return render_template(
            "qigong_page.html",
            locale=locale,
            item=item,
            category=category,
            body=body,
            prev=order[i - 1] if i > 0 else None,
            next=order[i + 1] if i + 1 < len(order) else None,
        )

    return app
