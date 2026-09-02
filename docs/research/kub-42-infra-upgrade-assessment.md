# KUB-42 — Infra upgrade assessment for Talos-on-Proxmox

**Date of evidence:** 2026-09-02 (UTC). Version "latest" claims are point-in-time.
**Scope:** read-only version discovery on live infra + primary-source latest-version research.
**No changes were made to any host.** The complete set of live commands run is enumerated in the
"Method / commands used" section at the end of this brief: `pveversion -v`, `qemu-system-x86_64 --version`,
`pvesh get /version`, `pvesm status`, `cat /etc/pve/storage.cfg`, `docker ps`, `docker inspect`,
`docker exec crowdsec cscli version`, and unauthenticated HTTPS GETs. All are read-only.

---

## Question

What are the current versus latest versions of the homelab platform components, and which of those
upgrades **block** or **materially benefit** running Talos Linux VMs on Proxmox VE provisioned through
OpenTofu with the `bpg/proxmox` provider?

## Answer (short)

Nothing currently blocks the Talos-on-Proxmox work. The three PVE nodes run **9.1.2**, and `bpg/proxmox`
requires **Proxmox VE 9.x** — the requirement is already met, so the migration can start today. The only
Proxmox-side caveat is that the provider does **not** support the new PVE 9.x HA-resources API, so Talos VM
HA membership must be managed outside OpenTofu. The genuinely urgent items are on the gateway VPS and are
security/exposure debt unrelated to Talos: Authentik 2025.10.1 is ~10 months and three release trains behind
2026.8.1, and CrowdSec 1.6.8 is behind 1.8.0 which fixes two DoS advisories. Those belong on the
upgrade-now list; PVE 9.1.2 → 9.2 and everything else can be sequenced deliberately.

---

## Current vs latest

