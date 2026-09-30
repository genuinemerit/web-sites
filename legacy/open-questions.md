# Open questions for David

Surfaced by the 2026-09-29 droplet review (see `inventory.md`). Nothing here
blocks continuing the earlier tech-stack conversation, but these need
answers before scaffolding/migration planning gets concrete.

1. **`windfallhouse.genuinemerit.com`** — config exists, not enabled, no
   content dir, no cert. Was this ever live, or is it a placeholder for a
   site not yet built? Migrate, rebuild fresh, or drop?

A: Drop. An abandoned project.

2. **`mint.genuinemerit.net`** — confirmed retired per your note. OK to
   treat as fully decommissioned (not just "not migrated" but actively
   disable `mint.service`/`postgresql.service` on the *legacy* droplet, and
   not carry the DB/app forward at all), or do you want the Postgres data
   exported/kept somewhere first before anything gets torn down?

A: Fully decommission. An abandoned project. Lessons learned already applied to newer projects like `sask`.

3. **`old_sfp.conf`** — looks like a dead predecessor of `sfp.conf` (same
   domain, same content root, not enabled). OK to just not carry forward?

A: Correct, dead predecessor. Drop.

4. **Three different domains** (`davidstitt.net`, `genuinemerit.com`,
   `genuinemerit.org`) across the 5 live sites — confirms these aren't one
   umbrella property. Do you manage all three registrations yourself (same
   registrar or different), and do you have DNS access sorted for all three,
   or is that part of what needs setting up for the new droplet?

A: These are all my domains. And there are two more. We need to review the domain usage and design as a separate step. All use Digital Ocean nameservers and most have specified sub-domains. Want to review how all of that is being handled. The only web site that really needs to maintain its current domain is the taiji one.

5. **OS version drift** — droplet is Ubuntu 24.10 (interim release, not
   LTS), not 24.04 LTS as assumed in the original project summary. Worth
   knowing if that was intentional (e.g. wanted a newer kernel/package at
   the time) or just drift, mostly as a data point for planning the new
   droplet's OS choice — 26.04 LTS was the original stated target.

A: Just my mistake. The goal is to move to a new droplet using the latest fully supported long-term Ubuntu.

6. **`music`/`openmic`/`taiji` are multi-GB each** (video/photo galleries).
   Worth flagging now: do these need to migrate byte-for-byte, or is this a
   chance to reconsider hosting large media (e.g. object storage / CDN
   instead of the droplet's own disk) as part of the "improve" goal? Not
   urgent, just don't want to assume "copy as-is" without asking.

A: Yes, good point. We will want to review the large media files to see which ones to carry forward, which to archive or abandon. May want to consider CDN, but all things considered, a minimally-sized droplet has been sufficient so far.

