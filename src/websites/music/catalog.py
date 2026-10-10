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
  - dates are YYYY or YYYY-MM; featured ids exist

    python -m websites.music.catalog      # check, exit 1 on problems

Run by tools/dev/pre-build-check.sh before the build.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG = REPO_ROOT / "sites" / "music" / "content" / "catalog.toml"
MEDIA_DIR = REPO_ROOT / "sites" / "music" / "media"

# Hosted file extension -> resource type.
MEDIA_TYPES = {".mp3": "audio", ".m4a": "audio", ".wav": "audio", ".mp4": "video"}

VOCAB_GROUPS = ("kind", "activity", "instrument", "genre", "status", "type")
TOP_KEYS = {"featured", "default_checklist", "vocabulary", "piece"}
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

    for fid in data.get("featured", []):
        if fid not in seen:
            add(f"featured: no piece with id {fid!r}")
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


def main() -> int:
    try:
        data = load_catalog()
    except CatalogError as exc:
        for problem in exc.problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    pieces = data["piece"]
    resources = sum(len(p["resource"]) for p in pieces)
    print(f"music catalog OK ({len(pieces)} pieces, {resources} resources).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
