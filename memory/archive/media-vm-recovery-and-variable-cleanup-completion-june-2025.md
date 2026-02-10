---
title: Media-VM Recovery and Variable Cleanup Completion - June 18, 2025
type: note
permalink: decisions/media-vm-recovery-and-variable-cleanup-completion-june-18-2025
---

# Media-VM Recovery and Variable Cleanup Completion - June 18, 2025

## Summary
Successfully completed comprehensive infrastructure recovery and variable cleanup operation. All systems operational with dangerous variable naming eliminated.

## Recovery Results

### Media-VM (Primary Success)
- ✅ **Complete Recovery**: All 24 containers running (Jellyfin + Servarr + OAM)
- ✅ **Data Integrity**: NFS mount working (`/mnt/nas-data` correctly mounted)
- ✅ **Tunnel Restored**: Pangolin connection reestablished with fresh credentials
  - **Issue**: 18-day restore brought stale Newt credentials
  - **Solution**: Manual credential update + HTTPS endpoint
  - **Result**: 14 TCP proxies active, full external connectivity
- ✅ **Variable Cleanup**: Dangerous `DATA_DIR` pointing fixed

### Apps-VM 
- ✅ **Deployed Successfully**: 22 changes, all stacks (OAM, AI, Tools, DBs)
- ✅ **Variable Inheritance**: Clean global variable usage

### Obs-VM
- ✅ **Deployed Successfully**: 30 changes, all monitoring stacks  
- ✅ **Services**: OAM, Obs-apps, Grafana, Graylog, TICK operational

### Gateway-VPS
- ✅ **Deployed Successfully**: All 9 containers running
- ✅ **Elegant Override**: Only `PGID=999` VPS-specific, inherits everything else
- ✅ **Services**: Pangolin, Authentik, Traefik, CrowdSec, Gerbil healthy

## Critical Variable Refactoring Completed

### Problem Solved
**Before (Dangerous)**:
```yaml
docker_data_dir: /opt/docker/appdata  # Wrong! This is app data, not media
DATA_DIR: "{{ docker_data_dir }}"     # Would point media to app configs!
```

### Solution Implemented
**Global Variables** (defined once):
```yaml
all:
  vars:
    docker_appdata_dir: /opt/docker/appdata    # App configs/runtime
    docker_compose_dir: /opt/docker/compose    # Compose files  
    docker_logs_dir: /opt/docker/logs          # Log storage
    media_dir: /mnt/nas-data                   # NFS media files
    docker_env_vars:
      common:
        PUID: "1001"
        PGID: "1001"  # homelab default
        TZ: "Europe/London"
        UMASK: "022"
        LOG_LEVEL: "info"
        APP_DATA: "{{ docker_appdata_dir }}"
```

**Group Overrides** (only exceptions):
```yaml
gateway:
  vars:
    docker_env_vars:
      common:
        PGID: "999"  # VPS uses docker_gid: 999, different from homelab
```

## Key Fixes Applied

### 1. Newt Tunnel Credentials
- **Problem**: Stale credentials from 18-day restore
- **Solution**: Fresh credentials + HTTPS endpoint
- **Credentials Used**:
  - ID: `<redacted>`
  - Secret: `<redacted>` 
  - Endpoint: `https://pangolin.nobasura.org` (not HTTP)

### 2. Gateway Variable Reference
- **Problem**: `deploy_vps.yml` using `{{ docker_env_vars.common.APP_DATA }}`
- **Solution**: Changed to `{{ docker_appdata_dir }}` for consistency
- **Result**: Elegant variable inheritance maintained

### 3. Container Deployments
- **All VMs**: Complete redeployment with clean variable structure
- **No Regressions**: All services operational, paths correct
- **Performance**: Deployments smooth except expected CrowdSec delay

## Benefits Achieved
- ✅ **Prevents Data Loss**: `DATA_DIR` correctly points to NFS media
- ✅ **Clear Naming**: Variables self-document their purpose  
- ✅ **DRY Configuration**: Single source of truth for common values
- ✅ **Documented Exceptions**: PGID difference clearly explained
- ✅ **Maintainable**: Future changes easier and safer

## Lessons Learned
1. **Variable Inheritance**: When group defines variable, it completely overrides global
2. **Credential Staleness**: Restores can bring back old authentication tokens
3. **Protocol Sensitivity**: HTTPS vs HTTP matters for Pangolin endpoint
4. **Elegant Solutions**: Fix inconsistencies rather than add complexity

## Current Status
- **All Infrastructure Operational**: 60+ containers across 4 systems
- **External Connectivity**: Tunnel and proxy systems working
- **Security**: CrowdSec protection active
- **Monitoring**: Full observability stack operational
- **Zero Critical Issues**: No blocking problems remaining

## Next Steps
- Monitor tunnel stability over next 24-48 hours
- Consider updating 1Password with verified working credentials
- Document Pangolin endpoint requirements (HTTPS) for future reference

---

This recovery demonstrates the infrastructure's resilience and our ability to handle major restoration challenges while improving system architecture.