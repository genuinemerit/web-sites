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

Translations (design step 4), as in music's catalog: each other locale
has an overlay, sites/movement/content/qigong.<locale>.toml, with one
block per category, set and reference holding the translated fields
(TRANSLATED below) and a `source` fingerprint of the English they were
translated from. Changed English makes the fingerprint stale and the
check fails ("out of date") until the translation is updated and
reviewed; missing blocks fail the same way.

    python -m websites.movement.check            # check, exit 1 on problems
    python -m websites.movement.check --status   # the fingerprints to record
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SITE_DIR = REPO_ROOT / "sites" / "movement"
CONTENT_DIR = SITE_DIR / "content"
CATALOG = CONTENT_DIR / "qigong.toml"
IMG_DIR = SITE_DIR / "static" / "img"
HEIRLOOM = SITE_DIR / "heirloom" / "qigong"
BASE_LOCALE = "en-US"

FIELDS = {
    "category": {"id", "title", "subtitle", "image", "alt"},
    "set": {"id", "category", "title", "summary", "source"},
    "reference": {"id", "title", "summary", "source"},
}
# The fields a translation provides, per kind of entry.
TRANSLATED = {
    "category": ("title", "subtitle", "alt"),
    "set": ("title", "summary"),
    "reference": ("title", "summary"),
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


def read_catalog(path: Path = CATALOG) -> dict:
    """The English catalog, checked (raises CatalogError)."""
    with path.open("rb") as f:
        data = tomllib.load(f)
    problems = check(data)
    if problems:
        raise CatalogError("\n".join(problems))
    return data


# --- translations ---------------------------------------------------------


def fingerprint(value) -> str:
    """Short, stable fingerprint of some English text (any JSON value)."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def expected_sources(data: dict) -> dict[str, dict[str, str]]:
    """kind -> id -> fingerprint of the English fields a translation covers."""
    return {
        kind: {
            e["id"]: fingerprint({f: e[f] for f in fields}) for e in data.get(kind, [])
        }
        for kind, fields in TRANSLATED.items()
    }


def translation_path(locale: str) -> Path:
    return CONTENT_DIR / f"qigong.{locale}.toml"


def check_translation(data: dict, tr: dict, locale: str) -> list[str]:
    name = translation_path(locale).name
    problems: list[str] = []
    extra = set(tr) - set(TRANSLATED)
    if extra:
        problems.append(f"{name}: unknown tables {', '.join(sorted(extra))}")
    for kind, sources in expected_sources(data).items():
        blocks = tr.get(kind, {})
        for ident in sorted(set(blocks) - set(sources)):
            problems.append(f"{name}: [{kind}.{ident}] has no English original")
        for ident, source in sources.items():
            block = blocks.get(ident)
            where = f"{name}: [{kind}.{ident}]"
            if block is None:
                problems.append(f"{where} missing")
                continue
            wanted = set(TRANSLATED[kind]) | {"source"}
            missing = wanted - set(block)
            if missing:
                problems.append(f"{where} missing {', '.join(sorted(missing))}")
            unknown = set(block) - wanted
            if unknown:
                problems.append(f"{where} unknown {', '.join(sorted(unknown))}")
            if block.get("source") != source:
                problems.append(
                    f"{where} out of date - the English changed; update the"
                    f" translation, then record source = {source!r}"
                )
    return problems


def load_translation(data: dict, locale: str) -> dict:
    path = translation_path(locale)
    if not path.is_file():
        raise CatalogError(f"{path.name}: missing (translation for {locale})")
    with path.open("rb") as f:
        tr = tomllib.load(f)
    problems = check_translation(data, tr, locale)
    if problems:
        raise CatalogError("\n".join(problems))
    return tr


def localize(data: dict, locale: str) -> dict:
    """The catalog as seen in `locale`: English, or with the translated
    fields of the checked overlay laid over it."""
    out = copy.deepcopy(data)
    if locale != BASE_LOCALE:
        tr = load_translation(data, locale)
        for kind, fields in TRANSLATED.items():
            for e in out.get(kind, []):
                for field in fields:
                    e[field] = tr[kind][e["id"]][field]
    return out


def load_catalog(locale: str = BASE_LOCALE, path: Path = CATALOG) -> dict:
    """The checked catalog in `locale`, with each category's sets
    attached in order."""
    data = localize(read_catalog(path), locale)
    for c in data["category"]:
        c["sets"] = [s for s in data["set"] if s["category"] == c["id"]]
    return data
