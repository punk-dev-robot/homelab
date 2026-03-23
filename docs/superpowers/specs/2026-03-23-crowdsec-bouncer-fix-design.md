# CrowdSec Bouncer Fix & VPS Cleanup

**Date**: 2026-03-23
**Status**: Implemented

## Problem

The CrowdSec Traefik bouncer on the gateway VPS only protected 4 core routes (pangolin, api, int-api, auth). All ~30 Pangolin-managed service routes (grafana, jellyfin, sonarr, etc.) were unprotected because the bouncer middleware was applied per-router instead of at the Traefik entrypoint level.

Additionally:
- Two stale bouncer registrations existed from pre-Feb-9 container restarts
- The Traefik access log had never been rotated (15.5GB, caused a disk-full incident on Feb 8-9)
- The bouncer ran in `live` mode (LAPI query per request), which doesn't scale for all traffic

## Root Cause

The CrowdSec integration was set up via Ansible rather than the Pangolin installer. The installer applies the bouncer middleware at the Traefik entrypoint level (covering all routes automatically). Our manual setup only applied it to specific routers in `dynamic_config.yml`, leaving Pangolin-managed services unprotected.

Per Pangolin docs (Middleware Manager troubleshooting):
> "Protecting Pangolin itself - Apply middlewares directly on the websecure entryPoint to cover all traffic."
> "Applying to many services - Attach middleware to entryPoints instead of individual resources."

## Changes Made

### 1. Entrypoint-level CrowdSec middleware

**Files changed**:
- `ansible/files/gateway-vps/pangolin/traefik_static_config/traefik_config.yml`

Added `crowdsec-bouncer@file` middleware to the `websecure` entrypoint, ensuring all HTTPS traffic passes through CrowdSec regardless of router config.

### 2. Stream mode + remove redundant per-router middleware

**Files changed**:
- `ansible/files/gateway-vps/pangolin/traefik_rules/dynamic_config.yml`
- `ansible/roles/docker/templates/dynamic_config.yml.j2` (Jinja2 template - actual source of truth)

- Changed `crowdsecMode` from `live` to `stream` with 15s update interval
- Removed per-router `crowdsec-bouncer` middleware from 4 core routers (now redundant since entrypoint handles it)

Note: The Jinja2 template overrides the files/ version at deploy time. Both must be kept in sync.

### 3. Stale bouncer cleanup + logrotate

**Files changed**:
- `ansible/deploy_vps.yml` - Added logrotate deployment task and stale bouncer cleanup tasks
- `ansible/files/gateway-vps/logrotate/traefik` - New logrotate config (daily, 7 files, 500MB max, compressed, USR1 signal to Traefik)

## Verification

- Gateway VPS smoke tests: passed
- Bouncer status: `traefik-bouncer` using `/v1/decisions/stream` (stream mode confirmed)
- Two clean bouncer registrations only (traefik-bouncer + crowdsec-firewall-bouncer)
- Services accessible in browser: confirmed
- Logrotate config deployed to `/etc/logrotate.d/traefik`

## References

- Pangolin CrowdSec docs: https://docs.pangolin.net/self-host/community-guides/crowdsec
- Pangolin Middleware Manager: https://docs.pangolin.net/self-host/community-guides/middlewaremanager#troubleshooting
- CrowdSec bouncer plugin: https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin
- CrowdSec Console remediation metrics: https://doc.crowdsec.net/u/console/remediation_metrics
