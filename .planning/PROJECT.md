# Homelab Public Release Prep

## What This Is

Prepare the homelab infrastructure repo for public release as both a portfolio piece and community resource. The repo contains Ansible-managed infrastructure with 27+ Docker services across a gateway VPS and 3 homelab VMs, managed via 1Password for secrets. Before going public: scrub secrets, review PII, clean stale content, consolidate memory files, and squash to a single clean commit.

## Core Value

No secrets or personally identifiable information leak when the repository goes public.

## Requirements

### Validated

<!-- Inferred from existing codebase — these are already working. -->

- ✓ Ansible-driven infrastructure-as-code across hybrid homelab + gateway VPS — existing
- ✓ Docker Compose service deployment organized into logical stacks — existing
- ✓ Secret management via 1Password lookup integration — existing
- ✓ Comprehensive test suites (gateway VPS + homelab VMs) — existing
- ✓ CrowdSec protection on gateway — existing
- ✓ Traefik + Pangolin external routing — existing
- ✓ Caddy internal proxy for .lab.nobasura.org — existing

### Active

- [ ] All hardcoded secrets replaced with 1Password lookups
- [ ] PII audit completed and remediation agreed
- [ ] Stale root-level files removed or relocated
- [ ] Memory files consolidated, duplicates merged, sessions archived
- [ ] .gitignore updated for public release (.planning/, etc.)
- [ ] Public README.md written
- [ ] Git history squashed to single clean commit
- [ ] Final automated secrets + PII scan passes clean

### Out of Scope

- Domain anonymization (nobasura.org) — public-facing domain, intentional to keep
- Internal IP anonymization (10.x.x.x, .lan) — private ranges, no risk
- Service email anonymization (auth@, letsencrypt@, no-reply@) — functional, tied to domain
- Refactoring ansible code — this is cleanup only, not improvement
- Migrating to different secret management — 1Password pattern stays

## Context

**Secrets audit findings (4 hardcoded values):**
- `ansible/files/gateway-vps/pangolin/config/config.yml.j2:26` — Pangolin session secret in plaintext
- `ansible/files/gateway-vps/pangolin/beszel-agent.yml:15` — Beszel agent token in plaintext
- `ansible/files/apps-vm/tools/firecrawl.yml:120` — Default postgres password
- `ansible/files/obs-vm/tick/influxdb2.yml:13-14` — Commented-out credentials

**PII findings (needs discussion):**
- Public VPS IP (`141.147.93.212`) in inventory + docs
- Home IP (`185.24.123.11`) in 10+ files (inventory, traefik rules, crowdsec whitelists, memory)
- Personal emails: kuba@gajmail.com, gaj.borys@gmail.com, punkdevrobot@pm.me in inventory/group_vars
- Auto-login email in beszel config
- Personal name "Kuba" in HOMELAB_SERVICES.md title and Proxmox user config

**Stale content:**
- AUTHENTIK_IMPLEMENTATION_STATE.md, KARAKEEP_SSO_SETUP.md at root
- Stray archive/ and research/ directories at root
- .planning/ should be excluded from public commit

**Memory (90+ files):**
- Duplicate tracks: 7 Authentik, 6 CrowdSec, 4 Media-VM, 3 VPS recovery
- Overlapping folders: memory/architecture/ vs memory/network-info/architecture/
- Outdated README.md
- Approach: consolidate + archive, Kuba reviews

**Git strategy:** Full squash to single commit eliminates history risk. Rotate exposed secrets after public push.

## Constraints

- **Secrets pattern**: Must use 1Password lookups (existing pattern) — no env files or vault files
- **PII approach**: Generate report for Kuba to review before any changes
- **Memory cleanup**: Kuba reviews consolidation before commit
- **Git**: Full squash, no history preserved

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep nobasura.org domain | Public-facing, intentional showcase | — Pending |
| Keep internal IPs (10.x.x.x) | RFC1918 private ranges, no risk | — Pending |
| Full git squash | Eliminates any secrets in history | — Pending |
| 1Password for secrets | Consistent with existing codebase pattern | — Pending |
| PII via report + discussion | User wants control over what gets anonymized | — Pending |

---
*Last updated: 2026-02-09 after initialization*
