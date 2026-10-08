#!/usr/bin/env bash
# Fast diagnosis for "ssh web-sites-droplet" hanging/timing out: checks
# whether it's the known cause — the DO Cloud Firewall's SSH rule pinned
# to a stale developer IP — before you go digging further.
#
# Reads the local tofu state directly, so no DIGITALOCEAN_TOKEN needed.
#
#   bash tools/ops/check-ip-drift.sh         # diagnose only
#   bash tools/ops/check-ip-drift.sh --fix   # also repair (deploy.sh does this)
#
# Why it happens: DIGI (the home ISP) hands out dynamic residential IPs
# that change without notice - seen 2026-10-08, same location, no VPN.
#
# --fix runs a tofu plan, and applies it ONLY if the sole change is
# digitalocean_firewall.web_sites (the SSH rule's source IP). Any other
# planned change - droplet, reserved IP, alias file - aborts with a
# pointer to provision.sh, so a routine deploy can never quietly
# rebuild infrastructure. Needs ~/.config/sask/infra.env for the fix.
#
# Exit codes: 0 rule matches (or was fixed), 1 drift not fixed,
# 2 couldn't determine (state or IP lookup unavailable).

set -euo pipefail

FIX=0
[[ "${1:-}" == "--fix" ]] && FIX=1

cd "$(dirname "$0")/../.."

STATE_FILE="infra/tofu/terraform.tfstate"
if [[ ! -f "$STATE_FILE" ]]; then
    printf '[FAIL] %s not found — run from a dev host with tofu state present.\n' "$STATE_FILE" >&2
    exit 2
fi

ALLOWED_IP=$(jq -r '
    .resources[]
    | select(.type == "digitalocean_firewall" and .name == "web_sites")
    | .instances[0].attributes.inbound_rule[]
    | select(.port_range == "22")
    | .source_addresses[0] // empty
' "$STATE_FILE")
ALLOWED_IP="${ALLOWED_IP%%/*}"

if [[ -z "$ALLOWED_IP" ]]; then
    printf '[FAIL] Could not find the port-22 inbound rule in %s.\n' "$STATE_FILE" >&2
    exit 2
fi

CURRENT_IP=$(curl -s --max-time 5 https://api.ipify.org || true)
if [[ -z "$CURRENT_IP" ]]; then
    printf '[WARN] Could not reach api.ipify.org to determine your current IP.\n' >&2
    exit 2
fi

if [[ "$ALLOWED_IP" == "$CURRENT_IP" ]]; then
    printf '[OK] Firewall SSH rule already allows your current IP (%s).\n' "$CURRENT_IP"
    printf '     If ssh web-sites-droplet still times out, look elsewhere (droplet\n'
    printf '     down, sshd stopped, etc.) — the DO web console is the fallback.\n'
    exit 0
fi

printf '[DRIFT] Firewall SSH rule is stale — this is almost certainly why ssh web-sites-droplet times out.\n' >&2
printf '        Firewall currently allows: %s\n' "$ALLOWED_IP" >&2
printf '        Your current public IP is: %s\n' "$CURRENT_IP" >&2

if [[ "$FIX" != 1 ]]; then
    printf '\n        Fix: bash tools/ops/check-ip-drift.sh --fix   (or provision.sh)\n' >&2
    exit 1
fi

INFRA_ENV="$HOME/.config/sask/infra.env"
PLAN="$(mktemp)"
trap 'rm -f "$PLAN"' EXIT
(
    cd infra/tofu
    set -a
    # shellcheck source=/dev/null
    . "$INFRA_ENV"
    set +a
    tofu init -input=false >/dev/null
    tofu plan -input=false -out="$PLAN" >/dev/null
    CHANGES=$(tofu show -json "$PLAN" | jq -r '
        [.resource_changes[]?
         | select(.change.actions != ["no-op"] and .change.actions != ["read"])
         | .address] | join(" ")')
    if [[ "$CHANGES" != "digitalocean_firewall.web_sites" ]]; then
        printf '[FAIL] Refusing to auto-apply: the plan changes more than the firewall:\n' >&2
        printf '         %s\n' "${CHANGES:-(nothing - state may be out of date)}" >&2
        printf '       Review it with: bash tools/ops/provision.sh\n' >&2
        exit 1
    fi
    tofu apply -input=false "$PLAN" >/dev/null
)
printf '[FIXED] Firewall SSH rule now allows %s (was %s).\n' "$CURRENT_IP" "$ALLOWED_IP"
exit 0
