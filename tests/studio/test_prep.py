"""prep.sh: one site, every media type, then the media check.

Runs from the fake repo (fake_repo fixture), never the real sites/.
"""

from pathlib import Path

import pytest

from .conftest import make_jpeg, make_mp3, make_pdf, make_wav, run_tool


@pytest.fixture
def demo(fake_repo: Path):
    studio = fake_repo / "tools" / "studio"
    site = fake_repo / "sites" / "demo"

    def run(*args):
        return run_tool("prep.sh", *args, studio=studio)

    return run, site


def fill_raw(raw: Path) -> None:
    """One of each kind, one of them in a subfolder."""
    (raw / "docs").mkdir()
    make_jpeg(raw / "Photo 1.jpg")
    make_pdf(raw / "docs" / "Flyer.pdf")
    make_mp3(raw / "Song.mp3")
    make_wav(raw / "Take.wav")


def test_everything_in_raw_goes_to_its_folder(demo):
    run, site = demo
    fill_raw(site / "raw")
    result = run("demo")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all prepped" in result.stdout
    assert [p.name for p in (site / "static" / "img").iterdir()] == ["photo_1.jpg"]
    assert [p.name for p in (site / "static" / "docs").iterdir()] == ["flyer.pdf"]
    assert sorted(p.name for p in (site / "media").iterdir()) == [
        "song.mp3",
        "take.mp3",
    ]


def test_explicit_inputs(demo, src_dir: Path):
    run, site = demo
    photo = make_jpeg(src_dir / "elsewhere.jpg")
    assert run("demo", photo).returncode == 0
    assert (site / "static" / "img" / "elsewhere.jpg").is_file()


def test_unsupported_file_is_reported_and_fails(demo):
    run, site = demo
    make_jpeg(site / "raw" / "photo.jpg")
    (site / "raw" / "notes.txt").write_text("not media")
    (site / "raw" / "README").write_text("no extension")
    result = run("demo")
    assert result.returncode == 1
    assert result.stderr.count("UNSUPPORTED") == 2
    assert (site / "static" / "img" / "photo.jpg").is_file()  # the rest still ran


def test_check_catches_unprepped_files_already_there(demo, src_dir: Path):
    run, site = demo
    make_jpeg(site / "raw" / "new.jpg")
    (site / "static" / "img").mkdir(parents=True)
    make_jpeg(site / "static" / "img" / "sneaked-in.jpg")  # GPS and all
    result = run("demo")
    assert result.returncode == 1
    assert "sneaked-in.jpg: GPS" in result.stdout


def test_dry_run_writes_nothing(demo):
    run, site = demo
    fill_raw(site / "raw")
    result = run("--dry-run", "demo")
    assert result.returncode == 0, result.stderr
    assert "Dry run" in result.stdout
    assert not (site / "static").exists()
    assert not (site / "media").exists()


def test_skip_existing_passes_through(demo):
    run, site = demo
    make_mp3(site / "raw" / "song.mp3")
    assert run("demo").returncode == 0
    assert run("demo").returncode == 1  # output exists
    result = run("--skip-existing", "demo")
    assert result.returncode == 0, result.stderr
    assert "SKIP" in result.stdout


def test_map_file_collects_every_tool(demo, tmp_path: Path):
    run, site = demo
    fill_raw(site / "raw")
    map_file = tmp_path / "map.tsv"
    assert run("--map", map_file, "demo").returncode == 0
    rows = map_file.read_text().splitlines()
    assert rows[0] == "source\toutput"
    assert sorted(rows[1:]) == [
        "Flyer.pdf\tflyer.pdf",
        "Photo 1.jpg\tphoto_1.jpg",
        "Song.mp3\tsong.mp3",
        "Take.wav\ttake.mp3",
    ]


@pytest.mark.parametrize("args", [[], ["nosuch"], ["heirloom"], ["--bad", "demo"]])
def test_usage_errors(demo, args):
    run, _ = demo
    assert run(*args).returncode == 2


def test_no_raw_folder(demo):
    run, site = demo
    (site / "raw").rmdir()
    result = run("demo")
    assert result.returncode == 1
    assert "raw/ doesn't exist" in result.stderr
