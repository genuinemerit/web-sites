"""Load and validate the music workbench catalog
(sites/music/content/catalog.toml) - see design/music.md.

The catalog is hand-edited, so every rule here exists to turn a typo
into a clear message instead of a wrong page:

  - only known top-level, piece and resource fields (catches "sumary")
  - ids are unique lowercase slugs (they become page addresses)
  - every tag (kind, activity, instrument, genre, status, type) is
    defined in [vocabulary]
  - a resource has exactly one of `file` (hosted here, must exist in
    sites/music/media/ with a known audio/video extension) or `url`
    (http/https only - never javascript: or other schemes - plus a type)
  - dates are YYYY or YYYY-MM

Translations (design/music.md, step 7): each other locale has a
parallel file, sites/music/content/catalog.<locale>.toml, holding the
translated vocabulary labels, default checklist, and per piece the
translated text (summary, resource titles/descriptions, optional title,
subtitle, headings, custom checklist). Every translated block records a
`source` fingerprint of the English it was translated from; when the
English changes, the fingerprint no longer matches and the check fails
("out of date") until the translation is updated and reviewed. Missing
blocks fail the same way - nothing untranslated reaches the build.

    python -m websites.music.check            # check, exit 1 on problems
    python -m websites.music.check --status   # translation status and the
                                              # fingerprints to record

Run by tools/dev/pre-build-check.sh before the build.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "sites" / "music" / "content"
CATALOG = CONTENT_DIR / "catalog.toml"
BASE_LOCALE = "en-US"
MEDIA_DIR = REPO_ROOT / "sites" / "music" / "media"

# Hosted file extension -> resource type.
MEDIA_TYPES = {".mp3": "audio", ".m4a": "audio", ".wav": "audio", ".mp4": "video"}

VOCAB_GROUPS = ("kind", "activity", "instrument", "genre", "status", "type")
TOP_KEYS = {"default_checklist", "vocabulary", "piece"}
PIECE_REQUIRED = {"id", "title", "kind", "activity", "instrument", "genre", "summary"}
PIECE_OPTIONAL = {
    "subtitle",
    "status",
    "checklist",
    "resources_heading",
    "checklist_heading",
    "resource",
}
RESOURCE_KEYS = {"title", "file", "url", "type", "date", "desc"}

_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_DATE_RE = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")


class CatalogError(Exception):
    """The catalog has problems; .problems lists them all."""

    def __init__(self, problems: list[str]):
        super().__init__(f"{len(problems)} catalog problem(s)")
        self.problems = problems


def _strings(value) -> bool:
    return isinstance(value, list) and value and all(isinstance(v, str) for v in value)


def validate(data: dict, media_dir: Path = MEDIA_DIR) -> list[str]:
    problems: list[str] = []
    add = problems.append

    for k in sorted(set(data) - TOP_KEYS):
        add(f"unknown top-level field {k!r}")

    vocab = data.get("vocabulary", {})
    for group in VOCAB_GROUPS:
        if not vocab.get(group):
            add(f"[vocabulary.{group}] is missing or empty")
    for group in sorted(set(vocab) - set(VOCAB_GROUPS)):
        add(f"unknown vocabulary group [vocabulary.{group}]")

    def known(group: str, key, where: str) -> None:
        if key not in vocab.get(group, {}):
            add(f"{where}: {group} {key!r} is not in [vocabulary.{group}]")

    if not _strings(data.get("default_checklist")):
        add("default_checklist must be a non-empty list of strings")

    pieces = data.get("piece", [])
    if not pieces:
        add("no [[piece]] entries")
    seen: set[str] = set()
    for n, p in enumerate(pieces, 1):
        pid = p.get("id", f"#{n}")
        where = f"piece {pid!r}"
        for k in sorted(PIECE_REQUIRED - set(p)):
            add(f"{where}: missing {k!r}")
        for k in sorted(set(p) - PIECE_REQUIRED - PIECE_OPTIONAL):
            add(f"{where}: unknown field {k!r}")
        if not isinstance(pid, str) or not _ID_RE.match(pid):
            add(f"{where}: id must be lowercase letters, digits and hyphens")
        elif pid in seen:
            add(f"{where}: duplicate id")
        seen.add(pid)
        if "kind" in p:
            known("kind", p["kind"], where)
        known("status", p.get("status", "not-started"), where)
        for group in ("activity", "instrument", "genre"):
            if group in p:
                if not _strings(p[group]):
                    add(f"{where}: {group} must be a non-empty list")
                else:
                    for key in p[group]:
                        known(group, key, where)
        if "checklist" in p and not _strings(p["checklist"]):
            add(f"{where}: checklist must be a non-empty list of strings")

        resources = p.get("resource", [])
        if not resources:
            add(f"{where}: no [[piece.resource]] entries")
        for m, r in enumerate(resources, 1):
            rwhere = f"{where}, resource {m} ({r.get('title', 'untitled')!r})"
            for k in sorted(set(r) - RESOURCE_KEYS):
                add(f"{rwhere}: unknown field {k!r}")
            if not r.get("title"):
                add(f"{rwhere}: missing title")
            if ("file" in r) == ("url" in r):
                add(f"{rwhere}: needs exactly one of file or url")
            elif "file" in r:
                name = r["file"]
                ext = Path(name).suffix.lower()
                if "/" in name or "\\" in name or name.startswith("."):
                    add(f"{rwhere}: file must be a plain file name")
                elif ext not in MEDIA_TYPES:
                    add(f"{rwhere}: unknown media type {ext!r}")
                elif not (media_dir / name).is_file():
                    add(f"{rwhere}: {name!r} not found in {media_dir.name}/")
                if "type" in r and r["type"] != MEDIA_TYPES.get(ext):
                    add(f"{rwhere}: type {r['type']!r} contradicts the file extension")
            else:
                parts = urlsplit(r["url"])
                if parts.scheme not in ("http", "https") or not parts.netloc:
                    add(f"{rwhere}: url must be an http(s) address")
                if "type" not in r:
                    add(f"{rwhere}: an external url needs a type")
                else:
                    known("type", r["type"], rwhere)
            if "date" in r and not _DATE_RE.match(str(r["date"])):
                add(f"{rwhere}: date must be YYYY or YYYY-MM")

    return problems


def load_catalog(path: Path = CATALOG, media_dir: Path = MEDIA_DIR) -> dict:
    """Parse and validate; raise CatalogError listing every problem."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise CatalogError([f"{path.name}: not valid TOML - {exc}"]) from exc
    problems = validate(data, media_dir)
    if problems:
        raise CatalogError(problems)
    return data


