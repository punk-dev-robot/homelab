---
title: OAuth Client Credentials Pattern for 1Password
type: note
permalink: patterns/oauth-client-credentials-pattern-for-1-password
---

# OAuth Client Credentials Pattern for 1Password

## Standard Pattern for OAuth Client Storage

When storing OAuth client credentials in 1Password for homelab services, use this consistent pattern:

### 1Password Item Structure
- **Item Name**: `{SERVICE_NAME}_OAUTH_CLIENT` (e.g., `KARAKEEP_OAUTH_CLIENT`)
- **Username Field**: Contains the OAuth Client ID
- **Password Field**: Contains the OAuth Client Secret

### Ansible Variable Lookup Pattern
```yaml
# For Client ID - use username field
oauth_client_id: "{{ lookup('community.general.onepassword', '{SERVICE_NAME}_OAUTH_CLIENT', field='username', vault='Homelab') }}"

# For Client Secret - use password field (default)
oauth_client_secret: "{{ lookup('community.general.onepassword', '{SERVICE_NAME}_OAUTH_CLIENT', vault='Homelab') }}"
```

### Example: Karakeep Configuration
```yaml
# 1Password item: KARAKEEP_OAUTH_CLIENT
# Username: karakeep (OAuth Client ID)
# Password: <generated-secret> (OAuth Client Secret)

# Ansible variables:
karakeep_oauth_client_id: "{{ lookup('community.general.onepassword', 'KARAKEEP_OAUTH_CLIENT', field='username', vault='Homelab') }}"
karakeep_oauth_client_secret: "{{ lookup('community.general.onepassword', 'KARAKEEP_OAUTH_CLIENT', vault='Homelab') }}"
```

## Benefits of This Pattern
1. **Consistency**: All OAuth credentials follow same structure
2. **Simplicity**: One 1Password item per service OAuth config
3. **Security**: Credentials grouped logically, easy to rotate
4. **Ansible-friendly**: Clean variable lookup syntax

## Implementation Notes
- Use this pattern for all new OAuth integrations
- Update existing inconsistent patterns during maintenance
- Document service-specific OAuth requirements alongside this pattern