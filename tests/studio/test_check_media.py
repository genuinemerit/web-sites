"""tools/dev/check_media.py: prepped files pass, unprepped ones fail.

The round trip is the main guarantee: whatever the prep tools write
passes the check, and the raw samples they start from do not.
"""

import subprocess
from pathlib import Path

import check_media  # on sys.path via conftest
import pytest
from PIL import Image

from .conftest import (
    ffmpeg,
    make_jpeg,
    make_mp3,
    make_pdf,
    make_video,
    make_wav,
    run_tool,
)

MAX = 100 * 1024 * 1024


def problems(path: Path, rel: str | None = None) -> list[str]:
    return check_media.check_file(path, Path(rel or path.name), MAX)


# --- round trip ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("tool", "make", "name"),
    [
        ("av_prep.sh", make_mp3, "song.mp3"),
        ("av_prep.sh", make_wav, "take.wav"),
        ("av_prep.sh", make_video, "clip.mp4"),
        ("img_prep.sh", make_jpeg, "photo.jpg"),
        ("pdf_prep.sh", make_pdf, "doc.pdf"),
    ],
)
def test_raw_fails_and_prepped_passes(tool, make, name, src_dir, out_dir):
    raw = make(src_dir / name)
    assert problems(raw), f"raw {name} should not pass"
    assert run_tool(tool, "-o", out_dir, raw).returncode == 0
    [prepped] = out_dir.iterdir()
    assert problems(prepped) == []


def test_pdf_title_is_allowed(src_dir, out_dir):
    raw = make_pdf(src_dir / "doc.pdf")
    assert run_tool("pdf_prep.sh", "-o", out_dir, "--keep-info", raw).returncode == 0
    assert problems(out_dir / "doc.pdf") == []


def test_transparent_png_passes(src_dir, out_dir):
    Image.new("RGBA", (64, 64), (0, 0, 255, 128)).save(src_dir / "logo.png")
    assert run_tool("img_prep.sh", "-o", out_dir, src_dir).returncode == 0
    assert problems(out_dir / "logo.png") == []


# --- individual rules -------------------------------------------------------------


def test_gps_is_named(src_dir):
    found = problems(make_jpeg(src_dir / "photo.jpg"))
    assert any("GPS" in p for p in found)
    assert all("img_prep.sh" in p for p in found)


def test_exif_without_gps(src_dir):
    exif = Image.Exif()
    exif[0x010F] = "TestCam"  # camera make only
    path = src_dir / "photo.jpg"
    Image.new("RGB", (10, 10)).save(path, exif=exif)
    found = problems(path)
    assert any("EXIF" in p for p in found)
    assert not any("GPS" in p for p in found)


def test_oversized_image(src_dir):
    path = src_dir / "big.webp"
    Image.new("RGB", (3000, 100)).save(path)
    assert any("long edge" in p for p in problems(path))


def test_png_text_chunk(src_dir):
    from PIL import PngImagePlugin

    info = PngImagePlugin.PngInfo()
    info.add_text("Software", "SomeEditor")
    path = src_dir / "shot.png"
    Image.new("RGB", (10, 10)).save(path, pnginfo=info)
    assert any("text chunks" in p for p in problems(path))


@pytest.mark.parametrize("ext", [".heic", ".tif", ".bmp"])
def test_unserved_image_types(src_dir, ext):
    path = src_dir / f"pic{ext}"
    path.write_bytes(b"x")
    assert any("web image format" in p for p in problems(path))


def test_wav_is_not_served(src_dir):
    assert any("isn't served" in p for p in problems(make_wav(src_dir / "a.wav")))


def test_mp3_cover_art(src_dir, tmp_path):
    cover = make_jpeg(tmp_path / "cover.jpg")
    path = src_dir / "with_art.mp3"
    ffmpeg(
        "-f", "lavfi", "-i", "sine=duration=1", "-i", cover,
        "-map", "0", "-map", "1", "-c:a", "libmp3lame", "-c:v", "copy",
        "-map_metadata", "-1", "-id3v2_version", "3", path,
    )  # fmt: skip
    assert any("cover art" in p for p in problems(path))


