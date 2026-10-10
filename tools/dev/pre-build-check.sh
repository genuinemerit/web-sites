#!/usr/bin/env bash
# tools/dev/pre-build-check.sh — checks before any build, push, or deploy.
# Every check must exit 0. Mirrors sask's tools/dev/pre-commit-check.sh
# pattern (run_check helper, stop-on-first-failure), scaled to what a
# static-site project actually needs — see planning/architecture.md's
# Testing section and CLAUDE.md for the full rationale.

set -uo pipefail

cd "$(dirname "$0")/../.." || exit 1

run_check() {
    local label="$1"
    shift
    printf '\n[CHECK] %s\n' "$label"
    if ! "$@"; then
        printf '\n[FAIL]  %s — fix the issues above, then re-run.\n' "$label" >&2
        exit 1
    fi
    printf '[PASS]  %s\n' "$label"
}

run_check "ruff lint" \
    poetry run ruff check src/ tools/

run_check "ruff format" \
    poetry run ruff format --check src/ tools/

run_check "shellcheck" \
    shellcheck -S warning tools/*/*.sh

# planning/ and design/ are both excluded — David's call 2026-09-30,
# "more noise than we need for this project." Both are discussion/
# decision-record docs, not user-facing content; only README.md,
# CLAUDE.md, and docs/ (the actual pandoc guides/changelog output) get
# linted.
run_check "pymarkdown" \
    poetry run pymarkdown --config .pymarkdown scan README.md CLAUDE.md docs/

# --- Site checks: i18n, then the build itself, then checks over the
# build output. Order matters - the HTML/link/contrast checks read
# sites/*/build/, so the build must run (and pass) first.

# Every src/websites/<site>/ package (with an __init__.py) except
# common/ is a site - same rule as validate_i18n.py.
SITES=()
for pkg in src/websites/*/; do
    [[ -f "$pkg/__init__.py" ]] || continue
    pkg="$(basename "$pkg")"
    [[ "$pkg" == "common" ]] && continue
    SITES+=("$pkg")
done

# Content catalogs edited by hand - checked before anything is built.
run_check "music catalog" \
    poetry run python -m websites.music.catalog

run_check "i18n completeness" \
    poetry run python tools/dev/validate_i18n.py

build_sites() {
    local site
    for site in "${SITES[@]}"; do
        printf '  freezing %s\n' "$site"
        poetry run python -m websites.common.freeze "$site" || return 1
    done
}
# A real check, not just a build step: Frozen-Flask fails on template
# errors, missing content files, and unresolvable url_for() calls.
run_check "Frozen-Flask build (${SITES[*]})" build_sites

# W3C Nu HTML Checker - install/update with tools/dev/install-vnu.sh
# (no sudo; lands in ~/.local/bin/vnu).
VNU="${VNU:-$HOME/.local/bin/vnu}"
check_html() {
    if [[ ! -x "$VNU" ]]; then
        printf 'vnu not found at %s - run: bash tools/dev/install-vnu.sh\n' "$VNU" >&2
        return 1
    fi
    local build_dirs=()
    local site
    for site in "${SITES[@]}"; do
        build_dirs+=("sites/$site/build")
    done
    # The CSS checker predates scroll-driven animations: it rejects the
    # real, shipping properties animation-timeline/animation-range (used
    # inside @supports by comunidad's openmic.css). Filter exactly those
    # two messages, nothing broader.
    "$VNU" --errors-only --skip-non-html --also-check-css \
        --filterpattern '.*Property “animation-(timeline|range)” doesn.t exist.*' \
        "${build_dirs[@]}"
}
run_check "HTML/CSS validity (vnu)" check_html

run_check "internal links" \
    python3 tools/dev/check_links.py

run_check "colour contrast (WCAG AA)" \
    python3 tools/dev/check_contrast.py

# The droplet's real nginx templates, rendered locally and served by an
# unprivileged nginx with throwaway certs, then smoke-tested: every
# redirect, header, certificate name and page in ansible/vhosts.yml.
run_check "nginx config + redirects (local)" \
    bash tools/dev/test-nginx-local.sh

# --- Not wired yet: readability scoring (planning/architecture.md's
# Testing section). Deferred deliberately - textstat's formulas are
# English-centric, and every site here is bilingual; worth a proper
# look before it becomes a gate. Tracked in design/tech-debt.md.

printf '\n[ALL PASS] Pre-build checks complete.\n'
