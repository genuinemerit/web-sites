"""davidstitt - hub page for bare davidstitt.net: an index of the
personal sites. From David's 2026-10-02 prototype; see
design/domains.md. Layout shared with genuinemerit via
sites/_shared/templates/hub.html.
"""

from __future__ import annotations

from flask import Flask

from websites.common.single_page import create_single_page_app

SITE = "davidstitt"
LOCALES = ["en-US", "es-ES"]

# (catalog tag, URL, live) - see websites.genuinemerit.LINKS. `music`
# is live: the legacy site keeps serving it until its own rebuild.
LINKS = [
    ("site.music", "https://music.davidstitt.net/", True),
    ("site.callejerez", "https://callejerez.davidstitt.net/", False),
    ("site.movement", "https://movement.davidstitt.net/", False),
]


def create_app() -> Flask:
    return create_single_page_app(
        SITE, LOCALES, "index.html", links=LINKS, image="dachshund-saxophone"
    )
