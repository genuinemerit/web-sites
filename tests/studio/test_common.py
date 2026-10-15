"""Rules every studio prep tool shares (design/studio.md).

Never touch originals, never overwrite, never write beside a source,
refuse name clashes, URL-safe names, dry runs write nothing, a usable
file mode, and the same exit codes.
"""

import os
import stat
from collections.abc import Callable
from pathlib import Path

import pytest

from .conftest import make_jpeg, make_mp3, make_pdf, run_tool, sha256

# tool, sample maker, output name for a source called "Café Ñandú (v2)"
TOOLS: list[tuple[str, Callable[[Path], Path], str, str]] = [
    ("av_prep.sh", make_mp3, ".mp3", "cafe_nandu_v2.mp3"),
    ("img_prep.sh", make_jpeg, ".jpg", "cafe_nandu_v2.jpg"),
    ("pdf_prep.sh", make_pdf, ".pdf", "cafe_nandu_v2.pdf"),
]
IDS = [t[0] for t in TOOLS]


@pytest.fixture(params=TOOLS, ids=IDS)
def tool(request, src_dir: Path):
    name, make, ext, expected = request.param
    sample = make(src_dir / f"Café Ñandú (v2){ext}")
    return name, sample, expected


def test_writes_url_safe_name_and_keeps_original(tool, out_dir: Path):
    name, sample, expected = tool
    before = sha256(sample)
    result = run_tool(name, "-o", out_dir, sample)
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in out_dir.iterdir()) == [expected]
    assert sha256(sample) == before


def test_output_mode_follows_umask(tool, out_dir: Path):
    name, sample, expected = tool
    assert run_tool(name, "-o", out_dir, sample).returncode == 0
    mode = stat.S_IMODE((out_dir / expected).stat().st_mode)
    umask = os.umask(0)
    os.umask(umask)
    assert mode == 0o666 & ~umask


def test_never_overwrites(tool, out_dir: Path):
    name, sample, expected = tool
    out_dir.mkdir()
    existing = out_dir / expected
    existing.write_bytes(b"keep me")
    result = run_tool(name, "-o", out_dir, sample)
    assert result.returncode == 1
    assert "output exists" in result.stderr
    assert existing.read_bytes() == b"keep me"


def test_skip_existing(tool, out_dir: Path):
    name, sample, expected = tool
    out_dir.mkdir()
    (out_dir / expected).write_bytes(b"keep me")
    result = run_tool(name, "-o", out_dir, "--skip-existing", sample)
    assert result.returncode == 0, result.stderr
    assert "SKIP" in result.stdout
    assert (out_dir / expected).read_bytes() == b"keep me"


def test_refuses_source_inside_output_folder(tool):
    name, sample, _ = tool
    result = run_tool(name, "-o", sample.parent, sample)
    assert result.returncode == 1
    assert "inside the output folder" in result.stderr


def test_name_clash_is_an_error(tool, src_dir: Path, out_dir: Path):
    name, sample, expected = tool
    twin_dir = src_dir / "twin"
    twin_dir.mkdir()
    twin = twin_dir / sample.name.replace("Café", "cafe")
    twin.write_bytes(sample.read_bytes())
    result = run_tool(name, "-o", out_dir, sample, twin)
    assert result.returncode == 1
    assert "name clash" in result.stderr
    assert [p.name for p in out_dir.iterdir()] == [expected]


def test_dry_run_writes_nothing(tool, out_dir: Path, tmp_path: Path):
    name, sample, _ = tool
    map_file = tmp_path / "map.tsv"
    result = run_tool(name, "-o", out_dir, "--dry-run", "--map", map_file, sample)
    assert result.returncode == 0, result.stderr
    assert not out_dir.exists()
    assert "Dry run" in result.stdout


def test_map_file(tool, out_dir: Path, tmp_path: Path):
    name, sample, expected = tool
    map_file = tmp_path / "map.tsv"
    assert run_tool(name, "-o", out_dir, "--map", map_file, sample).returncode == 0
    assert map_file.read_text().splitlines() == [
        "source\toutput",
        f"{sample.name}\t{expected}",
    ]


def test_folder_input_is_recursive(tool, src_dir: Path, out_dir: Path):
    name, sample, expected = tool
    nested = src_dir / "a" / "b"
    nested.mkdir(parents=True)
    sample.rename(nested / sample.name)
    (src_dir / ".hidden").write_text("ignored")
    result = run_tool(name, "-o", out_dir, src_dir)
    assert result.returncode == 0, result.stderr
    assert [p.name for p in out_dir.iterdir()] == [expected]


def test_no_temp_files_left(tool, out_dir: Path):
    name, sample, _ = tool
    assert run_tool(name, "-o", out_dir, sample).returncode == 0
    assert not [p for p in out_dir.iterdir() if p.name.startswith(".")]


@pytest.mark.parametrize("args", [[], ["--no-such-option", "x"]])
@pytest.mark.parametrize("name", IDS)
def test_usage_errors_exit_2(name: str, args: list[str]):
    assert run_tool(name, *args).returncode == 2


@pytest.mark.parametrize("name", IDS)
def test_missing_file_fails(name: str, out_dir: Path):
    result = run_tool(name, "-o", out_dir, out_dir.parent / "nope.xyz")
    assert result.returncode == 1
    assert "FAILED" in result.stderr
