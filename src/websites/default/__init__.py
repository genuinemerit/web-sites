"""default - the page nginx's default server shows to any request that
doesn't name one of our sites (a bare-IP visit, a stale DNS record),
replacing the stock "Welcome to nginx!". From David's 2026-10-02
prototype; served by the droplet's port-80 default server
(ansible/roles/nginx/templates/00-default.conf.j2) and by ubuvm's local
nginx (tools/dev/setup-local-nginx.sh).
"""

from __future__ import annotations

from flask import Flask

from websites.common.single_page import create_single_page_app

SITE = "default"
LOCALES = ["en-US", "es-ES"]

LINKS = [
    ("https://genuinemerit.com/", "genuinemerit.com"),
    ("https://davidstitt.net/", "davidstitt.net"),
]


def create_app() -> Flask:
    return create_single_page_app(
        SITE, LOCALES, "index.html", links=LINKS, image="max-headroom"
    )
