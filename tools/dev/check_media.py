"""Check that every media file under sites/ has been prepped.

design/studio.md, step 4. Media means images, sound, video and PDFs.
Each file is analysed itself (no log or manifest): the check verifies
what the tools/studio prep tools guarantee, and changes nothing.

  all       type is one we serve (by content, not just extension); name
            and folders URL-safe: lowercase letters, digits, "_" and "-";
            at most media_max_mb (ansible/vhosts.yml)
  images    no EXIF, GPS, XMP, IPTC, comments or text chunks (a colour
            profile is fine); long edge at most 2048 px; one frame
  audio     MP3 (.mp3) or AAC (.m4a); at most 256 kbps; no tags beyond
            the technical ones FFmpeg writes; no chapters or cover art
  video     MP4: one H.264 (yuv420p) video stream, at most one AAC audio
            stream, at most 1080 px tall, index before media
            ("faststart"); same tag rules as audio
  PDF       passes qpdf --check, not encrypted, linearized, no XMP;
            document information at most a title and a modification date

Where: every site folder (sites/<site>/, not sites/_shared fonts/CSS),
skipping raw/ (originals), heirloom/ and build/. Favicons (.ico, .svg)
are skipped - they're made once by hand, not prepped.

  check_media.py                 every site
  check_media.py PATH...         just these files or folders
  check_media.py --staged        files staged for commit (the git
                                 pre-commit hook), as staged

Run via `poetry run` (needs Pillow). Exit 0 when clean, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SITES = REPO_ROOT / "sites"
SKIP_DIRS = {"raw", "heirloom", "build"}

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
UNSERVED_IMAGE_EXT = {".heic", ".heif", ".tif", ".tiff", ".bmp"}
AUDIO_EXT = {".mp3": "mp3", ".m4a": "aac"}
UNSERVED_AUDIO_EXT = {".wav", ".flac", ".ogg", ".opus", ".aac", ".wma", ".aiff"}
VIDEO_EXT = {".mp4"}
UNSERVED_VIDEO_EXT = {".mov", ".m4v", ".mkv", ".webm", ".avi"}
PDF_EXT = {".pdf"}
SKIP_EXT = {".ico", ".svg"}
MEDIA_EXT = (
    IMAGE_EXT
    | UNSERVED_IMAGE_EXT
    | set(AUDIO_EXT)
    | UNSERVED_AUDIO_EXT
    | VIDEO_EXT
    | UNSERVED_VIDEO_EXT
    | PDF_EXT
)

# Tags FFmpeg writes itself (container brand, encoder, track handler) -
# technical, not about the recording. Anything else is metadata.
TECH_TAGS = {
    "major_brand", "minor_version", "compatible_brands", "encoder",
    "handler_name", "vendor_id", "language",
}  # fmt: skip
MAX_EDGE = 2048
MAX_AUDIO_BPS = 256_000
MAX_VIDEO_HEIGHT = 1080
SAFE_NAME = re.compile(r"[a-z0-9][a-z0-9_-]*")

FIX = {
    "image": "re-make it with tools/studio/img_prep.sh",
    "audio": "re-make it with tools/studio/av_prep.sh",
    "video": "re-make it with tools/studio/av_prep.sh",
    "pdf": "re-make it with tools/studio/pdf_prep.sh",
}


def max_media_bytes() -> int:
    vhosts = REPO_ROOT / "ansible" / "vhosts.yml"
    text = vhosts.read_text(encoding="utf-8") if vhosts.is_file() else ""
    match = re.search(r"^media_max_mb:\s*(\d+)", text, re.MULTILINE)
    return int(match.group(1) if match else 100) * 1024 * 1024


def kind_of(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in IMAGE_EXT | UNSERVED_IMAGE_EXT:
        return "image"
    if ext in set(AUDIO_EXT) | UNSERVED_AUDIO_EXT:
        return "audio"
    if ext in VIDEO_EXT | UNSERVED_VIDEO_EXT:
        return "video"
    if ext in PDF_EXT:
        return "pdf"
    return None


def run(*cmd: str | Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(map(str, cmd)), capture_output=True, text=True, check=False
    )


# --- per-kind checks: each returns a list of problems -----------------------


def check_name(rel: Path) -> list[str]:
    parts = [*rel.parent.parts, rel.stem]
    bad = [p for p in parts if not SAFE_NAME.fullmatch(p)]
    problems = []
    if bad:
        problems.append(
            f"name not URL-safe ({', '.join(bad)}): use lowercase letters, digits, _ and -"
        )
    if rel.suffix != rel.suffix.lower():
        problems.append("extension must be lowercase")
    return problems


def check_image(path: Path) -> list[str]:
    if path.suffix.lower() in UNSERVED_IMAGE_EXT:
        return [f"{path.suffix} isn't a web image format"]
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            problems = []
            exif = im.getexif()
            if exif.get_ifd(0x8825):
                problems.append("GPS location in EXIF")
            if len(exif):
                problems.append(f"EXIF metadata ({len(exif)} tags)")
            for key in ("xmp", "XML:com.adobe.xmp", "comment", "iptc", "photoshop"):
                if im.info.get(key):
                    problems.append(f"{key} metadata")
            text = getattr(im, "text", None) or {}
            if text:
                problems.append(f"text chunks ({', '.join(sorted(text))})")
            if max(im.size) > MAX_EDGE:
                problems.append(f"{im.size[0]}x{im.size[1]}: long edge over {MAX_EDGE}")
            if getattr(im, "n_frames", 1) > 1:
                problems.append("multi-frame (animated) image")
            return problems
    except Exception as exc:  # noqa: BLE001 - any decoder error means unusable
        return [f"not a readable image ({exc})"]


def ffprobe(path: Path) -> dict | None:
    result = run(
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-show_chapters", "-of", "json", path,
    )  # fmt: skip
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def tag_problems(info: dict) -> list[str]:
    keys = set(info.get("format", {}).get("tags", {}))
    for stream in info.get("streams", []):
        keys |= set(stream.get("tags", {}))
    extra = sorted(keys - TECH_TAGS)
    problems = [f"metadata tags ({', '.join(extra)})"] if extra else []
    if info.get("chapters"):
        problems.append("chapters")
    return problems


def check_audio(path: Path) -> list[str]:
    ext = path.suffix.lower()
    if ext in UNSERVED_AUDIO_EXT:
        return [f"{ext} isn't served - MP3 or AAC (.m4a) only"]
    info = ffprobe(path)
    if info is None:
        return ["not readable audio"]
    streams = info["streams"]
    problems = tag_problems(info)
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if len(audio) != 1 or len(streams) != 1:
        kinds = ", ".join(s.get("codec_type", "?") for s in streams)
        problems.append(f"expected one audio stream, found: {kinds} (cover art?)")
    if audio and audio[0].get("codec_name") != AUDIO_EXT[ext]:
        problems.append(f"{ext} holds {audio[0].get('codec_name')}")
    bps = int(info["format"].get("bit_rate") or 0)
    if bps > MAX_AUDIO_BPS:
        problems.append(f"{bps // 1000} kbps (over {MAX_AUDIO_BPS // 1000})")
    return problems


def mp4_top_level_boxes(path: Path) -> list[str]:
    """The MP4's top-level box types, in file order."""
    boxes = []
    with path.open("rb") as f:
        while header := f.read(8):
            if len(header) < 8:
                break
            size = int.from_bytes(header[:4], "big")
            boxes.append(header[4:8].decode("latin-1"))
            if size == 1:
                size = int.from_bytes(f.read(8), "big")
                f.seek(size - 16, 1)
            elif size == 0:
                break
            else:
                f.seek(size - 8, 1)
    return boxes