def test_video_without_faststart(src_dir):
    path = make_video(src_dir / "clip.mp4")
    assert any("faststart" in p for p in problems(path))


def test_tall_video(src_dir, tmp_path):
    src = make_video(tmp_path / "tall.mp4", height=1200, bitrate="100k")
    path = src_dir / "tall.mp4"
    ffmpeg(
        "-i", src, "-c", "copy", "-map_metadata", "-1", "-movflags", "+faststart", path
    )
    assert any("px tall" in p for p in problems(path))


def test_pdf_not_linearized_with_info(src_dir):
    found = problems(make_pdf(src_dir / "doc.pdf"))
    assert any("not linearized" in p for p in found)
    assert any("document information" in p for p in found)


def test_encrypted_pdf(src_dir, tmp_path):
    plain = make_pdf(tmp_path / "plain.pdf")
    path = src_dir / "locked.pdf"
    subprocess.run(
        ["qpdf", "--encrypt", "u", "o", "256", "--", str(plain), str(path)],
        check=True,
    )
    assert problems(path) == ["encrypted - re-make it with tools/studio/pdf_prep.sh"]


def test_fake_pdf(src_dir):
    path = src_dir / "fake.pdf"
    path.write_text("hello")
    assert any("not a PDF" in p for p in problems(path))


def test_size_limit(src_dir, out_dir):
    raw = make_jpeg(src_dir / "photo.jpg")
    assert run_tool("img_prep.sh", "-o", out_dir, raw).returncode == 0
    found = check_media.check_file(out_dir / "photo.jpg", Path("photo.jpg"), 10)
    assert any("over 0 MB" in p for p in found)


# --- names and scope ----------------------------------------------------------


@pytest.mark.parametrize(
    ("rel", "ok"),
    [
        ("img/openmic/portrait-01-800.webp", True),
        ("song_take_2.mp3", True),
        ("vid/Taiji_for_Balance.mp4", False),
        ("img/My Photo.jpg", False),
        ("img/photo.JPG", False),
        ("Img/photo.jpg", False),
        ("img/café.jpg", False),
    ],
)
def test_names(rel: str, ok: bool):
    assert (check_media.check_name(Path(rel)) == []) is ok


@pytest.mark.parametrize(
    ("rel", "ok"),
    [
        ("music/media/song.mp3", True),
        ("taiji/static/img/tree.webp", True),
        ("taiji/content/en-US/photo.jpg", True),
        ("music/raw/original.wav", False),
        ("music/heirloom/old.jpg", False),
        ("music/build/img/x.webp", False),
        ("heirloom/music/x.jpg", False),
        ("_shared/static/x.png", False),
        ("music/static/favicon.svg", False),
        ("music/static/css/site.css", False),
    ],
)
def test_scope(rel: str, ok: bool):
    assert check_media.in_scope(Path(rel)) is ok


# --- staged files (the git pre-commit hook) ------------------------------------


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_staged_checks_the_staged_version(tmp_path, out_dir):
    repo = tmp_path / "repo"
    (repo / "sites" / "demo" / "static" / "img").mkdir(parents=True)
    git(repo, "init", "-q")
    raw = make_jpeg(tmp_path / "raw.jpg")
    assert run_tool("img_prep.sh", "-o", out_dir, raw).returncode == 0
    target = repo / "sites" / "demo" / "static" / "img" / "photo.jpg"

    target.write_bytes(raw.read_bytes())  # stage the raw, GPS and all ...
    git(repo, "add", ".")
    target.write_bytes((out_dir / "raw.jpg").read_bytes())  # ... fix only on disk

    staged = check_media.staged_files(tmp_path / "copies", repo)
    assert [rel for _, rel in staged] == [Path("sites/demo/static/img/photo.jpg")]
    [(copy, _)] = staged
    assert any("GPS" in p for p in problems(copy))
