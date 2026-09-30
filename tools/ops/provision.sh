#!/usr/bin/env bash
# Provision (or re-converge) the web-sites droplet via OpenTofu.
#
# Run from the dev host (ubuvm), repo root:
#
#   bash tools/ops/provision.sh        # interactive: tofu prompts before applying
#   bash tools/ops/provision.sh -y     # non-interactive: tofu -auto-approve
#
# Requires ~/.config/sask/infra.env (outside the repo, shared with sask -
# confirmed in planning/architecture.md) exporting DIGITALOCEAN_TOKEN.

set -euo pipefail

cd "$(dirname "$0")/../.."

INFRA_ENV="$HOME/.config/sask/infra.env"
if [[ ! -f "$INFRA_ENV" ]]; then
    printf '[FAIL] %s not found.\n' "$INFRA_ENV" >&2
    printf '       This project shares sask'"'"'s secrets cache - see sask/secrets/infra.env.example.\n' >&2
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "$INFRA_ENV"
set +a

if [[ -z "${DIGITALOCEAN_TOKEN:-}" ]]; then
    printf '[FAIL] DIGITALOCEAN_TOKEN is not set after sourcing %s.\n' "$INFRA_ENV" >&2
    exit 1
fi

AUTO_APPROVE=()
if [[ "${1:-}" == "-y" ]]; then
    AUTO_APPROVE=("-auto-approve")
fi

cd infra/tofu
tofu init -upgrade
tofu apply "${AUTO_APPROVE[@]}"
