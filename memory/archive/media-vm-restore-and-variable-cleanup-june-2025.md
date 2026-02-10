---
title: Media-VM Restore and Variable Cleanup - June 18, 2025
type: note
permalink: decisions/media-vm-restore-and-variable-cleanup-june-18-2025
---

# Media-VM Restore and Variable Cleanup - June 18, 2025

## Summary
Successfully completed major infrastructure restore and variable cleanup operation. Media-VM restored from 18-day backup and dangerous ansible variable naming fixed.

## Restore Status
- **VM Status**: ✅ Restored and running (accessible on 10.10.10.20/media.lan)
- **Container Count**: 21 containers running from backup (Jellyfin + full Servarr stack)
- **NFS Mount**: ✅ Working (`/mnt/nas-data` mounted from truenas.lan)
- **Git State**: Preserved with commit `9452f76` containing inventory fix + SSO work

## Critical Variable Refactoring Completed

### Problem Fixed
**Before (Dangerous)**:
- `docker_data_dir: /opt/docker/appdata` ← Wrong! This is app data, not media
- `DATA_DIR: "{{ docker_data_dir }}"` ← Would point media to app configs!

### Solution Implemented
**Global Variables** (defined once in `all:vars:`):
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
      oam:
        WT_GOTIFY_TOKEN: "{{ lookup('community.general.onepassword', 'WT_GOTIFY_TOKEN', vault='Homelab') }}"
```

**Group Overrides** (only exceptions):
```yaml
# Docker group: Clean inheritance (no vars needed)
docker:
  vars:  # Empty - inherits everything from global

# Gateway group: Only override what's different
gateway:
  vars:
    docker_env_vars:
      common:
        PGID: "999"  # VPS uses docker_gid: 999, different from homelab
```

## Key Benefits Achieved
- ✅ **Prevents data loss**: `DATA_DIR` correctly points to NFS media (`/mnt/nas-data`)
- ✅ **Clear naming**: Variables self-document their purpose
- ✅ **DRY configuration**: Single source of truth for common values
- ✅ **Documented exceptions**: PGID difference clearly explained

## Testing Status
- ✅ **Syntax check**: Ansible playbook valid
- ✅ **Dry run media-vm**: All stacks (oam, servarr, jelly) process correctly
- ⏳ **Pending**: Dry run on apps-vm, obs-vm, gateway-vps

## Next Steps
1. Test dry runs on all other VMs/VPS to ensure no regressions
2. Deploy to media-vm when confident
3. Verify Jellyfin and media services accessibility
4. Complete SSO configuration (was never finished on Jellyfin)

## Files Modified
- `ansible/inventory.yml` - Global variable consolidation
- `ansible/deploy_docker.yml` - Updated NFS mount path reference
- `ansible/roles/docker/defaults/main.yml` - Cleaned up variable definitions

## Critical Lesson
**Variable inheritance in Ansible**: When a group defines a variable (even partially), it completely overrides the global definition rather than merging. Solution: Use explicit inheritance or keep truly global variables separate from group-specific ones.