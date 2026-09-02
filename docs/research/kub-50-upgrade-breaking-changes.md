# KUB-50 — Upgrade breaking-changes research: CrowdSec + Authentik

**Scope:** internet-facing gateway VPS, Ubuntu, ARM64/aarch64, docker compose.
**Researched:** from primary sources only (upstream repos, upstream release notes, upstream docs, registry manifests).
**Method note:** version facts come from the GitHub Releases API, the GitHub Security Advisories API, upstream docs source (`website/docs/**` in `goauthentik/authentik`, `crowdsec-docs`), and OCI registry manifest lists. Blog posts were not used.

---

## Question

For each of CrowdSec (installed 1.6.8) and Authentik (installed 2025.10.1): what is the actual latest stable, what is the exact upgrade path, and what breaks along the way for a docker-compose ARM64 deployment behind Traefik?

## One-paragraph answer

Both target versions in the ticket are correct: CrowdSec latest stable is **v1.8.0** (2026-08-31) and Authentik latest stable is **2026.8.1** (2026-09-01), and both publish `linux/arm64` images. CrowdSec can be upgraded in a single hop from 1.6.8 to 1.8.0 — it fixes the two named advisories (GHSA-g2x2-jgfg-pg7g, GHSA-rh69-4vqj-9gj8, both DoS, both `first_patched_version: 1.8.0`, both in *opt-in* datasources this host probably does not run) — but the hop crosses the 1.7.0 hard requirement that `/var/lib/crowdsec/data/` be a mounted volume or the container refuses to start, plus the 1.7.4 removal of `CROWDSEC_CONTAINER_ENV` and the 1.7.7 switch to RE2 as default regexp engine; the LAPI bouncer API stays v1 and upstream designed the 1.8.0 stream-cursor change so existing bouncers get one full decision resync on first pull, so the Traefik plugin and host firewall bouncer should keep working (no upstream compatibility matrix exists — see UNVERIFIED). Authentik must be stepped train-by-train — `2025.10.1 → 2025.10.4 → 2025.12.6 → 2026.2.6 → 2026.5.6 → 2026.8.1` — because downgrades are explicitly unsupported and 2026.8 added tooling that blocks major-version skips; the painful step is 2025.12 (host `./media` must be moved to `./data/media`, files now served from `/files`, and group-name uniqueness is enforced at the DB level so the migration fails loudly on duplicates), followed by the 2026.2 `docker-compose.yml` → `compose.yml` rename and the 2026.5 default listen address change from `0.0.0.0` to `[::]`. PostgreSQL 16 needs no upgrade (2026.8 supports PG 14–18), and `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` was **not** made required by any train in this range — it already existed in 2025.10 with defaults that cover Docker networks.

---

# 1. CrowdSec

## 1.1 Version facts

| Fact | Value | Source |
| --- | --- | --- |
| Installed | 1.6.8 (released 2025-03-25) | https://github.com/crowdsecurity/crowdsec/releases/tag/v1.6.8 |
| Latest stable | **v1.8.0**, published 2026-08-31 | https://github.com/crowdsecurity/crowdsec/releases/tag/v1.8.0 (GitHub Releases API, newest non-prerelease) |
| Ticket claim "1.8.0" | ✅ correct | as above |
| Image tag to pin | `crowdsecurity/crowdsec:v1.8.0-debian` | https://hub.docker.com/r/crowdsecurity/crowdsec/tags |
| arm64 support | ✅ `v1.8.0-debian` = `linux/386`, `linux/amd64`, `linux/arm64`; `v1.8.0` / `v1.8.0-slim` additionally `linux/arm` | Docker Hub tags API for `crowdsecurity/crowdsec` |

Note: the `-debian` variant does **not** ship `linux/arm` (armv7), only arm64 — fine for aarch64.

## 1.2 The two advisories — confirmed

Both were published 2026-08-31 alongside v1.8.0 and are listed in the v1.8.0 release notes "Security Notice" section.

