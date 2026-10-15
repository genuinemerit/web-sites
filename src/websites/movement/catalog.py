"""Load and check the qigong catalog (sites/movement/content/qigong.toml)
- see design/movement.md.

The catalog is hand-edited, so every rule here turns a typo into a clear
message instead of a wrong page:

  - only known top-level, category, set and reference fields
  - ids are unique lowercase slugs across sets and references (they
    become page addresses, /<locale>/qigong/<id>/)
  - every set names a defined category, and every category has a set
  - every category image exists in sites/movement/static/img/
  - every source names a prototype PDF that exists in heirloom/ (when
    heirloom/ is present - it's gitignored, so a fresh clone skips this)
  - every page file, content/<locale>/qigong/<id>.md, belongs to a set
    or reference in the catalog (a misspelt file name would otherwise
    never be linked)

Spanish (design step 4) will add a parallel overlay file, as music's
catalog has.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SITE_DIR = REPO_ROOT / "sites" / "movement"
CATALOG = SITE_DIR / "content" / "qigong.toml"
IMG_DIR = SITE_DIR / "static" / "img"
CONTENT_DIR = SITE_DIR / "content"
HEIRLOOM = SITE_DIR / "heirloom" / "qigong"

FIELDS = {
    "category": {"id", "title", "subtitle", "image", "alt"},
    "set": {"id", "category", "title", "summary", "source"},
    "reference": {"id", "title", "summary", "source"},
}
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


class CatalogError(ValueError):
    """The catalog has problems; str() lists them, one per line."""


def check(data: dict) -> list[str]:
    problems: list[str] = []
    extra = set(data) - set(FIELDS)
    if extra:
        problems.append(f"unknown top-level tables: {', '.join(sorted(extra))}")
    seen: dict[str, str] = {}
    for kind, fields in FIELDS.items():
        for n, entry in enumerate(data.get(kind, []), 1):
            where = f"{kind} #{n} ({entry.get('id', '?')})"
            missing = fields - set(entry)
            if missing:
                problems.append(f"{where}: missing {', '.join(sorted(missing))}")
            unknown = set(entry) - fields
            if unknown:
                problems.append(f"{where}: unknown {', '.join(sorted(unknown))}")
            ident = entry.get("id", "")
            if not SLUG.fullmatch(ident):
                problems.append(f"{where}: id must be a lowercase slug")
            if kind != "category":
                if ident in seen:
                    problems.append(f"{where}: id already used by a {seen[ident]}")
                seen[ident] = kind
    categories = {c.get("id") for c in data.get("category", [])}
    used = {s.get("category") for s in data.get("set", [])}
    for s in data.get("set", []):
        if s.get("category") not in categories:
            problems.append(f"set {s.get('id')}: unknown category {s.get('category')}")
    for c in data.get("category", []):
        if c.get("id") not in used:
            problems.append(f"category {c.get('id')}: has no sets")
        if c.get("image") and not (IMG_DIR / c["image"]).is_file():
            problems.append(f"category {c.get('id')}: no image static/img/{c['image']}")
    for page in sorted(CONTENT_DIR.glob("*/qigong/*.md")):
        if page.stem not in seen:
            rel = page.relative_to(CONTENT_DIR)
            problems.append(f"content/{rel}: no set or reference {page.stem!r}")
    if HEIRLOOM.is_dir():
        for kind, folder in (("set", "sets"), ("reference", "img")):
            for e in data.get(kind, []):
                src = e.get("source", "")
                if src and not (HEIRLOOM / folder / src).is_file():
                    problems.append(
                        f"{kind} {e.get('id')}: no {folder}/{src} in heirloom"
                    )
    return problems


def load_catalog(path: Path = CATALOG) -> dict:
    """The checked catalog, with each category's sets attached in order."""
    with path.open("rb") as f:
        data = tomllib.load(f)
    problems = check(data)
    if problems:
        raise CatalogError("\n".join(problems))
    for c in data["category"]:
        c["sets"] = [s for s in data["set"] if s["category"] == c["id"]]
    return data
