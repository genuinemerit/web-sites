"""Where the prep tools write (tools/studio/common.sh, design/studio.md).

Images go to sites/<site>/static/img/, PDFs to static/docs/, audio and
video to media/. The site comes from --site or from where the sources
are; -o overrides; otherwise it is a usage error - no default folder.
All runs use a fake repo (the fake_repo fixture), never the real sites/.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from .conftest import make_jpeg, make_mp3, make_pdf, run_tool

# tool, sample maker, sample name, type folder, output name
TOOLS: list[tuple[str, Callable[[Path], Path], str, str, str]] = [
    ("av_prep.sh", make_mp3, "Song.mp3", "media", "song.mp3"),
    ("img_prep.sh", make_jpeg, "Photo.jpg", "static/img", "photo.jpg"),
    ("pdf_prep.sh", make_pdf, "Doc.pdf", "static/docs", "doc.pdf"),
]


@pytest.fixture(params=TOOLS, ids=[t[0] for t in TOOLS])
def case(request, fake_repo: Path):
    tool, make, sample, type_dir, output = request.param
    studio = fake_repo / "tools" / "studio"

    def run(*args):
        return run_tool(tool, *args, studio=studio)

    return run, make, sample, type_dir, output


def test_site_from_source_location(case, fake_repo: Path):
    run, make, sample, type_dir, output = case
    src = make(fake_repo / "sites" / "demo" / "raw" / sample)
    result = run(src)
    assert result.returncode == 0, result.stderr
    assert (fake_repo / "sites" / "demo" / type_dir / output).is_file()


def test_site_from_folder_input(case, fake_repo: Path):
    run, make, sample, type_dir, output = case
    raw = fake_repo / "sites" / "demo" / "raw"
    make(raw / sample)
    assert run(raw).returncode == 0
    assert (fake_repo / "sites" / "demo" / type_dir / output).is_file()


def test_site_option(case, fake_repo: Path, src_dir: Path):
    run, make, sample, type_dir, output = case
    src = make(src_dir / sample)
    result = run("--site", "other", src)
    assert result.returncode == 0, result.stderr
    assert (fake_repo / "sites" / "other" / type_dir / output).is_file()


def test_output_option_wins(case, fake_repo: Path, out_dir: Path):
    run, make, sample, type_dir, output = case
    src = make(fake_repo / "sites" / "demo" / "raw" / sample)
    assert run("--site", "other", "-o", out_dir, src).returncode == 0
    assert (out_dir / output).is_file()
    assert not (fake_repo / "sites" / "demo" / type_dir).exists()
    assert not (fake_repo / "sites" / "other" / type_dir).exists()


def test_no_site_is_a_usage_error(case, src_dir: Path):
    run, make, sample, _, _ = case
    result = run(make(src_dir / sample))
    assert result.returncode == 2
    assert "--site" in result.stderr


def test_sources_from_two_sites_is_a_usage_error(case, fake_repo: Path):
    run, make, sample, _, _ = case
    a = make(fake_repo / "sites" / "demo" / "raw" / sample)
    b = make(fake_repo / "sites" / "other" / "raw" / f"b_{sample}")
    assert run(a, b).returncode == 2


@pytest.mark.parametrize("folder", ["heirloom", "_shared"])
def test_heirloom_and_shared_are_not_sites(case, fake_repo: Path, folder: str):
    run, make, sample, _, _ = case
    assert run(make(fake_repo / "sites" / folder / "raw" / sample)).returncode == 2


@pytest.mark.parametrize("name", ["nosuch", "../demo", "heirloom", "Demo"])
def test_unknown_site_is_a_usage_error(case, src_dir: Path, name: str):
    run, make, sample, _, _ = case
    result = run("--site", name, make(src_dir / sample))
    assert result.returncode == 2
    assert "No such site" in result.stderr
