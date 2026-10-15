"""pdf_prep.sh: size, metadata, linearization and refusals."""

import subprocess
from pathlib import Path

from .conftest import (
    make_image_pdf,
    make_pdf,
    pdf_has_xmp,
    pdf_info,
    pdf_is_linearized,
    run_tool,
)


def run_ok(*args) -> subprocess.CompletedProcess:
    result = run_tool("pdf_prep.sh", *args)
    assert result.returncode == 0, result.stderr
    return result


def test_metadata_removed_and_linearized(src_dir: Path, out_dir: Path):
    src = make_pdf(src_dir / "Doc.pdf", pages=2)
    assert pdf_info(src).get("/Author")
    run_ok("-o", out_dir, src)
    out = out_dir / "doc.pdf"
    assert set(pdf_info(out)) <= {"/ModDate"}
    assert not pdf_has_xmp(out)
    assert pdf_is_linearized(out)
    subprocess.run(["qpdf", "--check", str(out)], check=True, capture_output=True)


def test_keep_info_keeps_only_the_title(src_dir: Path, out_dir: Path):
    src = make_pdf(src_dir / "doc.pdf")
    run_ok("-o", out_dir, "--keep-info", src)
    assert pdf_info(out_dir / "doc.pdf") == {"/Title": "u:Sample Title"}


def test_keep_info_lossless_keeps_only_the_title(src_dir: Path, out_dir: Path):
    src = make_pdf(src_dir / "doc.pdf")
    run_ok("-o", out_dir, "--keep-info", "--lossless", src)
    assert pdf_info(out_dir / "doc.pdf") == {"/Title": "u:Sample Title"}


def test_image_pdf_shrinks(src_dir: Path, out_dir: Path, tmp_path: Path):
    src = make_image_pdf(src_dir / "photo.pdf", tmp_path)
    result = run_ok("-o", out_dir, src)
    assert "REWRITE" in result.stdout
    assert (out_dir / "photo.pdf").stat().st_size < src.stat().st_size / 2


def test_lossless_skips_ghostscript(src_dir: Path, out_dir: Path, tmp_path: Path):
    src = make_image_pdf(src_dir / "photo.pdf", tmp_path)
    result = run_ok("-o", out_dir, "--lossless", src)
    assert "CLEAN" in result.stdout
    assert (out_dir / "photo.pdf").stat().st_size > src.stat().st_size / 2


def test_bad_preset_is_a_usage_error(src_dir: Path, out_dir: Path):
    src = make_pdf(src_dir / "doc.pdf")
    assert (
        run_tool("pdf_prep.sh", "-o", out_dir, "--preset", "huge", src).returncode == 2
    )


def test_password_protected_is_refused(src_dir: Path, out_dir: Path):
    plain = make_pdf(src_dir / "plain.pdf")
    locked = src_dir / "locked.pdf"
    subprocess.run(
        ["qpdf", "--encrypt", "user", "owner", "256", "--", str(plain), str(locked)],
        check=True,
    )
    result = run_tool("pdf_prep.sh", "-o", out_dir, locked)
    assert result.returncode == 1
    assert "password-protected" in result.stderr


def test_not_a_pdf_fails(src_dir: Path, out_dir: Path):
    fake = src_dir / "fake.pdf"
    fake.write_text("hello")
    result = run_tool("pdf_prep.sh", "-o", out_dir, fake)
    assert result.returncode == 1
    assert "not a PDF" in result.stderr
