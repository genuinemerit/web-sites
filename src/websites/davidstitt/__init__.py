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
# (2026-10-10) and `movement` (2026-10-16) are live on the new droplet.
LINKS = [
    ("site.music", "https://music.davidstitt.net/", True),
    ("site.callejerez", "https://callejerez.davidstitt.net/", False),
    ("site.movement", "https://movement.davidstitt.net/", True),
]


def create_app() -> Flask:
    return create_single_page_app(
        SITE, LOCALES, "index.html", links=LINKS, image="dachshund-saxophone"
    )
