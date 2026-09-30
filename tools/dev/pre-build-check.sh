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

# planning/ is deliberately excluded — it's the frozen pre-build
# discussion archive (see design/README.md), not actively maintained
# content. design/ is the active equivalent and does get linted.
run_check "pymarkdown" \
    poetry run pymarkdown --config .pymarkdown scan README.md CLAUDE.md design/ docs/

# --- Checks below are not wired up yet — no site content/templates
# exist to check yet (Phase 1 scaffolding only). Add each as its
# underlying piece comes online, don't stub a no-op check that would
# give false confidence:
#
#   - HTML validity          (needs Frozen-Flask output to exist)
#   - internal link check    (needs Frozen-Flask output to exist)
#   - color-contrast check   (needs the shared CSS custom-properties file)
#   - readability check      (needs Markdown content to exist)
#   - i18n completeness      (needs config/i18n/*.toml to exist)
#   - Frozen-Flask build     (needs at least one site app to exist)

printf '\n[ALL PASS] Pre-build checks complete (partial — see script comments).\n'
