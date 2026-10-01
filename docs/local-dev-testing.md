# Testing a local build in a browser, from `wingchun`

`ubuvm` (the dev host) is server-only — no GUI, no browser. Viewing a
site's local Frozen-Flask build happens from David's laptop
(`wingchun`), over an SSH local port-forward into `ubuvm`'s nginx.
Confirmed working 2026-10-02.

## One-time setup, on `ubuvm`

1. **Let nginx read the repo.** `/home/dave` is `750` (no access for
   other users), and nginx's worker runs as `www-data` — without group
   access, every request 404s no matter what's actually on disk.

   ```bash
   sudo usermod -aG dave www-data
   sudo systemctl restart nginx
   ```

   Must be `restart`, not `reload` — group membership is only re-read
   when the worker process starts, not on a config reload.

2. **Generate the per-site dev vhosts** (also re-run this any time
   `tools/dev/nginx-site.conf.template` changes — it already has twice,
   adding the `/media/` location and the `50x` error page):

   ```bash
   bash tools/dev/setup-local-nginx.sh
   ```

   This needs your interactive sudo password, so it's not something
   Claude can run unattended — same reason it's a separate manual step
   here.

## One-time setup, on `wingchun`

1. **Add the dev domains to `/etc/hosts`**, pointed at `127.0.0.1` (this
   is `wingchun`'s own hosts file, resolving to itself — the actual
   traffic reaches `ubuvm` through the SSH tunnel in the next step, not
   through DNS):

   ```text
   127.0.0.1 taiji.web-sites.test
   127.0.0.1 spain.web-sites.test
   127.0.0.1 comunidad.web-sites.test
   127.0.0.1 movement.web-sites.test
   127.0.0.1 play.web-sites.test
   127.0.0.1 music.web-sites.test
   127.0.0.1 callejerez.web-sites.test
   ```

   This is the same list `tools/dev/setup-local-nginx.sh`'s `SITES`
   array adds to `ubuvm`'s own `/etc/hosts` — add a site there, add it
   here too.

## Every time you want to look at a build

1. **Open the port-forward**, in a spare terminal tab on `wingchun`
   (leave it running for the session):

   ```bash
   ssh -L 8080:localhost:80 ubuvm -N
   ```

   `8080` is unprivileged, so this never needs sudo on `wingchun`. `-N`
   means "just forward, don't open a shell."

2. **Browse**, e.g.:

   ```text
   http://taiji.web-sites.test:8080/en-US/
   http://taiji.web-sites.test:8080/es-ES/taiji-for-balance/
   ```

   nginx matches `server_name` by hostname only, so the `:8080` in the
   `Host` header doesn't break routing.

## Previewing the error pages

`/404.html` shows itself for any URL that doesn't exist, no setup
needed. `/50x.html` is harder — this vhost is static files only, so
there's no real upstream that can actually fail and trigger it. A
dedicated path forces it instead:

```text
http://taiji.web-sites.test:8080/__trigger-500
```

This needs `tools/dev/setup-local-nginx.sh` re-run on `ubuvm` once to
pick up the vhost template change that added it.

## After changing a site's content, templates, or CSS

The browser is only ever looking at `sites/<site>/build/` — nothing
live-reloads. On `ubuvm`, rebuild, then refresh the browser tab:

```bash
poetry run python -m websites.common.freeze taiji
```

## Troubleshooting

- **Everything 404s, including pages that definitely exist in
  `build/`**: almost always the `www-data`/`dave` group step above —
  check `groups www-data` includes `dave`, and that nginx was
  *restarted* (not reloaded) since.
- **Connection refused in the browser**: the SSH port-forward isn't
  running, or was closed when the terminal tab closed.
- **Old content still showing**: the freeze step wasn't re-run after
  the change, or the browser cached the page — hard refresh.
