"""av_prep.sh: what happens to each kind of audio and video file."""

from pathlib import Path

from .conftest import (
    TECH_TAGS,
    ffprobe,
    make_mp3,
    make_video,
    make_wav,
    run_tool,
)


def tag_keys(info: dict) -> set[str]:
    """Every format and stream tag name in an ffprobe result."""
    keys = set(info["format"].get("tags", {}))
    for stream in info["streams"]:
        keys |= set(stream.get("tags", {}))
    return keys


def test_wav_becomes_mp3(src_dir: Path, out_dir: Path):
    make_wav(src_dir / "Take 1.wav")
    result = run_tool("av_prep.sh", "-o", out_dir, src_dir)
    assert result.returncode == 0, result.stderr
    info = ffprobe(out_dir / "take_1.mp3")
    assert [s["codec_name"] for s in info["streams"]] == ["mp3"]


def test_modest_mp3_is_copied_without_tags(src_dir: Path, out_dir: Path):
    src = make_mp3(src_dir / "song.mp3", bitrate="128k")
    result = run_tool("av_prep.sh", "-o", out_dir, src)
    assert result.returncode == 0, result.stderr
    assert "COPY" in result.stdout
    assert tag_keys(ffprobe(out_dir / "song.mp3")) <= TECH_TAGS


def test_high_bitrate_mp3_is_reencoded(src_dir: Path, out_dir: Path):
    src = make_mp3(src_dir / "song.mp3", bitrate="320k")
    result = run_tool("av_prep.sh", "-o", out_dir, src)
    assert result.returncode == 0, result.stderr
    assert "ENCODE" in result.stdout


def test_phone_video_is_reencoded_without_location(src_dir: Path, out_dir: Path):
    src = make_video(src_dir / "Clip.mp4", bitrate="2M")
    assert "location" in tag_keys(ffprobe(src))
    result = run_tool("av_prep.sh", "-o", out_dir, src)
    assert result.returncode == 0, result.stderr
    assert "ENCODE" in result.stdout
    info = ffprobe(out_dir / "clip_video.mp4")
    assert tag_keys(info) <= TECH_TAGS
    assert [s["codec_name"] for s in info["streams"]] == ["h264", "aac"]


def test_low_bitrate_h264_is_copied(src_dir: Path, out_dir: Path):
    src = make_video(src_dir / "small.mp4", bitrate="20k")
    result = run_tool("av_prep.sh", "-o", out_dir, src)
    assert result.returncode == 0, result.stderr
    assert "COPY" in result.stdout
    assert tag_keys(ffprobe(out_dir / "small_video.mp4")) <= TECH_TAGS


def test_tall_video_is_scaled_down(src_dir: Path, out_dir: Path):
    src = make_video(src_dir / "tall.mp4", height=240, bitrate="20k")
    result = run_tool("av_prep.sh", "-o", out_dir, "--max-height", "120", src)
    assert result.returncode == 0, result.stderr
    video = ffprobe(out_dir / "tall_video.mp4")["streams"][0]
    assert video["height"] == 120


def test_mp4_starts_before_download_ends(src_dir: Path, out_dir: Path):
    """faststart: the index ("moov") comes before the media ("mdat")."""
    src = make_video(src_dir / "clip.mp4")
    assert run_tool("av_prep.sh", "-o", out_dir, src).returncode == 0
    data = (out_dir / "clip_video.mp4").read_bytes()
    assert data.index(b"moov") < data.index(b"mdat")


def test_non_media_file_fails(src_dir: Path, out_dir: Path):
    junk = src_dir / "notes.txt"
    junk.write_text("not audio")
    result = run_tool("av_prep.sh", "-o", out_dir, junk)
    assert result.returncode == 1
    assert "no audio or video" in result.stderr
