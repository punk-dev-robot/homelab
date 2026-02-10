---
title: Authentik Environment Variables Configuration Completed
type: note
permalink: decisions/authentik-environment-variables-configuration-completed
---

# Authentik Environment Variables Configuration Completed

## What Was Done

### 1. Environment Variable Configuration
- **Added authentik to stacks list** in `ansible/inventory.yml` gateway-vps section
- **Configured 1Password secrets** following existing patterns:
  - `AUTHENTIK_PG_PASS`: Database password  
  - `AUTHENTIK_SECRET_KEY`: Application secret key
  - `RESEND_API_KEY`: Email service (reused from Pangolin)

### 2. Volume Mount Patterns Applied
Following infrastructure rules:
- **APP_DATA mounts**: `${APP_DATA}/authentik/media:/media` and `${APP_DATA}/authentik/certs:/certs` (persistent data, auto-created)
- **Manual config**: `./config/custom-templates:/templates` (next to compose file for manual editing)

### 3. Deployment Configuration  
- **No special pre-tasks needed**: Docker will auto-create APP_DATA directories
- **Automatic deployment**: Authentik added to stacks list, will deploy with `deploy_vps.yml`
- **Directory structure**: Only `config/custom-templates/` kept next to compose file

## Files Modified

### ansible/inventory.yml
```yaml
stacks:
  - pangolin  
  - authentik

env_vars:
  authentik:
    AUTHENTIK_PG_PASS: "{{ lookup('community.general.onepassword', 'AUTHENTIK_PG_PASS', vault='Homelab') }}"
    AUTHENTIK_SECRET_KEY: "{{ lookup('community.general.onepassword', 'AUTHENTIK_SECRET_KEY', vault='Homelab') }}"
    RESEND_API_KEY: "{{ lookup('community.general.onepassword', 'RESEND_API_KEY', vault='Homelab') }}"
```

### ansible/files/gateway-vps/authentik/compose.yml
- Updated volume mounts to follow correct patterns
- APP_DATA for persistent data, local config for manual templates

## Next Steps
1. Deploy to gateway VPS with `ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml`
2. Test Authentik access at `auth.nobasura.org`
3. Configure OAuth2/OIDC integration per official docs

## Architecture Verified
- Static Traefik routes already configured (previous session)
- CrowdSec protection will apply automatically  
- Network connectivity to Pangolin stack configured
- Email configuration using existing Resend integration