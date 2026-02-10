---
title: Jellyfin SSO Troubleshooting Resolution
type: note
permalink: decisions/jellyfin-sso-troubleshooting-resolution
---

# Jellyfin SSO Troubleshooting Resolution

## Issue Identified
The Jellyfin SSO integration was not working despite being configured because of a **provider name mismatch** between Jellyfin and Authentik.

## Root Cause
- SSO-Auth plugin (3.5.2.4) was installed and loaded correctly
- OIDC endpoint was accessible and returning valid configuration
- Network connectivity between Jellyfin and Authentik was working
- **The provider name in Jellyfin didn't match the expected value**

## Solution Applied
1. **Corrected provider name** in Jellyfin SSO plugin configuration
2. **Restarted Jellyfin container** to apply SSO configuration changes
   ```bash
   ansible -i ansible/inventory.yml media-vm -a "docker restart jellyfin"
   ```

## Key Insight
The SSO-Auth plugin requires an exact match between:
- Provider name configured in Jellyfin
- Provider name expected by Authentik application
- Jellyfin requires a restart after SSO configuration changes

## Status
- ✅ Plugin installed and loaded: SSO-Auth 3.5.2.4
- ✅ Network connectivity: Jellyfin ↔ Authentik working
- ✅ OIDC endpoint: Returning valid configuration
- ✅ Provider name: Corrected and container restarted
- 🔄 Testing: End-to-end SSO authentication flow

## Next Steps
Test the complete SSO authentication flow:
1. Access Jellyfin login page
2. Look for SSO/OIDC login option
3. Test authentication redirect to Authentik
4. Verify successful login and session creation

## Related Files
- Jellyfin config: `/config/data/plugins/SSO Authentication_3.5.2.4/`
- Authentik OIDC: `https://auth.nobasura.org/application/o/jellyfin/`