"""Shared i18n catalog loading. Per-site TOML catalogs
(config/i18n/<site>/<locale>.toml), tag-substitution for short UI
strings - see planning/architecture.md's Internationalization section
and planning/site-build-checklist.md's confirmed per-site structure.

en-US is the completeness floor: every tag any other locale uses must
exist there too. Missing translations degrade gracefully (fall back to
en-US) rather than crash a page - same principle as sask's DD-0022.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FLOOR_LOCALE = "en-US"


def load_catalog(site: str, locale: str) -> dict[str, str]:
    """Load one site's one-locale tag catalog. Raises FileNotFoundError
    if the catalog file doesn't exist - fail fast at startup, not at
    first render."""
    path = REPO_ROOT / "config" / "i18n" / site / f"{locale}.toml"
    with path.open("rb") as f:
        data = tomllib.load(f)
    return data.get("tags", {})


def load_site_catalogs(site: str, locales: list[str]) -> dict[str, dict[str, str]]:
    """Load every locale's catalog for a site, and verify the
    completeness floor: every tag any non-floor locale uses must also
    exist in en-US. Raises ValueError on violation rather than shipping
    a page with a silently-missing floor tag."""
    catalogs = {locale: load_catalog(site, locale) for locale in locales}
    floor = catalogs.get(FLOOR_LOCALE, {})
    for locale, tags in catalogs.items():
        if locale == FLOOR_LOCALE:
            continue
        missing_from_floor = set(tags) - set(floor)
        if missing_from_floor:
            raise ValueError(
                f"{site}/{locale}.toml has tags not present in "
                f"{FLOOR_LOCALE}.toml (the completeness floor): "
                f"{sorted(missing_from_floor)}"
            )
    return catalogs


def translate(catalogs: dict[str, dict[str, str]], locale: str, tag: str) -> str:
    """Resolve one tag for one locale, falling back to the floor locale
    (and then to the tag itself) if missing - graceful degradation, not
    a crash."""
    value = catalogs.get(locale, {}).get(tag)
    if value is not None:
        return value
    floor_value = catalogs.get(FLOOR_LOCALE, {}).get(tag)
    if floor_value is not None:
        return floor_value
    return tag
