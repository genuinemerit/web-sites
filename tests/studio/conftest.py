"""Shared helpers and generated sample files for the tools/studio tests.

Every sample is made on the fly (ffmpeg test sources, Pillow, Ghostscript),
never taken from real media, and lives in pytest's tmp_path (under /tmp,
which Ubuntu's AppArmor profile for qpdf allows).
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from PIL import Image

STUDIO = Path(__file__).resolve().parents[2] / "tools" / "studio"

# Tags FFmpeg writes itself (container brand, encoder, track handler) -
# technical, not about the recording. Anything else is metadata.
TECH_TAGS = {
    "major_brand", "minor_version", "compatible_brands", "encoder",
    "handler_name", "vendor_id", "language",
}  # fmt: skip


def run_tool(tool: str, *args: str | Path) -> subprocess.CompletedProcess:
    """Run tools/studio/<tool> and capture its output (never raises)."""
    return subprocess.run(
        ["bash", str(STUDIO / tool), *map(str, args)],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*cmd: str | Path) -> str:
    """Run a helper command, fail the test if it fails, return stdout."""
    return subprocess.run(
        list(map(str, cmd)), capture_output=True, text=True, check=True
    ).stdout


def ffprobe(path: Path) -> dict:
    return json.loads(
        run(
            "ffprobe", "-v", "error", "-show_format", "-show_streams",
            "-show_chapters", "-of", "json", path,
        )
    )  # fmt: skip


def ffmpeg(*args: str | Path) -> None:
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", *args)


# --- samples ----------------------------------------------------------------


@pytest.fixture
def src_dir(tmp_path: Path) -> Path:
    d = tmp_path / "originals"
    d.mkdir()
    return d


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    return tmp_path / "out"


def make_wav(path: Path, seconds: int = 2) -> Path:
    ffmpeg("-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", path)
    return path


def make_mp3(path: Path, bitrate: str = "128k") -> Path:
    """MP3 with tags a phone or DAW would leave behind."""
    ffmpeg(
        "-f", "lavfi", "-i", "sine=frequency=330:duration=2",
        "-c:a", "libmp3lame", "-b:a", bitrate,
        "-metadata", "title=Secret Title", "-metadata", "artist=Someone",
        "-metadata", "date=2020-01-01", path,
    )  # fmt: skip
    return path


def make_video(path: Path, height: int = 240, bitrate: str = "2M") -> Path:
    """H.264 + AAC MP4 with a location tag, like phone video."""
    ffmpeg(
        "-f", "lavfi", "-i", f"testsrc2=size={height * 4 // 3}x{height}:rate=25:duration=2",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-c:v", "libx264", "-preset", "ultrafast", "-b:v", bitrate,
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
        "-metadata", "location=+40.4468-079.9915/",
        "-metadata", "creation_time=2020-01-01T00:00:00Z", path,
    )  # fmt: skip
    return path


def gps_exif(orientation: int = 1) -> Image.Exif:
    exif = Image.Exif()
    exif[0x0112] = orientation  # Orientation
    exif[0x010F] = "TestCam"  # Make
    gps = exif.get_ifd(0x8825)
    gps[1] = "N"
    gps[2] = (40.0, 26.0, 46.0)
    return exif


def make_jpeg(
    path: Path,
    size: tuple[int, int] = (300, 200),
    quality: int = 90,
    orientation: int = 1,
    noise: bool = False,
) -> Path:
    if noise:
        im = Image.effect_noise(size, 60).convert("RGB")
    else:
        im = Image.new("RGB", size, (150, 40, 40))
    im.save(path, quality=quality, exif=gps_exif(orientation))
    return path


def make_pdf(path: Path, pages: int = 1) -> Path:
    """A text PDF with full document information (title, author, ...)."""
    ps = (
        "[ /Title (Sample Title) /Author (Some Author) /Creator (SomeApp)"
        " /Keywords (k1 k2) /DOCINFO pdfmark "
        + " ".join(
            f"/Helvetica findfont 24 scalefont setfont 72 700 moveto (Page {n}) show"
            " showpage"
            for n in range(1, pages + 1)
        )
    )
    run(
        "gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
        f"-sOutputFile={path}", "-c", ps,
    )  # fmt: skip
    return path


def make_image_pdf(path: Path, tmp: Path) -> Path:
    """A PDF holding one big noisy photo - Ghostscript can shrink it."""
    jpg = make_jpeg(tmp / "big_for_pdf.jpg", size=(2400, 1800), quality=95, noise=True)
    run("magick", jpg, "-density", "300", path)
    return path


def pdf_info(path: Path) -> dict:
    """The PDF's document information dictionary ({} if none)."""
    trailer = json.loads(
        run("qpdf", "--json=2", "--json-key=qpdf", "--json-object=trailer", path)
    )["qpdf"][1]["trailer"]["value"]
    ref = trailer.get("/Info")
    if not ref:
        return {}
    obj = json.loads(
        run("qpdf", "--json=2", "--json-key=qpdf", f"--json-object={ref}", path)
    )["qpdf"][1][f"obj:{ref}"]
    return obj["value"]


def pdf_has_xmp(path: Path) -> bool:
    plain = subprocess.run(
        ["qpdf", "--qdf", "--object-streams=disable", str(path), "-"],
        capture_output=True,
        check=True,
    ).stdout
    return b"/Metadata" in plain


def pdf_is_linearized(path: Path) -> bool:
    return "linearization data" in run("qpdf", "--show-linearization", path)
