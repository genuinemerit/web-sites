"""Shared Markdown + front-matter content loading. Long-form prose uses
parallel per-locale documents (sites/<site>/content/<locale>/*.md), not
tag substitution - see planning/architecture.md's Internationalization
section. Convention confirmed here: content files nest under a locale
subfolder, mirroring config/i18n/<site>/<locale>.toml's shape.
"""

from __future__ import annotations

from pathlib import Path

import frontmatter
from markdown import markdown

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_page(site: str, locale: str, slug: str) -> tuple[dict, str]:
    """Load one Markdown content file, returning (front_matter_dict,
    rendered_html_body). Raises FileNotFoundError if the page doesn't
    exist for this locale - no silent fallback for long-form content,
    unlike short UI-string tags (missing prose is a real content gap,
    not something to paper over)."""
    path = REPO_ROOT / "sites" / site / "content" / locale / f"{slug}.md"
    post = frontmatter.load(path)
    html_body = markdown(post.content)
    return post.metadata, html_body
