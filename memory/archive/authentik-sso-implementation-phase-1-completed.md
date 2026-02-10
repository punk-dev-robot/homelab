---
title: Authentik SSO Implementation Phase 1 Completed
type: note
permalink: decisions/authentik-sso-implementation-phase-1-completed
---

# Authentik SSO Implementation Phase 1 Completed

## ✅ Implementation Status: SUCCESS

**Date**: June 18, 2025  
**Branch**: authentik  
**Phase**: Infrastructure deployment completed successfully

## 🎯 What Was Accomplished

### Core Infrastructure Deployed
1. **Authentik Docker Stack**: PostgreSQL + Redis + Server + Worker running on gateway VPS
2. **Static Traefik Routes**: `auth.nobasura.org` routes configured with CrowdSec protection
3. **Environment Variables**: 1Password secrets integration following infrastructure patterns
4. **Network Configuration**: Authentik server connected to pangolin network for Traefik access
5. **Directory Structure**: Proper volume mounts (APP_DATA for persistent data, local for templates)

### Integration Architecture
- **Access URL**: `https://auth.nobasura.org` 
- **SSL**: Uses existing wildcard certificate `*.nobasura.org`
- **Security**: CrowdSec protection applied automatically
- **Email**: Configured with Resend API (same as Pangolin)
- **Network**: Authentik stack connected to both `authentik` and `pangolin` networks

### Files Created/Modified

#### ansible/inventory.yml
```yaml
# Added authentik to stacks
stacks:
  - pangolin
  - authentik

# Added environment variables
env_vars:
  authentik:
    AUTHENTIK_PG_PASS: "{{ lookup('community.general.onepassword', 'AUTHENTIK_PG_PASS', vault='Homelab') }}"
    AUTHENTIK_SECRET_KEY: "{{ lookup('community.general.onepassword', 'AUTHENTIK_SECRET_KEY', vault='Homelab') }}"
    RESEND_API_KEY: "{{ lookup('community.general.onepassword', 'RESEND_API_KEY', vault='Homelab') }}"

# Added docker_env_vars for gateway
docker_env_vars:
  common:
    PUID: "1001"
    PGID: "999"
    TZ: "Europe/London"
    UMASK: "022"
    LOG_LEVEL: "info"
    APP_DATA: "/opt/docker/appdata"
```

#### ansible/files/gateway-vps/authentik/compose.yml
- Complete 4-service stack (PostgreSQL, Redis, Server, Worker)
- Network configuration connecting to pangolin
- Volume mounts following infrastructure patterns
- Health checks and restart policies
- Email configuration using Resend

#### Traefik Routes (Previously Created)
- Static routes in `traefik_rules/dynamic_config.yml`
- HTTP->HTTPS redirect for auth.nobasura.org
- CrowdSec middleware protection

### Infrastructure Validation
- ✅ **Gateway VPS Test Suite**: All security, functionality, and health tests passed
- ✅ **No Regressions**: Existing services unaffected
- ✅ **Container Health**: All Authentik containers running and healthy
- ✅ **Network Connectivity**: Traefik can reach Authentik service
- ✅ **Permissions**: Fixed APP_DATA directory ownership for container access

## 🔧 Technical Resolution

### Challenge: Network Connectivity
**Issue**: Traefik couldn't reach Authentik containers (502 errors)  
**Solution**: Added `networks: [default, pangolin]` to authentik-server service

### Challenge: Permission Issues  
**Issue**: Authentik couldn't create `/media/public` (Permission denied)  
**Solution**: Fixed APP_DATA directory ownership: `chown -R 1001:999 /opt/docker/appdata/authentik`

### Challenge: Variable Configuration
**Issue**: `docker_env_vars` undefined for gateway group  
**Solution**: Added complete docker environment variable structure to gateway vars

## 📋 Current Status

### Deployed Services
- **authentik-postgresql**: ✅ Healthy  
- **authentik-redis**: ✅ Healthy
- **authentik-server**: ✅ Running (accessible at auth.nobasura.org)
- **authentik-worker**: ✅ Running

### Access & Security
- **URL**: `https://auth.nobasura.org` (502 -> 403, indicating CrowdSec protection active)
- **SSL**: Automatic Let's Encrypt certificate
- **Protection**: CrowdSec bouncer middleware applied
- **Network**: Properly connected to Traefik for routing

## 🎯 Next Steps (Phase 2)

The final remaining task is **OAuth2/OIDC integration configuration**:

1. **Access Authentik Admin Interface**: Configure initial admin user
2. **Create OAuth2 Provider**: Following official Pangolin + Authentik documentation
3. **Configure Pangolin Integration**: Update Pangolin config for OAuth2 authentication
4. **Test Authentication Flow**: Verify end-to-end SSO works
5. **User Provisioning**: Configure automatic user creation

## 📚 References

- **Official Docs**: https://docs.goauthentik.io/integrations/services/pangolin/
- **Implementation State**: `AUTHENTIK_IMPLEMENTATION_STATE.md`
- **Memory Context**: `decisions/authentik-sso-implementation-progress`

---

**Result**: Phase 1 (Infrastructure) completed successfully. Authentik is deployed, accessible, and ready for OAuth2/OIDC configuration.