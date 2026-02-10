---
title: VPS Recovery Progress - Host-Level Variable Solution June 18, 2025
type: note
permalink: decisions/vps-recovery-progress-host-level-variable-solution-june-18-2025
---

# VPS Recovery Progress - Host-Level Variable Solution June 18, 2025

## Current Status: READY TO TEST ✅
- **Issue**: VPS access broken due to Authentik permission errors
- **Root Cause**: Missing APP_DATA variable in VPS environment (inheritance issue)
- **Solution**: Host-level docker_env_vars override (lines 146-148 in inventory.yml)

## What We Fixed

### 1. Root Cause Analysis ✅
- Authentik containers failing with `PermissionError: [Errno 13] Permission denied: '/media/public'`
- Issue was missing `APP_DATA` variable in VPS environment
- VPS `docker_env_vars.common` only had `PGID: "999"` but no inheritance from global vars

### 2. Elegant Solution Found ✅  
- **Original Problem**: Group-level `docker_env_vars` completely replaced global vars
- **Failed Attempt**: Moving to group level (`gateway.docker_env_vars`) - invalid Ansible syntax
- **Working Solution**: Host-level override (`gateway-vps.docker_env_vars`) - proper Ansible precedence

### 3. Current Configuration ✅
**Location**: `ansible/inventory.yml` lines 146-148
```yaml
gateway:
  hosts:
    gateway-vps:
      # ... normal host config  
      docker_env_vars:
        common:
          PGID: "999" # VPS uses docker_gid: 999, different from homelab
```

## Expected Behavior
- **Inheritance**: VPS should get ALL global `docker_env_vars.common` variables
- **Override**: Plus the VPS-specific `PGID: "999"`
- **Result**: Authentik gets `APP_DATA=/opt/docker/appdata` + proper permissions

## Next Steps (When Resuming)
1. **Test deployment**: Run `ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml`
2. **Verify .env file**: Check `/opt/docker/compose/authentik/.env` has APP_DATA
3. **Check Authentik status**: Ensure containers start without permission errors
4. **Test external access**: Verify auth.nobasura.org works
5. **Run test suite**: `ansible-playbook tests/suites/gateway_vps_test_suite.yml`

## Technical Context
- **Authentik compose**: Removed `user: "1001:106"` overrides (reverted to defaults)
- **Container user**: Running as default 1000:1000 (working configuration)
- **File ownership**: Directories will be created with correct ownership
- **Security**: No compromise - just proper variable inheritance

## Files Changed
- `ansible/inventory.yml`: Moved docker_env_vars to host level (lines 146-148)
- `ansible/files/gateway-vps/authentik/compose.yml`: Removed user overrides

**Status**: Ready for testing - host-level variable solution should work!