# --- translations ------------------------------------------------------------

TRANSLATED_PIECE_FIELDS = (
    "title",
    "subtitle",
    "summary",
    "resources_heading",
    "checklist_heading",
    "checklist",
)


def fingerprint(value) -> str:
    """Short, stable fingerprint of some English text (any JSON value)."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def piece_source(piece: dict) -> dict:
    """The English text of a piece that a translation is based on."""
    text = {k: piece[k] for k in TRANSLATED_PIECE_FIELDS if k in piece}
    text["resource"] = [[r["title"], r.get("desc", "")] for r in piece["resource"]]
    return text


def expected_sources(data: dict) -> dict:
    """Fingerprints a fully up-to-date translation must record."""
    return {
        "default_checklist": fingerprint(data["default_checklist"]),
        "vocabulary": {g: fingerprint(data["vocabulary"][g]) for g in VOCAB_GROUPS},
        "piece": {p["id"]: fingerprint(piece_source(p)) for p in data["piece"]},
    }


def translation_path(locale: str) -> Path:
    return CONTENT_DIR / f"catalog.{locale}.toml"


def check_translation(data: dict, tr: dict, locale: str) -> list[str]:
    """Problems with one locale's translation file against the English."""
    problems: list[str] = []
    add = problems.append
    name = translation_path(locale).name
    want = expected_sources(data)
    have = tr.get("source", {})

    for k in sorted(set(tr) - {"source", "vocabulary", "default_checklist", "piece"}):
        add(f"{name}: unknown top-level field {k!r}")

    if have.get("default_checklist") != want["default_checklist"]:
        add(f"{name}: default_checklist is missing or out of date")
    elif len(tr.get("default_checklist", [])) != len(data["default_checklist"]):
        add(f"{name}: default_checklist has the wrong number of items")

    vocab = tr.get("vocabulary", {})
    for group in VOCAB_GROUPS:
        if have.get("vocabulary", {}).get(group) != want["vocabulary"][group]:
            add(f"{name}: [vocabulary.{group}] is missing or out of date")
        elif set(vocab.get(group, {})) != set(data["vocabulary"][group]):
            add(f"{name}: [vocabulary.{group}] keys differ from the English")

    pieces = tr.get("piece", {})
    for piece in data["piece"]:
        pid, where = piece["id"], f"{name}: piece {piece['id']!r}"
        t = pieces.get(pid)
        if t is None:
            add(f"{where}: missing")
            continue
        if t.get("source") != want["piece"][pid]:
            add(f"{where}: out of date (its English changed since it was translated)")
            continue
        allowed = {"source", "resource", *TRANSLATED_PIECE_FIELDS}
        for k in sorted(set(t) - allowed):
            add(f"{where}: unknown field {k!r}")
        for k in ("summary", "subtitle", "resources_heading", "checklist_heading"):
            if k in piece and not t.get(k):
                add(f"{where}: missing {k!r}")
        if "checklist" in piece and len(t.get("checklist", [])) != len(
            piece["checklist"]
        ):
            add(f"{where}: checklist has the wrong number of items")
        resources = t.get("resource", [])
        if len(resources) != len(piece["resource"]):
            add(f"{where}: needs {len(piece['resource'])} resource entries")
            continue
        for n, (r, rt) in enumerate(zip(piece["resource"], resources), 1):
            for k in sorted(set(rt) - {"title", "desc"}):
                add(f"{where}, resource {n}: unknown field {k!r}")
            if not rt.get("title"):
                add(f"{where}, resource {n}: missing title")
            if r.get("desc") and not rt.get("desc"):
                add(f"{where}, resource {n}: missing desc")
    for pid in sorted(set(pieces) - set(want["piece"])):
        add(f"{name}: piece {pid!r} is not in the English catalog")
    return problems


