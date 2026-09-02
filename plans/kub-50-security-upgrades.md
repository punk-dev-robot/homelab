# KUB-50: Gateway VPS security upgrades — CrowdSec + Authentik

## Context

Internet-facing gateway VPS (`homelab-arm`, OCI uk-london-1, ARM64) runs CrowdSec **v1.6.8** (15 months stale, via unpinned `latest-debian` tag) and Authentik **2025.10.1** (train out of security support — CVE-2026-49448, CVE-2026-47201 unpatched). Ticket: Linear KUB-50 (High). Research brief: `docs/research/kub-50-upgrade-breaking-changes.md`.

Owner decisions: sequential execution (CrowdSec first, then Authentik train-by-train), outage acceptable, app-level backups mandatory. Oracle boot-volume backup confirm in progress (owner, OCI console) — informative, not a blocker.

> [!NOTE]
> Two ticket premises contradicted by research: `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` was never made required (defaults cover pangolin net 172.18.0.0/16 ⊂ 172.16.0.0/12), and PG 16 needs no upgrade (2026.8 supports PG 14–18). Neither change will be made.

### Pre-flight results (verified live over ssh, all green)

| Check | Result |
|---|---|
| CrowdSec acquis datasources | apache2/authentik/nginx/syslog/traefik only — no `http`/`k8s-audit` → the two GHSAs **don't apply**; upgrade is hygiene |
| `/var/lib/crowdsec/data` volume (1.7.0 hard req) | ✅ `pangolin_crowdsec_db` mounted |
| `/etc/crowdsec` persistence | ✅ bind mount `/opt/docker/compose/crowdsec/config/crowdsec` |
| `CROWDSEC_CONTAINER_ENV` (removed 1.7.4) | ✅ unused |
| Duplicate Authentik group names (2025.12 DB migration) | ✅ none |
| Traefik rules special-casing `/media` (2025.12 `/files` change) | ✅ none |
| Disk | ⚠️ 80% full (9.1G free) — prune between image pulls |
| arm64 images for all target tags | ✅ verified via registry manifests |

## Approach

Two phases, strictly sequential, ansible-only for gateway changes (repo rule), backup + verification gate between every step. Rollback is app-level (image repin + pg_dump/config restore) — does not depend on Oracle boot-volume backups.

## Files to modify

| File | Change |
|---|---|
| `ansible/files/gateway-vps/pangolin/pangolin.yml:65` | `crowdsecurity/crowdsec:latest-debian` → `crowdsecurity/crowdsec:v1.8.0-debian` (pin; root cause of staleness) |
| `ansible/files/gateway-vps/pangolin/traefik_static_config/traefik_config.yml:20` | crowdsec-bouncer-traefik-plugin `v1.3.5` → `v1.7.1` (after LAPI verified) |
| `ansible/files/gateway-vps/authentik/compose.yml` | `AUTHENTIK_VERSION` default bump per train (×5); at 2025.12 step change media mount `…/media:/media` → `…/media:/data/media` (server + worker) |
| `ansible/roles/crowdsec_firewall_bouncer/tasks/main.yml` | re-run downloads latest (v0.0.36); force re-download past `creates:` guards (delete `/tmp` artifact or add force) |

## Reuse

- Deploy: `ansible/deploy_vps.yml` (existing gateway playbook)
- Tests: `ansible/tests/suites/gateway_vps_test_suite.yml` (full + `--tags smoke`)
- Bouncer role: `ansible/roles/crowdsec_firewall_bouncer/` (existing install path)
- Access: ssh `ubuntu@141.147.93.212` works today (verified); `docs/agent-access.md`

## Steps

### Phase 0 — prep (non-destructive first, then backups)

- [ ] Owner: confirm OCI boot-volume backup policy + newest backup date (console; parked, non-blocking)
- [ ] Commit research brief `docs/research/kub-50-upgrade-breaking-changes.md`
- [ ] Workstation: `uv tool install ansible` (+ `community.general` collection); verify 1P lookups resolve non-interactively (dry `--check` against gateway)
- [ ] VPS: `docker image prune -f` (disk 80%)
- [ ] Backups → scp off-VPS (workstation, then NAS):
  - [ ] `pg_dump` authentik DB (50MB)
  - [ ] tar `${APP_DATA}/authentik/media` + custom-templates
  - [ ] tar `/opt/docker/compose/crowdsec/config/crowdsec` + `pangolin_crowdsec_db` volume (LAPI creds, bouncer keys, decisions)

### Phase 1 — CrowdSec 1.6.8 → 1.8.0 (single hop, supported)

- [ ] Pin `v1.8.0-debian` in `ansible/files/gateway-vps/pangolin/pangolin.yml`; commit
- [ ] Deploy via `deploy_vps.yml`
- [ ] Verify: `cscli version` = 1.8.0, `cscli lapi status`, `cscli bouncers list` (both bouncers valid + pulling — expect one full decision resync per bouncer, id-cursor change), `cscli hub update && cscli hub upgrade`
- [ ] Run `gateway_vps_test_suite`
- [ ] Then bump bouncers: traefik plugin → v1.7.1, firewall bouncer role re-run → v0.0.36; redeploy; re-verify + smoke tests

> [!WARNING]
> UNVERIFIED (accepted): no upstream LAPI↔bouncer compat matrix. Mitigation is the ordering above — LAPI first, verify bouncers still pull, only then bump them.

### Phase 2 — Authentik 2025.10.1 → 2026.8.1 (5 trains, skips + downgrades unsupported)

Chain: `2025.10.4 → 2025.12.6 → 2026.2.6 → 2026.5.6 → 2026.8.1`

Per train (repeat ×5):
- [ ] `pg_dump` (fresh, off-VPS)
- [ ] Bump `AUTHENTIK_VERSION` default in `ansible/files/gateway-vps/authentik/compose.yml`; commit
- [ ] Deploy via ansible; wait migrations + healthcheck
- [ ] Verify: admin login, karakeep OIDC well-known reachable, worker logs clean, dashboard shows new version
- [ ] `gateway_vps_test_suite --tags smoke`; `docker image prune -f`

Train-specific:
- [ ] **2025.12.6**: media mount → `/data/media` (compose change, same host dir); post-check RBAC migration (`ak-migrated-role--*` roles); verify no custom expression policies touch `Group.parent`
- [ ] **2026.2.6**: pre-check no custom policies use `User.ak_groups`
- [ ] **2026.5.6**: bind default → `[::]`; verify healthcheck `curl localhost:9000` still passes
- [ ] **2026.8.1**: Rust proxy rewrite — verify embedded outpost + every OIDC app
- [ ] Full `gateway_vps_test_suite` after final train
- [ ] Close KUB-50 with resolution comment; update KUB-38 map

Rollback per train: stop stack → restore that train's pg_dump → repin previous tag → up. CrowdSec rollback: repin `v1.6.8-debian`; restore config/volume tar only if LAPI state corrupted.

## Verification

- Per step: service-specific checks above + `ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml` (smoke between trains, full after Phase 1 and after final train)
- End-to-end manual: external login via `https://auth.nobasura.org`, one SSO app (karakeep), one Pangolin-proxied service; `cscli decisions list` showing live decisions; firewall bouncer nftables set populated
- `ansible-lint ansible/` clean before each commit
