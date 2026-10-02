"""genuinemerit - hub page for bare genuinemerit.com (genuinemerit.org
redirects here): an index of the public sites. From David's 2026-10-02
prototype; see design/domains.md. Layout shared with davidstitt via
sites/_shared/templates/hub.html.
"""

from __future__ import annotations

from flask import Flask

from websites.common.single_page import create_single_page_app

SITE = "genuinemerit"
LOCALES = ["en-US", "es-ES"]

# (catalog tag, URL, live). live=False shows the name with a "coming
# soon" note instead of a link to a site that doesn't exist yet - flip
# it when the site goes live (it's listed in ansible/vhosts.yml).
LINKS = [
    ("site.taiji", "https://taiji.genuinemerit.com/", True),
    ("site.play", "https://play.genuinemerit.com/", False),
    ("site.spain", "https://spain.genuinemerit.com/", False),
    ("site.comunidad", "https://comunidad.genuinemerit.com/", False),
]


def create_app() -> Flask:
    return create_single_page_app(
        SITE, LOCALES, "index.html", links=LINKS, image="walrus"
    )