def check_video(path: Path) -> list[str]:
    ext = path.suffix.lower()
    if ext in UNSERVED_VIDEO_EXT:
        return [f"{ext} isn't served - MP4 only"]
    info = ffprobe(path)
    if info is None:
        return ["not readable video"]
    problems = tag_problems(info)
    streams = info["streams"]
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if len(video) != 1 or len(audio) > 1 or len(streams) != len(video) + len(audio):
        kinds = ", ".join(s.get("codec_type", "?") for s in streams)
        problems.append(f"expected one video + at most one audio stream: {kinds}")
    if video:
        v = video[0]
        if v.get("codec_name") != "h264" or v.get("pix_fmt") != "yuv420p":
            problems.append(f"video is {v.get('codec_name')}/{v.get('pix_fmt')}")
        if int(v.get("height") or 0) > MAX_VIDEO_HEIGHT:
            problems.append(f"{v.get('height')} px tall (over {MAX_VIDEO_HEIGHT})")
    if audio and audio[0].get("codec_name") != "aac":
        problems.append(f"audio is {audio[0].get('codec_name')}, not AAC")
    boxes = mp4_top_level_boxes(path)
    if (
        "moov" in boxes
        and "mdat" in boxes
        and boxes.index("moov") > boxes.index("mdat")
    ):
        problems.append("index after media (no faststart)")
    return problems


def qpdf_json(path: Path, obj: str) -> dict:
    result = run("qpdf", "--json=2", "--json-key=qpdf", f"--json-object={obj}", path)
    return json.loads(result.stdout)["qpdf"][1]


