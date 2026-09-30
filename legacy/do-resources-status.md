# DigitalOcean resource status

Snapshot as of 2026-09-29, via the DO API (`doctl`, using the token at
`~/.config/sask/infra.env`). This is the account-wide picture — most of it
is out of scope for this project but recorded here for context per David's
request, since understanding the overall DO layout matters even where the
individual resource belongs to a different project.

## Account

David Stitt (`david.stitt@pm.me`), team "Genuine Merit", 25-droplet limit.

## Droplets (2 total)

| Name | Public IPv4 | Region | Status | Memory | VCPUs | Disk | Project |
|---|---|---|---|---|---|---|---|
| `gmerit-nyc2` | 162.243.111.56 | nyc2 | active | 2GB | 1 | 70GB | **This project** — legacy static sites, migration target. |
| `sask-droplet` | 104.248.22.105 | fra1 | active | 1GB | 1 | 25GB | `sask` — active, operational, out of scope here. |

## Domains (5 total, all on DO nameservers)

| Domain | In use by | Live subdomains |
|---|---|---|
| `davidstitt.net` | This project + `sask` | `music` → `gmerit-nyc2` (this project). `sask` → `46.101.68.21` — confirmed by David 2026-09-30 this is `sask`'s **active, operational** deployment (a different droplet than `sask-droplet`'s current IP; not a mistake, not this project's concern — any change happens inside `sask`). |
| `genuinemerit.com` | This project | `taiji`, `sandwichopenmic`, `qigong` → `gmerit-nyc2`, all live. |
| `genuinemerit.org` | This project | `sfp` → `gmerit-nyc2`, live. `admin`/`auth` removed 2026-09-29 (confirmed aspirational/unused). |
| `genuinemerit.net` | This project (formerly) | Now empty — only NS/SOA/A boilerplate. `mint` CNAME removed 2026-09-30 (site decommissioned). |
| `genuinemerit.info` | Undecided | Now empty — only NS/SOA/A boilerplate. `story`/`wiki`/`docs` CNAMEs removed 2026-09-30, confirmed aspirational/unused. Whether this domain continues to be used at all is deferred — David's call, not yet made. |

## Full DNS record detail (as of 2026-09-30, post-cleanup)

Every domain carries the same DO-managed boilerplate (`SOA @`, 3× `NS @` →
`ns1/ns2/ns3.digitalocean.com`) plus an `A @` record pointing at
`162.243.111.56` (`gmerit-nyc2`) — omitted from the tables below to avoid
repeating it 5 times; only the domain-specific records are listed.

**`davidstitt.net`**

| Type | Name | Data | TTL |
|---|---|---|---|
| CNAME | `music` | `@` | 43200 |
| A | `sask` | `46.101.68.21` | 300 |

**`genuinemerit.com`**

| Type | Name | Data | TTL |
|---|---|---|---|
| CNAME | `taiji` | `@` | 43200 |
| CNAME | `sandwichopenmic` | `@` | 43200 |
| CNAME | `qigong` | `@` | 43200 |

**`genuinemerit.org`**

| Type | Name | Data | TTL |
|---|---|---|---|
| CNAME | `sfp` | `@` | 43200 |

**`genuinemerit.net`** — no domain-specific records remaining.

**`genuinemerit.info`** — no domain-specific records remaining.

All CNAMEs point at `@` (i.e. resolve through the domain's own `A` record)
rather than being independent A/AAAA records — consistent, simple setup,
nothing irregular about the pattern itself.

## Still open (not resolved this session)

- **`genuinemerit.info`'s future** — David said he'll decide later whether
  to keep supporting this domain at all. No action needed until he does.
- **`sfp/docs/cool_scripts.html` vs. `sfp/cool_scripts.html`** — two
  different files with the same name; see `content-inventory.md`.
- **`sfp/saskan/` asset tree** — very likely dead weight from the retired
  `saskan-app-alt` prototype, not the live `sask` app; see
  `content-inventory.md` for the evidence. Not removed, needs an explicit
  answer.