| Advisory | Summary | Severity | CVE | Affected | Fixed in |
| --- | --- | --- | --- | --- | --- |
| [GHSA-g2x2-jgfg-pg7g](https://github.com/crowdsecurity/crowdsec/security/advisories/GHSA-g2x2-jgfg-pg7g) | HTTP acquisition datasource lacks a decompressed body cap and trusts `Content-Length` → memory-exhaustion DoS (OOM kill of the Security Engine) | medium | none assigned | `github.com/crowdsecurity/crowdsec` `>= 0, <= 1.7.8` | **1.8.0** |
| [GHSA-rh69-4vqj-9gj8](https://github.com/crowdsecurity/crowdsec/security/advisories/GHSA-rh69-4vqj-9gj8) | Unbounded request-body read (`io.ReadAll`, no auth, no read timeout) in the kubernetes-audit acquisition webhook → memory-exhaustion DoS | medium | none assigned | `<= 1.7.8` | **1.8.0** |

**Exposure assessment for this host:** both advisories only apply if the respective *acquisition datasource* is configured. The HTTP datasource requires `basic_auth`/`headers`/`mtls` credentials and is opt-in; the k8s-audit datasource is a Kubernetes webhook. Upstream states the HTTP datasource "is not enabled by a default installation." Confirm against `acquis.d/` before treating this as an urgent-exposure upgrade rather than a hygiene upgrade. Corresponding fixes also appear in the v1.8.0 changelog as `acquis(http): Set default max body size and enforce it as well for compressed streams (#4616)` and `k8s-audit: add support for max body size (#4630)`.

## 1.3 Version chain

CrowdSec does **not** require sequential stepping; a single jump 1.6.8 → 1.8.0 is the normal path (no documented upgrade-order constraint in the release notes or docs). The intermediate releases still matter because their breaking changes accumulate:

| Release | Date | Relevance to this deployment |
| --- | --- | --- |
| v1.6.9 | 2025-06-17 | ⚠️ Docker acquisition now requires access to the Docker **events** API endpoint — socket-proxy configs must be updated |
| v1.6.10 | 2025-07-10 | HTTP datasource accepts GET/HEAD health probes; `cscli allowlists check` |
| v1.6.11 | 2025-07-22 | Windows shutdown fix; allowlist normalisation fix |
| **v1.7.0** | 2025-09-01 | 🔴 **Docker: `/var/lib/crowdsec/data/` MUST be a mounted volume or the container refuses to start.** `cscli dashboard` removed. New `cscli setup` service detection. Log processors now push acquisition/parser metrics to LAPI |
| v1.7.1 | 2025-10-15 | Bouncer-name sanitisation when the bouncer IP changes; WAF fixes |
| v1.7.2 / v1.7.3 | 2025-10-21/24 | Packaging only (hub-update systemd timer, deb/rpm) — no docker impact |
| **v1.7.4** | 2025-12-04 | 🔴 **`CROWDSEC_CONTAINER_ENV` removed from the docker entrypoint (#4085)**. New `api.server.disable_usage_metrics_export`; `log_media: syslog` option |
| v1.7.5 / v1.7.6 | 2026-01-22/23 | Refactors, CAPI token reuse fix, allowlist/PAPI fix |
| **v1.7.7** | 2026-03-30 | 🟠 **RE2 becomes the default regexp engine on Linux.** Faster matching, slower compile, higher baseline memory. Fallback: feature flag `re2_disable_grok_support`. Also adds alert `kind` attribute and `cscli allowlist import` |
| **v1.7.8** | 2026-05-11 | 🟠 **Decision stream moves to chunked transfer by default (#4413)** — relevant to bouncers. LAPI enforces max body size for decompression. New cleaner `appsec-config` configuration form |
| **v1.8.0** | 2026-08-31 | Bot-detection/WAF challenge mode, dedicated k8s datasource, expr HTTP helpers. 🔴 **JWT can no longer be passed in the query string (#4554)**. 🟠 **LAPI delta pull now uses a decision-id cursor (#4620)**. Two DoS fixes above |

Sources: each row is the corresponding `https://github.com/crowdsecurity/crowdsec/releases/tag/<tag>` release-notes body.

## 1.4 Config-file migrations

- No release in 1.6.9…1.8.0 documents a mandatory `config.yaml` schema migration. The upgrade is additive: new keys (`api.server.disable_usage_metrics_export` in 1.7.4, feature flags, appsec-config alternative form in 1.7.8) with defaults.
- The one hard config-shape change is deployment-level, not file-level: the **data volume requirement** (1.7.0) and the **removal of `CROWDSEC_CONTAINER_ENV`** (1.7.4).
- `cscli dashboard` removal (1.7.0) only matters if Metabase was in use.
- **UNVERIFIED:** there is no upstream "upgrading from 1.6 to 1.8" migration document in `crowdsecurity/crowdsec-docs` (the docs are versioned as `version-v1.6` / `version-v1.7` / `version-v1.8` with no dedicated upgrade page found). Release notes are the authoritative migration record.

## 1.5 Hub / collection compatibility

- The container runs a hub update/upgrade on start unless `NO_HUB_UPGRADE=true` is set (documented env var in the image README). After upgrading the image, hub items are refreshed automatically on the first boot of the new container.
- Manual equivalent inside the container: `cscli hub update && cscli hub upgrade` (see `cscli hub upgrade` reference, https://docs.crowdsec.net/docs/cscli/cscli_hub_upgrade).
- The image README notes the `slim` variant lacks the GeoIP DB and notifier plugins and tells you to run `cscli hub upgrade` in-container to fetch GeoIP at runtime — a reason to stay on `-debian`/full.
- **UNVERIFIED:** no upstream statement that hub items pinned/downloaded under 1.6.8 are incompatible with 1.8.0. Practically the hub is version-branch aware (`cscli` picks a hub branch matching the engine version), so the hub content will re-resolve to the 1.8 branch on first update.

## 1.6 LAPI / bouncer API compatibility (Traefik plugin + host firewall bouncer)

This is the highest-risk unknown, so the evidence is spelled out:

1. **No API version bump.** LAPI remains the `/v1` bouncer API (https://docs.crowdsec.net/docs/local_api/bouncers-api). No release in the 1.6.9…1.8.0 range announces a bouncer-API break.
2. **1.7.8 chunked transfer** (PR #4413, "Decision stream: move to chunked transfer by default"): this changes HTTP framing, not the JSON payload. Chunked transfer-encoding is HTTP/1.1-standard and transparent to Go/`net/http`-based clients (both the firewall bouncer and the Traefik plugin are Go).
3. **1.8.0 stream cursor** (PR #4620, "lapi: use decision id as cursor for delta pull"): the PR body states `stream_cursor` defaults to 0, so **every existing bouncer receives one full set of active decisions on its first pull after upgrade**, then runs on the cursor. Expect one large resync burst per bouncer immediately after the upgrade — not an outage, but worth watching for firewall-set churn.
4. **1.8.0 JWT-in-query removal** (PR #4554, "apiserver: prevent from fetching JWT token from query string"): bouncers authenticate with an API key in the `X-Api-Key` header, not a JWT in a query string, so standard bouncers are unaffected. Anything custom that shoved a token in a URL will break.
5. **1.7.1** changed how long bouncer names are handled when the bouncer's source IP changes (`bouncer@ip1@ip2…` no longer accumulates) — cosmetic in `cscli bouncers list`.

**Recommended bouncer versions to align to (latest upstream releases):**
- `crowdsecurity/cs-firewall-bouncer` **v0.0.36** (2026-08-04) — https://github.com/crowdsecurity/cs-firewall-bouncer/releases
- `maxlerebourg/crowdsec-bouncer-traefik-plugin` **v1.7.1** (2026-07-31) — https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/releases

**UNVERIFIED:** CrowdSec publishes no formal LAPI↔bouncer compatibility matrix, and neither bouncer's release notes state a minimum/maximum LAPI version for 1.8.0. The claim "old bouncers keep working against a 1.8.0 LAPI" is *strongly supported* by 1–5 above but is not an upstream guarantee. Treat it as: upgrade CrowdSec first, verify `cscli bouncers list` shows both bouncers pulling, then upgrade the bouncers.

## 1.7 Gotchas for docker compose (CrowdSec)

- 🔴 **Mount `/var/lib/crowdsec/data/`.** Since 1.7.0 the container **refuses to start** without it (`docker: enforce volume use for /var/lib/crowdsec/data/`, #3757). Escape hatch env var `CROWDSEC_BYPASS_DB_VOLUME_CHECK=true` exists but defeats the point — if your SQLite DB is currently inside the container's writable layer, you will silently have been losing decisions on every recreate, and adding the volume now starts from an empty DB.
  Source: `build/docker/README.md` @ v1.8.0, "Since CrowdSec 1.7.0, `/var/lib/crowdsec/data/` is required to be mounted in a volume."
- 🔴 **Persist `/etc/crowdsec`** in a named volume or bind mount. It holds the machine credentials (`local_api_credentials.yaml`, `online_api_credentials.yaml`). Losing it means re-registering the LAPI machine and re-enrolling in the console.
- 🟠 **Pin the tag.** Currently on `latest-debian`; move to `v1.8.0-debian` so the next `docker compose pull` is a decision, not an accident.
- 🟠 **`CROWDSEC_CONTAINER_ENV` is gone (1.7.4).** Grep the compose file for it.
- 🟠 **Docker log acquisition** (if used): since 1.6.9 it needs the Docker **events** API — update any socket-proxy allowlist.
- 🟠 **Hub upgrade on boot** unless `NO_HUB_UPGRADE=true`; the first start after the image bump will pull the 1.8 hub branch and may take longer than usual (hub download timeout was raised to 10 minutes in 1.7.0).
- 🟠 **RE2 (1.7.7)** raises baseline memory. On a small VPS, watch RSS after the upgrade; fall back with the `re2_disable_grok_support` feature flag if the container starts getting OOM-killed.
- 🟢 Rollback: keep the old image tag and a copy of the `/var/lib/crowdsec/data` volume (SQLite file) taken while the container is stopped. **UNVERIFIED:** CrowdSec does not document DB-schema downgrade support; assume a 1.8.0 DB cannot be re-opened by 1.6.8 and that rollback = restore the pre-upgrade data volume.

---

# 2. Authentik

## 2.1 Version facts

| Fact | Value | Source |
| --- | --- | --- |
| Installed | 2025.10.1 (2025-11-03) | https://github.com/goauthentik/authentik/releases/tag/version%2F2025.10.1 |
| Latest stable | **2026.8.1**, published 2026-09-01 | GitHub Releases API, newest non-prerelease |
| Ticket claim "2026.8.1" | ✅ correct | as above |
| Security support | Only **2026.5.x** and **2026.8.x** are supported | `SECURITY.md` @ version/2026.8.1 — https://github.com/goauthentik/authentik/blob/version/2026.8.1/SECURITY.md |
| arm64 support | ✅ `linux/amd64` + `linux/arm64` verified on the ghcr manifest list for every tag in the chain: `2025.10.1`, `2025.10.4`, `2025.12.6`, `2026.2.6`, `2026.5.6`, `2026.8.1` | `ghcr.io/goauthentik/server` manifest lists |

**The installed 2025.10 train is out of security support.** It last received a patch on 2026-02-12 (2025.10.4); every advisory published after that lists only 2025.12/2026.x fixed versions. This is the real driver for the upgrade.

Representative unpatched-on-2025.10 advisories (all from https://github.com/goauthentik/authentik/security/advisories):

| Advisory | CVE | Severity | Earliest fixed train |
| --- | --- | --- | --- |
| XML Signature Wrapping in SAML Source ACS → auth as arbitrary federated user (GHSA-c3m2-jqmq-pvp3) | CVE-2026-47201 | high | 2025.12.6 |
| SourceStage bypass via empty POST (GHSA-xp7f-xjjx-gwm8) | CVE-2026-49448 | critical | 2025.12.6 |
| Reflected XSS in SFE (GHSA-pgff-5mx8-fqj3) | CVE-2026-42849 | critical | 2025.12.5 |
| Unauthenticated access via client-controlled `X-Original-URI` in nginx forward-auth mode (GHSA-5wcc-hf24-rf5h) | — | high | 2025.12.5 |
| SAML NameID XML comment injection → auth bypass (GHSA-9wj8-xv4r-qwrp) | CVE-2026-40165 | high | 2025.12.5 |
| Account takeover via SAML NameID comment truncation (GHSA-35v6-hv2g-6992) | CVE-2026-57580 | high | 2026.2.6 / 2026.5.5 |
| RAC endpoints + stored credentials exposed to any authenticated user (GHSA-rv9x-92g6-9cpf) | CVE-2026-61574 | high | 2026.2.6 / 2026.5.5 |

## 2.2 Exact upgrade chain (ordered)

Upstream rule, verbatim intent from https://docs.goauthentik.io/install-config/upgrade (source: `website/docs/install-config/upgrade.mdx` @ version/2026.8.1):

- "Upgrades must follow the sequence of major releases; **do not skip** directly from an older major version to the most recent version."
- "Always upgrade to the latest minor version (`.x`) within each `major.minor` version before upgrading to the next major version."
- 2026.8 hardened this: "The lifecycle tooling now prevents unsupported major-version skips before migrations begin" (2026.8 release notes).
- 2026.2 release notes repeat it: "Upgrades MUST be performed sequentially by major version. If you are two or more major releases behind, you must first upgrade to each intermediate major release."

**Chain to execute — skipping is not supported:**

| Step | Target image tag | Train notes |
| --- | --- | --- |
| 0 | `2025.10.1` (current) | baseline; take pg_dump here |
| 1 | `2025.10.4` | latest patch of the current train (2026-02-12) |
| 2 | `2025.12.6` | 🔴 heaviest step — storage move + RBAC/group migrations |
| 3 | `2026.2.6` | compose file rename; SCIM/`ak_groups` changes |
| 4 | `2026.5.6` | listen-address default change |
| 5 | `2026.8.1` | final target |

Each step: pull, `docker compose up -d`, wait for migrations to finish and the instance to be healthy, sanity-check login + one app, **then** move on. Outposts must be upgraded in lockstep with the server at every step ("the version of the authentik instance and of any outposts must be the same").

## 2.3 Per-train breaking changes

### 2025.12 — https://docs.goauthentik.io/releases/2025.12 (`website/docs/releases/2025/v2025.12.md`)

- 🔴 **Storage mount move.** With local storage, authentik now expects a mount at `/data`; the existing `/media` mount must be moved to `/data/media`. Upstream's documented compose procedure: `docker compose down`, `mkdir -p ./data`, `mv ./media ./data/media`, then bring up with the new compose file.
- 🔴 **Files are served from `/files`, not `/media`.** Any reverse-proxy rule (Traefik router/middleware) that special-cases `/media` must be updated.
- 🔴 **Group name uniqueness enforced at the database level.** Upstream warning: make group names unique *before* starting the upgrade. Duplicates make the migration **fail loudly** — deliberately, no auto-rename. Check for duplicate group names in the API/admin before step 2.
- 🟠 **RBAC overhaul.** Permissions are granted exclusively via roles; existing direct user permissions are migrated to a generated role named `ak-migrated-role--user-{user_id}`. Groups now inherit all permissions from ancestor groups (previously only `is_superuser`).
- 🟠 **`Group.parent` (ForeignKey) → `Group.parents` (ManyToManyField).** Custom expression policies / property mappings touching group or role membership must be reviewed.
- 🟠 Custom flow CSS may need revision (mobile/tablet UI rework).

### 2026.2 — https://docs.goauthentik.io/releases/2026.2

- 🔴 **Compose file renamed: `docker-compose.yml` → `compose.yml`.** Upstream tells you to port your local edits into the new file before deleting the old one. If you keep a hand-maintained compose file this is mostly a naming decision, but the upstream reference file's paths changed too.
- 🟠 **SCIM group syncing behaviour changed.** Users are filtered by the policies bound to the SCIM provider's application; providers with an existing group filter are **deactivated** and raise a configuration warning for manual review.
- 🟠 **`User.ak_groups` deprecated** in favour of `User.groups`. Still functional, but emits a configuration-warning event (at most every 30 days). Audit expression policies / property mappings.
- 🟠 Runtime moved to Python 3.14.
- ℹ️ Release cadence changed from ~2 months to ~3 months; still only the two most recent trains get security coverage.

### 2026.5 — https://docs.goauthentik.io/releases/2026.5

- 🔴 **Default listen IP changed from `0.0.0.0` to `[::]`** (listen settings now accept a comma-separated list of IPs). Upstream: "Some IPv4-only environments might need to adapt those settings." On a dual-stack Docker host this is a no-op; on an IPv6-disabled kernel/container it can prevent the server from binding — verify the container comes up and Traefik's backend health check passes.
- 🟠 **`AUTHENTIK_POSTGRESQL__CONN_OPTIONS` (and its replica equivalent) deprecated**, slated for removal in the next version. Remove it if present.
- 🟠 Worker now starts through a Rust entrypoint (~200 MB less RSS per worker container, one fewer PG connection per worker). Behavioural parity intended, but this is where worker-health regressions would show up.
- ℹ️ Applications previously hidden via `Launch URL = blank://blank` are auto-migrated to the new "Hide from Application Dashboard" toggle.

### 2026.8 — https://docs.goauthentik.io/releases/2026.8

- 🔴 **`hash_password` management command no longer accepts the password as a positional argument** (it leaked into the process list). Use the interactive prompt (`docker compose run --rm server hash_password`) or pipe via stdin. Only affects automation that calls it.
- 🔴 **"Prevent duplicate devices" removed from the WebAuthn authenticator setup stage.** It was already disabled by default in 2026.5.4; no action needed on upgrade, but the option disappears from the stage config.
- 🟠 **Task status now reflects task logs.** Tasks that logged errors but completed were previously marked successful and hidden; they will now surface as errors/warnings on the System Tasks page after the upgrade. Expect *apparent* new failures that were actually pre-existing.
- 🟠 **Server and proxy outpost rewritten from Go to Rust** (entrypoint/proxy layer only; the Django core is unchanged). Intended as a 1:1 behavioural match — this is the change most likely to interact with a reverse proxy in front. Related changelog entry: `packages/ak-axum: extract the rightmost untrusted IP from X-Forwarded-For (#25397)`.
- 🟠 **`AUTHENTIK_WEB__BASE_URL` / "Base URL" system setting** introduced; scheme+host only, even when served under a subpath. **It becomes required in 2026.11** — set it now to avoid a forced change at the next upgrade.
- ℹ️ New PostgreSQL transaction-pooler support (`AUTHENTIK_POSTGRESQL__DIRECT__*`) — optional, not needed for a single local PG container.

## 2.4 `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` — the ticket's premise is wrong

**No train in 2025.10 → 2026.8 made this variable required.** Verified by diffing the configuration reference across four tags (`website/docs/install-config/configuration/configuration.mdx` at `version/2025.10.4`, `version/2025.12.6`, `version/2026.2.6`, `version/2026.5.6`, `version/2026.8.1`): the setting is documented in all of them with identical text and identical defaults.

- Semantics (docs, 2026.8.1): "List of comma-separated CIDRs that proxy headers should be accepted from. Applies to the Server. Requests directly coming from … an address within a CIDR specified here are able to set proxy headers, such as `X-Forwarded-For`. Requests coming from other addresses will not be able to set these headers."
- **Default:** `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fe80::/10`, `::1/128` — unchanged across all five tags checked.
- Docs URL: https://docs.goauthentik.io/install-config/configuration/#authentik_listen__trusted_proxy_cidrs

**Correct value semantics for Traefik on the same Docker network:** Docker's default address pools for user-defined bridge networks live in `172.16.0.0/12` (and `192.168.0.0/16`), both already in the default list. So with Traefik as a sibling container, the default already trusts it and `X-Forwarded-For` is honoured — **no change required**. Set it explicitly only if:
- your compose network uses a custom subnet outside those RFC1918 ranges, or
- you want to tighten it: set it to exactly the Traefik container's network subnet (e.g. `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS=172.18.0.0/16`), not to the public IP and not to `0.0.0.0/0`.

Related change to watch at 2026.8: the Rust server extracts the *rightmost untrusted* IP from `X-Forwarded-For` (#25397). If Traefik is the only hop, the client IP in authentik events stays correct; if there is an additional upstream proxy (Cloudflare etc.), verify event source IPs after step 5.

**UNVERIFIED:** the ticket's claim that some train "made `TRUSTED_PROXY_CIDRS` required" could not be substantiated in any release note or config doc in this range. If the source of that claim was an operator observing wrong client IPs, the likely real cause is the 2026.8 XFF-extraction change or a non-RFC1918 Docker subnet, not a new requirement.

## 2.5 PostgreSQL compatibility

- 2026.8 configuration reference: "authentik supports PostgreSQL 14 - 18." (`website/docs/install-config/configuration/configuration.mdx` @ version/2026.8.1 — https://docs.goauthentik.io/install-config/configuration/#postgresql-settings)
- ✅ **`postgres:16-alpine` remains supported at the target train. No PostgreSQL major upgrade is required for this ticket.** Keep the PG version constant across the whole authentik chain so that a rollback only has to undo one variable.
- Same doc (2026.5.6) also states 14–18, so no intermediate train narrows the window.
- If you do decide to move PG later, upstream has a dedicated procedure: https://docs.goauthentik.io/troubleshooting/postgres/upgrade_docker — do it as a separate change, not inside this upgrade.
- 🟠 2026.5 deprecates `AUTHENTIK_POSTGRESQL__CONN_OPTIONS`; 2026.8 marks it deprecated in favour of the pooler settings. Remove if set.

## 2.6 Backup and rollback

From https://docs.goauthentik.io/install-config/upgrade and https://docs.goauthentik.io/sys-mgmt/ops/backup-restore:

- 🔴 **"authentik does not support downgrading. Make sure to back up your database in case you need to revert an upgrade."** (upstream `:::danger` admonition). **You cannot step a train back.** Rollback = restore the PostgreSQL dump taken before that step *and* revert the image tag.
- **Backup before every step**, not just before step 1: use `pg_dump` / `pg_dumpall` / continuous archiving; exclude `template0` and `template1`; store off-host.
- **Restore** with `pg_restore` or `psql` depending on dump format, *before* bringing authentik back up; verify completeness before reconnecting.
- **Also back up these mounts:** `/data` (icons, flow backgrounds, uploaded files, CSV exports — post-2025.12 path; `/media` pre-2025.12), `/certs` (only if you rely on filesystem certs; imported certs live in the DB), `/custom-templates`, `/blueprints`.
- **Migration-inconsistency escape hatch** (upstream troubleshooting): if the dashboard version doesn't change after an upgrade, check server logs for `migration inconsistency`; if present, revert to the database backup and redo the upgrade in strict sequence.

## 2.7 Gotchas for docker compose (Authentik)

- 🔴 **Five separate `docker compose pull` + `up -d` cycles**, each preceded by a `pg_dump`. Budget maintenance-window time accordingly; migrations at 2025.12 (RBAC/groups) are the slowest.
- 🔴 **Pre-flight for 2025.12: find duplicate group names** and rename them *before* touching the images, or the migration aborts mid-upgrade.
- 🔴 **Pre-flight for 2025.12: the `./media` → `./data/media` host move**, executed with the stack down. Update both the `server` and `worker` service volume mappings (`./data:/data`), since both need file storage.
- 🔴 **Traefik: any router/middleware matching `/media`** must be updated to `/files` at 2025.12.
- 🟠 **Pin exact tags per step** (`ghcr.io/goauthentik/server:2025.12.6`, etc.), never `latest`, or the lifecycle skip-guard at 2026.8 will refuse a jump it detects.
- 🟠 **Server and worker use the same image tag** — bump both together; a mixed pair mid-upgrade is unsupported.
- 🟠 **Outposts must match the server version at every step.** If the embedded outpost is the only one in use this is automatic; any standalone proxy/LDAP outpost container needs its tag bumped in the same step.
- 🟠 **2026.5 `[::]` bind:** if the VPS or Docker daemon has IPv6 disabled, verify the container binds and Traefik's health check succeeds before proceeding to 2026.8.
- 🟠 **2026.8:** set `AUTHENTIK_WEB__BASE_URL` (scheme + host only) now, since 2026.11 will require it. Also expect previously-hidden failing tasks to appear on the System Tasks page — triage them, don't assume the upgrade caused them.
- 🟢 Consider dropping the ghcr digest of each step's image into the changelog so a rollback pulls exactly the image you validated.

---

# 3. ARM64 confirmation (both components)

| Image | Tag | Platforms |
| --- | --- | --- |
| `crowdsecurity/crowdsec` | `v1.8.0-debian` | linux/386, linux/amd64, **linux/arm64** |
| `crowdsecurity/crowdsec` | `v1.8.0`, `v1.8.0-slim` | linux/386, linux/amd64, linux/arm, **linux/arm64** |
| `ghcr.io/goauthentik/server` | `2025.10.1` (current) | linux/amd64, **linux/arm64** |
| `ghcr.io/goauthentik/server` | `2025.10.4` | linux/amd64, **linux/arm64** |
| `ghcr.io/goauthentik/server` | `2025.12.6` | linux/amd64, **linux/arm64** |
| `ghcr.io/goauthentik/server` | `2026.2.6` | linux/amd64, **linux/arm64** |
| `ghcr.io/goauthentik/server` | `2026.5.6` | linux/amd64, **linux/arm64** |
| `ghcr.io/goauthentik/server` | `2026.8.1` | linux/amd64, **linux/arm64** |

Method: OCI manifest-list inspection via the Docker Hub tags API (`hub.docker.com/v2/repositories/crowdsecurity/crowdsec/tags`) and anonymous ghcr token + `Accept: application/vnd.oci.image.index.v1+json` against `ghcr.io/v2/goauthentik/server/manifests/<tag>`.

Every tag in the upgrade chain was manifest-checked individually; there are no assumed rows in this table.

---

# 4. Contradictions found

1. **Ticket vs. reality on `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`.** The ticket assumes a train made it required. The configuration reference carries identical text and identical defaults at 2025.10.4, 2025.12.6, 2026.2.6, 2026.5.6 and 2026.8.1. No train made it required; the defaults already cover Docker bridge networks. See §2.4.
2. **CrowdSec advisory severity vs. urgency framing.** Both advisories are rated *medium* and require the opt-in HTTP or k8s-audit acquisition datasources. If neither is configured on this host, the CVE argument for the CrowdSec upgrade is weak — the stronger argument is that 1.6.8 is fifteen months behind. Authentik is the genuinely urgent half of this ticket (out-of-support train with unpatched critical/high advisories).
3. **"Both upgrades are the same shape."** They are not: CrowdSec is a single hop with deployment-shape prerequisites; Authentik is a five-step sequential chain with an explicit no-downgrade policy. Sequencing them as one change window is a mistake — do CrowdSec first (fast, reversible via volume snapshot), Authentik second.

# 5. What remains unknown (UNVERIFIED)

- **No upstream CrowdSec LAPI ↔ bouncer compatibility matrix exists.** The conclusion that the existing Traefik plugin and firewall bouncer keep working against a 1.8.0 LAPI is inference from PR #4620/#4413/#4554 and the unchanged `/v1` API surface, not an upstream guarantee.
- **No upstream CrowdSec 1.6 → 1.8 migration document.** Release notes are the only migration record; a config-schema change that was never mentioned in release notes would not be caught by this research.
- **CrowdSec DB downgrade support is undocumented.** Assume a 1.8.0 SQLite schema is not readable by 1.6.8.
- **Hub item compatibility across the 1.6 → 1.8 hub branches** is not explicitly documented; assumed to self-resolve on the first `cscli hub update`.
- **The exact Docker network subnet in use on this VPS** was not inspected (no repository access in this task), so §2.4's "default already covers Traefik" holds only if the compose network is inside RFC1918. Verify with `docker network inspect` before relying on it.
- **Whether the CrowdSec HTTP / k8s-audit acquisition datasources are actually configured** on this host was not checked — this determines whether the two advisories apply at all.
- **Authentik 2025.10 → 2025.12 real-world migration duration** on this dataset size is unknown; the RBAC/group migrations are the ones that can run long.