def check_pdf(path: Path) -> list[str]:
    if path.read_bytes()[:5] != b"%PDF-":
        return ["not a PDF"]
    if run("qpdf", "--is-encrypted", path).returncode == 0:
        return ["encrypted"]
    problems = []
    if run("qpdf", "--check", path).returncode not in (0, 3):
        problems.append("fails qpdf --check")
    if "linearization data" not in run("qpdf", "--show-linearization", path).stdout:
        problems.append("not linearized")
    trailer = qpdf_json(path, "trailer")["trailer"]["value"]
    info_ref = trailer.get("/Info")
    if isinstance(info_ref, str):
        info = qpdf_json(path, info_ref)[f"obj:{info_ref}"]["value"]
        extra = sorted(set(info) - {"/Title", "/ModDate"})
        if extra:
            problems.append(f"document information ({', '.join(extra)})")
    root = qpdf_json(path, trailer["/Root"])[f"obj:{trailer['/Root']}"]["value"]
    if "/Metadata" in root:
        problems.append("XMP metadata")
    return problems


CHECKS = {
    "image": check_image,
    "audio": check_audio,
    "video": check_video,
    "pdf": check_pdf,
}


# --- finding files ------------------------------------------------------------


def in_scope(rel: Path) -> bool:
    """rel is relative to sites/. Media of a site, not its originals."""
    if len(rel.parts) < 2 or rel.parts[0].startswith("_") or rel.parts[0] == "heirloom":
        return False
    if SKIP_DIRS & set(rel.parts[1:-1]):
        return False
    return rel.suffix.lower() in MEDIA_EXT


def site_files(paths: list[Path]) -> list[Path]:
    found = []
    for base in paths:
        candidates = base.rglob("*") if base.is_dir() else [base]
        for path in candidates:
            if not path.is_file() or path.name.startswith("."):
                continue
            try:
                rel = path.resolve().relative_to(SITES)
            except ValueError:
                continue
            if in_scope(rel):
                found.append(path.resolve())
    return sorted(set(found))


def check_file(path: Path, rel: Path, max_bytes: int) -> list[str]:
    """rel: the path shown and name-checked (relative to sites/<site>/)."""
    kind = kind_of(path)
    if kind is None:
        return []
    problems = check_name(rel)
    if path.stat().st_size > max_bytes:
        problems.append(f"over {max_bytes // 1024 // 1024} MB")
    problems += CHECKS[kind](path)
    return [f"{p} - {FIX[kind]}" for p in problems]


def staged_files(tmp: Path, repo: Path = REPO_ROOT) -> list[tuple[Path, Path]]:
    """Copy the staged version of each staged media file into tmp.
    Returns (copy, path in repo) pairs. Unlike the full scan, this covers
    media staged anywhere in the repo, not just in site folders."""
    names = run(
        "git", "-C", repo, "diff", "--cached", "--name-only",
        "--diff-filter=ACMR", "-z",
    ).stdout.split("\0")  # fmt: skip
    pairs = []
    for name in filter(None, names):
        repo_path = Path(name)
        if repo_path.suffix.lower() not in MEDIA_EXT:
            continue
        copy = tmp / repo_path
        copy.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(
            ["git", "-C", str(repo), "show", f":{name}"],
            capture_output=True,
            check=True,
        ).stdout
        copy.write_bytes(blob)
        pairs.append((copy, repo_path))
    return pairs


def name_rel(repo_path: Path) -> Path:
    """The part of a repo path that must be URL-safe: below sites/<site>/
    for site files, the whole path otherwise."""
    parts = repo_path.parts
    if len(parts) > 2 and parts[0] == "sites":
        return Path(*parts[2:])
    return repo_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args(argv)
    for tool in ("ffprobe", "qpdf"):
        if not shutil.which(tool):
            print(f"Missing dependency: {tool}", file=sys.stderr)
            return 1

    max_bytes = max_media_bytes()
    failures = checked = 0
    with tempfile.TemporaryDirectory(prefix="check_media.") as tmp:
        if args.staged:
            pairs = staged_files(Path(tmp))
        else:
            files = site_files([p.resolve() for p in args.paths] or [SITES])
            pairs = [(f, f.relative_to(REPO_ROOT)) for f in files]
        for path, repo_path in pairs:
            checked += 1
            for problem in check_file(path, name_rel(repo_path), max_bytes):
                failures += 1
                print(f"{repo_path}: {problem}")
    if failures:
        print(f"\n{failures} problem(s) in {checked} media file(s).", file=sys.stderr)
        return 1
    print(f"{checked} media file(s) checked, all prepped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
