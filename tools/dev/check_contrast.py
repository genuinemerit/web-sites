"""WCAG AA colour-contrast check over every built page's colour tokens.

Each page declares its palette as CSS custom properties on :root in its
own <style> block (light), optionally overridden inside
`@media (prefers-color-scheme: dark)` - see sites/_shared/static/
tokens.css for why palettes are per page, not global. This check reads
those tokens from the *built* HTML (sites/*/build/**/*.html), so it sees
exactly what ships, and verifies each text/background pairing in both
schemes:

  --text, --muted, --accent, --accent-hover   (foregrounds)
  on --background and --surface               (backgrounds)

against WCAG 2.x AA for normal text, 4.5:1 - the same formula WebAIM's
checker uses. A pairing is only checked when the page defines both
tokens. --line is decorative (separators marked aria-hidden) and is
not checked.

Convention this enforces: the six tokens above must be literal hex
colours (#rgb or #rrggbb), so contrast is verifiable. A token holding
anything else (color-mix(), a var() reference) is reported as an error
rather than silently skipped.

Known limit, by design: it checks the declared tokens, not the final
composited pixels. Where a page layers text over an image or a
semi-transparent surface (taiji's content page), the real contrast
also depends on that overlay - still a manual review item.

Exit 0 when every pairing passes, 1 otherwise. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SITES_DIR = REPO_ROOT / "sites"

AA_NORMAL_TEXT = 4.5
FOREGROUNDS = ("--text", "--muted", "--accent", "--accent-hover")
BACKGROUNDS = ("--background", "--surface")

_STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_DECL_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_DARK_MEDIA_RE = re.compile(r"prefers-color-scheme\s*:\s*dark")


def _blocks(css: str) -> list[tuple[str, str]]:
    """Split CSS into top-level (prelude, body) pairs by brace matching."""
    blocks: list[tuple[str, str]] = []
    depth = 0
    start = 0
    prelude = ""
    for i, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                prelude = css[start:i].strip()
                body_start = i + 1
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blocks.append((prelude, css[body_start:i]))
                start = i + 1
    return blocks


def _root_tokens(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return (light_tokens, dark_overrides) from :root rules."""
    light: dict[str, str] = {}
    dark: dict[str, str] = {}
    for prelude, body in _blocks(css):
        if prelude == ":root":
            light.update(_DECL_RE.findall(body))
        elif prelude.startswith("@media") and _DARK_MEDIA_RE.search(prelude):
            for inner_prelude, inner_body in _blocks(body):
                if inner_prelude == ":root":
                    dark.update(_DECL_RE.findall(inner_body))
    return light, dark


def _luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    channels = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    lighter, darker = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def check_scheme(label: str, tokens: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for name in FOREGROUNDS + BACKGROUNDS:
        value = tokens.get(name, "").strip()
        if value and not _HEX_RE.match(value):
            errors.append(f"{label}: {name} is {value!r}, not a literal hex colour")
    for fg in FOREGROUNDS:
        for bg in BACKGROUNDS:
            fg_val = tokens.get(fg, "").strip()
            bg_val = tokens.get(bg, "").strip()
            if not (_HEX_RE.match(fg_val) and _HEX_RE.match(bg_val)):
                continue
            ratio = contrast_ratio(fg_val, bg_val)
            if ratio < AA_NORMAL_TEXT:
                errors.append(
                    f"{label}: {fg} {fg_val} on {bg} {bg_val} = "
                    f"{ratio:.2f}:1 (needs {AA_NORMAL_TEXT}:1)"
                )
    return errors


def check_page(page: Path) -> tuple[list[str], int]:
    html = page.read_text(encoding="utf-8")
    css = _COMMENT_RE.sub("", "\n".join(_STYLE_RE.findall(html)))
    light, dark_overrides = _root_tokens(css)
    if not light:
        return [], 0
    rel = page.relative_to(REPO_ROOT)
    errors = check_scheme(f"{rel} [light]", light)
    schemes = 1
    if dark_overrides:
        errors += check_scheme(f"{rel} [dark]", {**light, **dark_overrides})
        schemes = 2
    return errors, schemes


def main() -> int:
    pages = sorted(SITES_DIR.glob("*/build/**/*.html"))
    if not pages:
        print("ERROR: no built pages found - run the build first.")
        return 1
    errors: list[str] = []
    checked = 0
    for page in pages:
        page_errors, schemes = check_page(page)
        errors.extend(f"ERROR: {e}" for e in page_errors)
        checked += schemes
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"All colour pairings meet WCAG AA ({checked} page/scheme palettes).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