| Component | Current (observed) | Latest stable (2026-09-02) | Gap | Source |
|---|---|---|---|---|
| Proxmox VE (px-cpu 10.10.101.11) | 9.1.2 / kernel 6.17.4-1-pve | 9.2 | 1 minor | `pveversion`; [PVE Downloads](https://pve.proxmox.com/wiki/Downloads) |
| Proxmox VE (px-net 10.10.101.12) | 9.1.2 / kernel 6.17.4-1-pve | 9.2 | 1 minor | `pveversion` |
| Proxmox VE (px-nas 10.10.101.13) | 9.1.2 / kernel 6.17.4-1-pve | 9.2 | 1 minor | `pveversion` |
| QEMU on all 3 nodes | 10.1.2 (`pve-qemu-kvm_10.1.2-4`) | ships with PVE | — | `qemu-system-x86_64 --version` |
| Proxmox Backup Server | **UNVERIFIED** (host 10.10.10.34, unreachable) | 4.2 | unknown | [PBS Roadmap](https://pbs.proxmox.com/wiki/index.php/Roadmap) |
| TrueNAS | **UNVERIFIED** (host 10.10.10.31, auth failed) | 26 series documented; exact patch **UNVERIFIED** | unknown | [TrueNAS docs hub](https://www.truenas.com/docs/scale/gettingstarted/versionnotes/) |
| OPNsense | **UNVERIFIED** (no host/IP resolvable) | 26.7.3 (2026-08-27), "Xenial Xenops" CE | unknown | [OPNsense CE 26.7 releases](https://docs.opnsense.org/releases/CE_26.7.html) |
| Authentik (server + worker) | 2025.10.1 | 2026.8.1 (2026-09-01) | 3 release trains | `docker ps`; [releases](https://github.com/goauthentik/authentik/releases) |
| Pangolin | 1.12.2 | 1.22.0 (2026-08-27) | 10 minors | `docker ps`; [1.22.0 notes](https://github.com/fosrl/pangolin/releases/tag/1.22.0) |
| Gerbil | 1.2.2 | 1.5.1 (2026-08-31) | 3 minors | `docker ps`; [releases](https://github.com/fosrl/gerbil/releases) |
| Traefik | v3.6.0 | v3.7.12 (2026-08-26) | 1 minor + 12 patches | `docker inspect`; [v3.7.0 notes](https://github.com/traefik/traefik/releases/tag/v3.7.0) |
| CrowdSec | 1.6.8 (image tag `latest-debian`) | 1.8.0 (2026-08-31) | 2 minors | `docker exec crowdsec cscli version`; [v1.8.0 notes](https://github.com/crowdsecurity/crowdsec/releases/tag/v1.8.0) |
| middleware-manager (midman) | v3.0.1 | v4.5.0 (2026-03-24) | 1 major | `docker ps`; [releases](https://github.com/hhftechnology/middleware-manager/releases) |
| Dozzle | v8.13.1 (tag `latest`) | not researched | — | `docker inspect` |
| authentik-postgresql | postgres:16-alpine | not researched | — | `docker ps` |
| `bpg/proxmox` provider | not yet in repo (no `.tf` files found) | v0.111.1 (2026-07-03) | n/a | [CHANGELOG](https://github.com/bpg/terraform-provider-proxmox/blob/main/CHANGELOG.md) |
| Talos Linux | not yet deployed | v1.13.9 (2026-08-19); v1.14.0-rc.2 in prerelease | n/a | [releases](https://github.com/siderolabs/talos/releases) |

---

## Talos-on-Proxmox verdict

### Provider requirement — satisfied, not a blocker

The `bpg/proxmox` README states its production requirements as **Proxmox VE 9.x**, TLS 1.3 on the API
endpoint (TLS 1.2 optionally supported), and **Terraform 1.5+ / OpenTofu 1.6+** (write-only attributes need
Terraform 1.11+ / OpenTofu 1.10+). It further says the provider "is compatible with Proxmox VE 9.x
(currently **9.2**)", that 8.x "is supported, but some functionality might be limited", and that **7.x is
NOT supported**.
Source: <https://github.com/bpg/terraform-provider-proxmox/blob/main/README.md>

All three nodes run 9.1.2, so the minimum is already met. **No Proxmox upgrade is required to begin the
Talos migration.**

### The one real caveat

The provider's own Known Issues section records that **PVE 9.x's new HA-resources API is not yet supported
by the provider** (tracked as [issue #2097](https://github.com/bpg/terraform-provider-proxmox/issues/2097)).
If the Talos control-plane VMs are meant to be HA-managed cluster resources, that membership cannot be
declared in OpenTofu today and must be handled out-of-band (Ansible or manual). Plan the module boundary
around this rather than discovering it mid-apply.

A second, smaller one, also from the provider's Known Issues: snippets and backups must be uploaded over
**SFTP** because the PVE API cannot do it, and **creating many VMs simultaneously can cause lock errors**
from PVE I/O contention. Both matter directly for a Talos bootstrap that uploads a machine-config snippet
and then creates several nodes in one apply — expect to need `-parallelism` tuning.

### Upgrade now

1. **CrowdSec 1.6.8 → 1.8.0** — *security, not Talos-related, but highest priority.* v1.8.0 fixes two
   denial-of-service advisories in the acquisition datasources:
   [GHSA-g2x2-jgfg-pg7g](https://github.com/crowdsecurity/crowdsec/security/advisories/GHSA-g2x2-jgfg-pg7g)
   (HTTP datasource lacks a decompressed body cap and trusts `Content-Length`) and
   [GHSA-rh69-4vqj-9gj8](https://github.com/crowdsecurity/crowdsec/security/advisories/GHSA-rh69-4vqj-9gj8)
   (unbounded request-body read in the kubernetes-audit webhook). This container is on the internet-facing
   gateway VPS. 1.8.0 also adds a **dedicated Kubernetes log-acquisition datasource** that pulls logs from
   the k8s apiserver — a direct forward-benefit once the Talos cluster exists.
   Source: <https://github.com/crowdsecurity/crowdsec/releases/tag/v1.8.0>
2. **Authentik 2025.10.1 → 2026.8.1** — *do this before the migration, and do it in steps.* Authentik's own
   upgrade docs, in the troubleshooting section on migration inconsistency, instruct: "upgrade in sequence,
   do not skip directly to the most recent version."
   (<https://docs.goauthentik.io/install-config/upgrade>). Two breaking changes matter for this deployment
   specifically: **forwarded headers are now restricted to trusted proxies** as of 2026.8 — the server only
   honours `X-Forwarded-Proto`/`-Host`/`-For` from networks listed in
   `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`, and a misconfiguration here "can cause authentik to interpret
   HTTPS requests as HTTP, resulting in blocked mixed content, an endless loading indicator, or
   authentication errors". Since Authentik sits behind Traefik on this VPS, the trusted-CIDR value must be
   set *before* the upgrade. Also breaking: `hash_password` command changes, and removal of "Prevent
   duplicate device" from the WebAuthn setup stage. `postgres:16-alpine` should be checked against 2026.8's
   supported range in the same window; PostgreSQL **custom connection options are deprecated** in 2026.8.
   Source: <https://docs.goauthentik.io/releases/2026.8>
3. **Fix or decommission the PBS target before touching anything.** `pvesm status` reports the `pbs-zima`
   storage as **`inactive` on all three nodes**, and the PBS API at `10.10.10.34:8007` did not respond from
   the workstation. The storage config (`/etc/pve/storage.cfg`) shows `datastore pbs-local`, `server
   10.10.10.34`, `prune-backups keep-all=1`. **Treat the cluster as currently un-backed-up.** Whether this
   is a genuine outage or just workstation-to-`10.10.10.0/24` network isolation is `UNVERIFIED` — but no
   node-level upgrade should proceed until a restorable backup is confirmed.

### Defer

- **PVE 9.1.2 → 9.2** — beneficial but not required; the provider already supports 9.1.2 and explicitly
  tracks 9.2 as its current test target, so upgrading brings the fleet onto the provider's best-tested
  version. Do it *after* PBS is healthy, one node at a time. One documented gotcha applies to this cluster:
  a **transient upgrade issue with a disarmed HA stack** — if the HA stack is disarmed while resources are
  still migrating, the upgrade can stall on `pve-ha-manager` package triggers; keep the HA stack armed or
  wait for migrations to finish. Source: <https://pve.proxmox.com/wiki/Roadmap>
- **Pangolin 1.12.2 → 1.22.0 and Gerbil 1.2.2 → 1.5.1** — ten minor versions is a large jump with no
  Talos relevance. Note 1.22.0 requires the **Badger Traefik plugin at v1.6.0 or greater**, with the
  migration attempting to update it automatically only if it finds the Traefik config in the standard
  location. Sequence Pangolin/Gerbil/Badger together, separately from the migration work.
  Source: <https://github.com/fosrl/pangolin/releases/tag/1.22.0>
- **Traefik v3.6.0 → v3.7.12** — the v3.7.0 notes direct readers to the
  [v3.7 migration guide](https://doc.traefik.io/traefik/v3.7/migrate/v3/#v370); v3.7 adds a providers
  routing-precedence setting and wildcard host matchers. Coordinate with the Pangolin/Badger work since
  both touch the same Traefik instance.
- **middleware-manager v3.0.1 → v4.5.0** — a major-version jump; no evidence gathered on its breaking
  changes. Defer until the Pangolin stack is being touched anyway.
- **Talos version choice** — target **v1.13.9**, the current stable. v1.14.0 is at rc.2 and should not be
  the migration target.
- **TrueNAS / OPNsense** — cannot be assessed without version data (see UNVERIFIED).

---

## Contradictions found

- The CrowdSec container image is tagged `latest-debian`, but the running binary reports
  `v1.6.8-f209766e`, BuildDate `2025-03-25`, while `docker inspect` reports the image `Created` as
  `2026-03-23`. A floating tag has therefore **not** produced a current build — the image has not been
  re-pulled, or the `Created` timestamp reflects a rebuild that did not advance the CrowdSec version.
  Either way, `latest-debian` is not delivering 1.8.0, and the tag should be pinned to an explicit version
  so drift is visible. Same risk applies to `dozzle:latest` (running v8.13.1) and
  `henrygd/beszel-agent` (untagged).
- Container uptimes read "Up 4 months" / "Up 3 months", which is consistent with images not having been
  refreshed since roughly May 2026.

## UNVERIFIED

- **Proxmox Backup Server version.** Host is `10.10.10.34` per `/etc/pve/storage.cfg`; the API at
  `:8007` did not respond from the workstation and the package is not installed on any PVE node. Latest
  is PBS 4.2, whose release notes state "Known Issues & Breaking Changes: None at time of release"
  (<https://pbs.proxmox.com/wiki/index.php/Roadmap>).
- **Whether `pbs-zima` being `inactive` is a real outage** or an artefact of the workstation not having a
  route into `10.10.10.0/24`. Must be checked from a PVE node.
- **TrueNAS version.** Host `truenas.lan` → `10.10.10.31`; SSH refused with "Too many authentication
  failures", and `https://10.10.10.31/api2/json/version` returned 404 (that is a Proxmox path, not a
  TrueNAS one — the TrueNAS API needs auth and a different endpoint). Latest-stable TrueNAS is also only
  partially established: the docs hub offers 27 (nightly), 26, 25.10, 25.04, and the 26.x release-notes
  page did not resolve.
- **OPNsense version.** No host entry in the Ansible inventory and `opnsense.lan` does not resolve from
  the workstation; no credentials attempted.
- **middleware-manager v4.x breaking changes** — release notes not read.
- **PostgreSQL 16 support status under Authentik 2026.8** — the deprecation of custom connection options
  was captured, but the supported-version range was not confirmed.
- **Talos-on-Proxmox official guide.** The `v1.13` URL 404s; the reachable equivalent is the v1.12 page
  (<https://www.talos.dev/v1.12/talos-guides/install/virtualized-platforms/proxmox/>). Its contents were
  not read in depth for this brief.

## Method / commands used (all read-only)

```
ssh root@10.10.101.{11,12,13} 'pveversion -v; qemu-system-x86_64 --version; pvesh get /version'
ssh root@10.10.101.{11,12,13} 'pvesm status; cat /etc/pve/storage.cfg'
ssh ubuntu@141.147.93.212 'docker ps --format ...; docker inspect <c> --format ...'
ssh ubuntu@141.147.93.212 'docker exec crowdsec cscli version'
curl -sk https://10.10.10.34:8007/api2/json/version   # no response
```

Note: `ansible` is not installed on the workstation (`ansible: command not found`), so host targeting was
resolved from `ansible/inventory.yml` and executed over plain SSH instead.
