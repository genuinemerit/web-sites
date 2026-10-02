#!/usr/bin/env bash
# Deploy (or re-converge) the web-sites droplet via Ansible: platform
# hardening (base), nginx, then every site in ansible/vhosts.yml
# (content, certificates, vhosts - roles/sites). Safe to re-run; sites
# whose DNS doesn't reach the droplet yet are skipped, not failed.
#
#   bash tools/ops/deploy.sh                          # normal
#   bash tools/ops/deploy.sh -e allow_large_media=true  # past the size gate
#   bash tools/ops/deploy.sh -e reissue_certs=true    # after changing hostnames
#
# Extra arguments are passed to ansible-playbook site.yml.
#
# Runs tools/dev/pre-build-check.sh first (which also builds every
# site): nothing is published that hasn't passed every check.
#
# Requires ~/.config/sask/infra.env (outside the repo, shared with sask)
# as a general setup-sanity precondition, even though Ansible itself
# doesn't need the DO token. Bootstraps the `dave` admin account on first
# run only (when it isn't already reachable as dave); every later run
# skips straight to the main site play.

set -euo pipefail

cd "$(dirname "$0")/../.."

bash tools/dev/pre-build-check.sh

INFRA_ENV="$HOME/.config/sask/infra.env"
if [[ ! -f "$INFRA_ENV" ]]; then
    printf '[FAIL] %s not found.\n' "$INFRA_ENV" >&2
    exit 1
fi

# Wait for the droplet's SSH daemon to come up before Ansible connects. A
# freshly created or recreated droplet can take ~60s to be ready.
# Succeeds immediately when the droplet is already running.
#
# Tries both root and dave: a freshly provisioned droplet only has root;
# a droplet where a prior deploy.sh run got as far as the base role's
# sshd hardening (PermitRootLogin no) before failing later only has dave.
_SSH_READY=false
for _I in $(seq 1 24); do
    if ssh -o BatchMode=yes -o ConnectTimeout=5 -o User=root web-sites-droplet true 2>/dev/null \
        || ssh -o BatchMode=yes -o ConnectTimeout=5 web-sites-droplet true 2>/dev/null; then
        _SSH_READY=true
        break
    fi
    printf '[INFO] SSH not ready yet (%d/24); retrying in 5 s...\n' "$_I"
    sleep 5
done
if [[ "$_SSH_READY" != true ]]; then
    printf '[FAIL] Droplet SSH did not become reachable within 2 minutes.\n' >&2
    exit 1
fi

# cd into ansible/ rather than passing -i/--ANSIBLE_CONFIG explicitly:
# Ansible only auto-loads ansible.cfg (and its relative inventory= path)
# from the current directory, not from the playbook's own location.
cd ansible

if ! ssh -o BatchMode=yes -o ConnectTimeout=5 web-sites-droplet true 2>/dev/null; then
    printf '[INFO] dave not yet reachable — running the one-time root bootstrap.\n'
    ansible-playbook bootstrap.yml
fi

ansible-playbook site.yml "$@"
