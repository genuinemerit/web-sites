# infra/tofu

OpenTofu IaC for the `web-sites` DigitalOcean droplet. Adapted from
`sask/infra/tofu/` (read in full before drafting this, not copied blind
— see `planning/roadmap.md`'s Phase 1f notes for what changed and why).

## What this creates

Droplet, a reserved IP (stable across destroy/recreate), a firewall
(SSH restricted to the current developer IP, 80/443 open), and a local
SSH config snippet — referencing a **dedicated** DO SSH key
(`ubuvm_ws`, local `~/.ssh/ws_ed25519`) generated specifically for this
project (confirmed 2026-10-01; an earlier choice to reuse the
`genuinemerit` key was reconsidered).

## What this deliberately does NOT do yet: DNS

Unlike `sask`'s equivalent (which wires a DNS record into the same
`apply`), this config creates **no DNS records**. The production domains
(`davidstitt.net`, `genuinemerit.com/.org/.net`) currently point at the
**legacy** droplet, serving real live sites — this infrastructure pass
proves the droplet/SSH/firewall pipeline works, it does not touch
anything a visitor could notice. Pointing a domain at this droplet's
`reserved_ip` output happens later, as its own deliberate, reviewed step,
once an actual site (`taiji` first, per `planning/roadmap.md`) has real
content ready to go live.

## Usage

See `tools/ops/{provision,destroy,recreate-droplet,check-ip-drift}.sh`
— same usage pattern as `sask`'s equivalents. Requires
`~/.config/sask/infra.env` (shared secrets cache, confirmed in
`planning/architecture.md`) exporting `DIGITALOCEAN_TOKEN`.
