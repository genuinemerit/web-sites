#!/usr/bin/env bash
# Test the droplet's nginx configuration locally, before deploying it.
#
#   bash tools/dev/test-nginx-local.sh
#
# Renders the real Ansible templates (ansible/render-local.yml) into a
# scratch directory, issues throwaway test certificates from a
# throwaway local CA, runs nginx unprivileged on ports 18080/18443 over
# the current sites/*/build output, then runs tools/ops/smoke_test.py -
# the same checks used after a real deploy - against it. Needs the
# builds to exist (pre-build-check.sh runs this after building). No
# sudo, nothing left behind.

set -euo pipefail

cd "$(dirname "$0")/../.."
REPO="$PWD"
OUT="$(mktemp -d)"
NGINX=(nginx -p "$OUT" -c "$OUT/nginx.conf" -e "$OUT/logs/error.log")

cleanup() {
    if [[ -f "$OUT/nginx.pid" ]]; then
        "${NGINX[@]}" -s stop 2>/dev/null || true
        sleep 0.5
    fi
    rm -rf "$OUT"
}
trap cleanup EXIT

# 1. Render. Ansible output goes to a log, shown only on failure
#    (ansible-playbook can refuse to run on a non-blocking pipe).
if ! (cd ansible && ansible-playbook render-local.yml -i localhost, -c local \
        -e "out=$OUT" >"$OUT.render.log" 2>&1); then
    cat "$OUT.render.log" >&2
    rm -f "$OUT.render.log"
    exit 1
fi
rm -f "$OUT.render.log"

# 2. Content and certificates, one line per site from vhosts.yml:
#    name source media-or-dash hostname...
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
    -keyout "$OUT/ca.key" -out "$OUT/ca.pem" -days 30 \
    -subj "/CN=web-sites local test CA" 2>/dev/null

python3 - "$REPO/ansible/vhosts.yml" <<'PY' >"$OUT/sites.txt"
import sys, yaml
for v in yaml.safe_load(open(sys.argv[1]))["vhosts"]:
    names = [v["canonical"], *(v.get("aliases") or [])]
    print(v["name"], v["source"], v.get("media", "-"), *names)
PY

while read -r name source media names; do
    mkdir -p "$OUT/www/$name" "$OUT/live/$name"
    ln -s "$REPO/$source" "$OUT/www/$name/build"
    [[ "$media" != "-" ]] && ln -s "$REPO/$media" "$OUT/www/$name/media"
    san=""
    for host in $names; do san+="DNS:$host,"; done
    openssl req -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
        -keyout "$OUT/live/$name/privkey.pem" -out "$OUT/live/$name/req.csr" \
        -subj "/CN=$name" 2>/dev/null
    openssl x509 -req -in "$OUT/live/$name/req.csr" -CA "$OUT/ca.pem" \
        -CAkey "$OUT/ca.key" -days 30 -out "$OUT/live/$name/fullchain.pem" \
        -extfile <(printf 'subjectAltName=%s' "${san%,}") 2>/dev/null
done <"$OUT/sites.txt"

# The default page (no certificate - plain-HTTP default server only).
default_source="$(python3 -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))["default_site"]["source"])' \
    "$REPO/ansible/vhosts.yml")"
mkdir -p "$OUT/www/default"
ln -s "$REPO/$default_source" "$OUT/www/default/build"

# 3. Validate, start, test.
"${NGINX[@]}" -t -q
"${NGINX[@]}"
python3 tools/ops/smoke_test.py --resolve 127.0.0.1 --http-port 18080 \
    --https-port 18443 --cafile "$OUT/ca.pem" --min-days 21
