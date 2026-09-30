#!/usr/bin/env bash
# tools/dev/setup-local-nginx.sh — generate and enable local dev nginx
# vhosts for every site, from tools/dev/nginx-site.conf.template.
#
# Build-output convention: each site's Frozen-Flask output lands at
# sites/<site>/build/ (already anticipated in .gitignore) — this script
# points each vhost's root there. Server-name-based routing
# (<site>.web-sites.test), not port-based, to mirror prod's actual
# routing behavior (see planning/architecture.md's Dev environment
# section).
#
# Idempotent and extendable: re-run any time, including after adding a
# new site to SITES below — existing /etc/hosts entries and vhost files
# are only added if missing, never duplicated.
#
# NOTE: needs sudo (writes /etc/nginx/, /etc/hosts) — sudo on ubuvm
# requires interactive password auth, so Claude cannot run this
# unattended. David runs it directly.
#
# Usage:
#   bash tools/dev/setup-local-nginx.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TEMPLATE="$REPO_ROOT/tools/dev/nginx-site.conf.template"

# The 7 confirmed properties (planning/target-sites.md). Add a new site
# here when it's ready for local dev serving — everything else in this
# script picks it up automatically.
SITES=(taiji spain comunidad movement play music callejerez)

echo "[1/3] Generating and enabling vhosts"
for site in "${SITES[@]}"; do
    conf="/etc/nginx/sites-available/${site}.web-sites.test.conf"
    # sed needs no sudo (the template is ours to read) - render to a
    # plain variable first, then a single sudo call to write it. Piping
    # two separate `sudo` calls together (the original version of this
    # script) starts both concurrently, which can produce two
    # overlapping password prompts on the same terminal - confusing and
    # error-prone. One sudo call per site, not two.
    rendered="$(sed -e "s|SITE_NAME|${site}|g" -e "s|REPO_ROOT|${REPO_ROOT}|g" "$TEMPLATE")"
    echo "$rendered" | sudo tee "$conf" > /dev/null
    sudo ln -sf "$conf" "/etc/nginx/sites-enabled/$(basename "$conf")"
    mkdir -p "$REPO_ROOT/sites/${site}/build"
    echo "  - ${site}.web-sites.test -> sites/${site}/build"
done

echo "[2/3] /etc/hosts entries"
for site in "${SITES[@]}"; do
    host="${site}.web-sites.test"
    if ! grep -q "[[:space:]]${host}\$" /etc/hosts; then
        echo "127.0.0.1 ${host}" | sudo tee -a /etc/hosts > /dev/null
        echo "  - added ${host}"
    else
        echo "  - ${host} already present, skipped"
    fi
done

echo "[3/3] Testing and reloading nginx"
sudo nginx -t
sudo systemctl reload nginx

echo
echo "[DONE] Try: curl http://taiji.web-sites.test/ (404 expected until"
echo "       taiji's Frozen-Flask build actually exists at"
echo "       sites/taiji/build/)"
