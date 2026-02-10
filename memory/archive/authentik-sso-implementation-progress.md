---
title: Authentik SSO Implementation Progress
type: note
permalink: decisions/authentik-sso-implementation-progress
---

# Authentik SSO Implementation Progress

## Current Status: Implementation Phase Started
- **Date**: June 18, 2025
- **Approved Plan**: Static Traefik route approach for auth.nobasura.org
- **Architecture**: Separate Authentik stack with network connectivity to Pangolin

## Implementation Strategy Approved

### DNS & Routing Solution
- **Access Method**: Static Traefik route to `auth.nobasura.org`
- **SSL**: Uses existing wildcard cert `*.nobasura.org`
- **Independence**: Auth service independent of Pangolin availability
- **Security**: CrowdSec protection automatically applied

### Technical Approach
1. **Static Route**: Add to `traefik_rules/dynamic_config.yml`
2. **Separate Stack**: `authentik/compose.yml` with network connectivity
3. **Official Integration**: Follow Authentik docs for OAuth2/OIDC with Pangolin

## Next Implementation Steps
1. Create Authentik compose stack
2. Add static Traefik routing configuration
3. Update deployment playbook
4. Configure OAuth2/OIDC integration
5. Test authentication flow

## Files to Implement
- `ansible/files/gateway-vps/authentik/compose.yml`
- `ansible/files/gateway-vps/authentik/config/` (templates)
- Update `ansible/files/gateway-vps/pangolin/traefik_rules/dynamic_config.yml`
- Update `ansible/deploy_vps.yml`
- Update `ansible/group_vars/gateway.yml`

## Integration Details (Official Docs)
- **Authorization URL**: `https://auth.nobasura.org/application/o/authorize/`
- **Token URL**: `https://auth.nobasura.org/application/o/token/`
- **Auto-provisioning**: Enabled for seamless user creation
- **Redirect URI**: To be configured after Pangolin setup

---

*Implementation in progress following approved architecture plan*