def load_translation(data: dict, locale: str) -> dict:
    """Parse and check one locale's translation; raise CatalogError."""
    path = translation_path(locale)
    if not path.is_file():
        raise CatalogError([f"{path.name}: missing (needed for locale {locale})"])
    try:
        tr = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise CatalogError([f"{path.name}: not valid TOML - {exc}"]) from exc
    problems = check_translation(data, tr, locale)
    if problems:
        raise CatalogError(problems)
    return tr


def localize(data: dict, locale: str) -> dict:
    """The catalog as seen in one locale (English for the base locale)."""
    if locale == BASE_LOCALE:
        return data
    tr = load_translation(data, locale)
    out = {
        "default_checklist": tr["default_checklist"],
        "vocabulary": tr["vocabulary"],
        "piece": [],
    }
    for piece in data["piece"]:
        t = tr["piece"][piece["id"]]
        merged = dict(piece)
        for k in TRANSLATED_PIECE_FIELDS:
            if k in t:
                merged[k] = t[k]
        merged["resource"] = [
            {**r, "title": rt["title"], "desc": rt.get("desc", r.get("desc", ""))}
            for r, rt in zip(piece["resource"], t["resource"])
        ]
        out["piece"].append(merged)
    return out


def translation_locales() -> list[str]:
    """Locales with a translation file present."""
    return sorted(
        p.name[len("catalog.") : -len(".toml")]
        for p in CONTENT_DIR.glob("catalog.*.toml")
    )


def print_status(data: dict) -> None:
    want = expected_sources(data)
    print("Fingerprints of the current English (record as `source`):")
    print(f"  default_checklist: {want['default_checklist']}")
    for group, fp in want["vocabulary"].items():
        print(f"  vocabulary.{group}: {fp}")
    for locale in translation_locales():
        try:
            load_translation(data, locale)
            print(f"{locale}: up to date")
        except CatalogError as exc:
            print(f"{locale}: {len(exc.problems)} problem(s)")
            for problem in exc.problems:
                print(f"  - {problem}")
    print("Pieces:")
    for pid, fp in want["piece"].items():
        print(f"  {pid}: {fp}")


def main() -> int:
    try:
        data = load_catalog()
        if "--status" in sys.argv[1:]:
            print_status(data)
            return 0
        for locale in translation_locales():
            load_translation(data, locale)
    except CatalogError as exc:
        for problem in exc.problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    pieces = data["piece"]
    resources = sum(len(p["resource"]) for p in pieces)
    locales = ", ".join([BASE_LOCALE, *translation_locales()])
    print(f"music catalog OK ({len(pieces)} pieces, {resources} resources; {locales}).")
    return 0
