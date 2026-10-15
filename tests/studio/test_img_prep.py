"""img_prep.sh: format, size, rotation and metadata of the copies."""

from pathlib import Path

from PIL import Image

from .conftest import make_jpeg, run_tool


def metadata(path: Path) -> dict:
    """What a viewer could learn beyond the pixels."""
    with Image.open(path) as im:
        exif = im.getexif()
        return {
            "exif": dict(exif),
            "gps": dict(exif.get_ifd(0x8825)),
            "xmp": im.info.get("xmp"),
            "comment": im.info.get("comment"),
            "text": {k: v for k, v in im.info.items() if k.startswith("date")},
        }


def assert_clean(path: Path) -> None:
    meta = metadata(path)
    assert not meta["exif"], meta
    assert not meta["gps"], meta
    assert not meta["xmp"], meta
    assert not meta["comment"], meta
    assert not meta["text"], meta


def test_big_photo_is_shrunk_and_cleaned(src_dir: Path, out_dir: Path):
    src = make_jpeg(src_dir / "Big.JPG", size=(3000, 2000), quality=95, noise=True)
    result = run_tool("img_prep.sh", "-o", out_dir, src)
    assert result.returncode == 0, result.stderr
    out = out_dir / "big.jpg"
    with Image.open(out) as im:
        assert max(im.size) == 2048
        assert im.info.get("progressive") or im.info.get("progression")
    assert_clean(out)


def test_max_edge_option(src_dir: Path, out_dir: Path):
    src = make_jpeg(src_dir / "photo.jpg", size=(800, 600))
    assert run_tool("img_prep.sh", "-o", out_dir, "-s", "400", src).returncode == 0
    with Image.open(out_dir / "photo.jpg") as im:
        assert im.size == (400, 300)


def test_kept_original_has_no_metadata(src_dir: Path, out_dir: Path):
    """A low-quality JPEG re-saved at 85 grows, so the original pixels are
    kept - but its GPS must still go (the fb-prep.sh leak)."""
    src = make_jpeg(src_dir / "low.jpg", size=(400, 300), quality=40, noise=True)
    result = run_tool("img_prep.sh", "-o", out_dir, src)
    assert result.returncode == 0, result.stderr
    assert "kept original" in result.stdout
    out = out_dir / "low.jpg"
    assert_clean(out)
    with Image.open(src) as a, Image.open(out) as b:
        assert a.tobytes() == b.tobytes()  # lossless: same decoded pixels


def test_exif_rotation_is_applied(src_dir: Path, out_dir: Path):
    src = make_jpeg(src_dir / "turned.jpg", size=(300, 200), orientation=6)
    assert run_tool("img_prep.sh", "-o", out_dir, src).returncode == 0
    out = out_dir / "turned.jpg"
    with Image.open(out) as im:
        assert im.size == (200, 300)
    assert_clean(out)


def test_transparency_becomes_png(src_dir: Path, out_dir: Path):
    Image.new("RGBA", (64, 64), (0, 0, 255, 128)).save(src_dir / "Logo.png")
    assert run_tool("img_prep.sh", "-o", out_dir, src_dir).returncode == 0
    out = out_dir / "logo.png"
    with Image.open(out) as im:
        assert im.mode in ("RGBA", "LA", "P")
    assert_clean(out)


def test_other_formats_become_jpeg(src_dir: Path, out_dir: Path):
    Image.new("RGB", (64, 64), (9, 99, 9)).save(src_dir / "pic.webp")
    Image.new("RGB", (64, 64), (9, 99, 9)).save(src_dir / "scan.tiff")
    assert run_tool("img_prep.sh", "-o", out_dir, src_dir).returncode == 0
    assert sorted(p.name for p in out_dir.iterdir()) == ["pic.jpg", "scan.jpg"]


def test_animated_gif_is_refused(src_dir: Path, out_dir: Path):
    frames = [Image.effect_noise((40, 40), 60).convert("P") for _ in range(3)]
    frames[0].save(src_dir / "anim.gif", save_all=True, append_images=frames[1:])
    result = run_tool("img_prep.sh", "-o", out_dir, src_dir / "anim.gif")
    assert result.returncode == 1
    assert "multi-frame" in result.stderr


def test_unreadable_image_fails(src_dir: Path, out_dir: Path):
    fake = src_dir / "fake.png"
    fake.write_text("not an image")
    result = run_tool("img_prep.sh", "-o", out_dir, fake)
    assert result.returncode == 1
    assert "not an image" in result.stderr
