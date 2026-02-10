---
title: Karakeep SSO Configuration Progress
type: note
permalink: decisions/karakeep-sso-configuration-progress
---

# Karakeep SSO Configuration Progress

## Current Status
- **Date**: June 18, 2025
- **Branch**: authentik (feat worktree)
- **Phase**: Configuring Karakeep SSO with Authentik

## What Was Completed

### 1. Configuration Files Updated
- **karakeep.yml**: Added OAuth environment variable placeholders
- **inventory.yml**: Added OAuth configuration with 1Password lookups
- **Created KARAKEEP_SSO_SETUP.md**: Complete setup guide

### 2. Correct Environment Variables Identified
From Karakeep documentation (https://docs.karakeep.app/configuration):
```yaml
OAUTH_WELLKNOWN_URL: "https://auth.nobasura.org/application/o/karakeep/.well-known/openid-configuration"
OAUTH_CLIENT_ID: "{{ lookup('community.general.onepassword', 'KARAKEEP_OAUTH_CLIENT_ID', vault='Homelab') }}"
OAUTH_CLIENT_SECRET: "{{ lookup('community.general.onepassword', 'KARAKEEP_OAUTH_CLIENT_SECRET', vault='Homelab') }}"
OAUTH_SCOPE: "openid email profile"
OAUTH_PROVIDER_NAME: "Authentik"
OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING: "true"  # Already set
OAUTH_TIMEOUT: "3500"
```

## Next Steps When Resuming

### 1. Create OAuth2 Provider in Authentik
- Navigate to https://auth.nobasura.org/if/admin/
- Create OAuth2/OpenID Provider with:
  - Client type: Confidential
  - Client ID: `karakeep`
  - Client Secret: Generate secure one
  - Redirect URIs: `https://karakeep.nobasura.org/api/auth/callback/custom`
  - Scopes: `openid email profile`
  - Subject mode: Based on the User's Email
  - Signing Key: authentik Self-signed Certificate

### 2. Create Application in Authentik
- Name: Karakeep
- Slug: karakeep
- Provider: Link to OAuth2 provider created above
- Launch URL: https://karakeep.nobasura.org

### 3. Add Credentials to 1Password
- Add `KARAKEEP_OAUTH_CLIENT_ID` with the client ID from Authentik
- Add `KARAKEEP_OAUTH_CLIENT_SECRET` with the client secret from Authentik

### 4. Deploy Updated Configuration
```bash
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml --limit apps-vm --tags tools
```

### 5. Test SSO Integration
- Navigate to https://karakeep.nobasura.org
- Click "Sign in with Authentik"
- Verify authentication flow works

## Files Modified
1. `ansible/files/apps-vm/tools/karakeep.yml` - Added OAuth env vars
2. `ansible/inventory.yml` - Added OAuth configuration section
3. `KARAKEEP_SSO_SETUP.md` - Complete setup documentation

## Important Notes
- Karakeep uses standard OIDC configuration
- The callback URL must be: `/api/auth/callback/custom`
- `OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING` is already set to true
- No custom scopes or group mappings needed initially

## Commands to Continue
```bash
# Switch to correct memory project
mcp__basic-memory__switch_project("lab-feat")

# Read this note to continue
mcp__basic-memory__read_note("decisions/karakeep-sso-configuration-progress")
```

## Updated Configuration (June 18, 2025)

### Fixed OAuth Credentials Pattern
Updated `ansible/inventory.yml` to use new standardized pattern:
```yaml
OAUTH_CLIENT_ID: "{{ lookup('community.general.onepassword', 'KARAKEEP_OAUTH_CLIENT', field='username', vault='Homelab') }}"
OAUTH_CLIENT_SECRET: "{{ lookup('community.general.onepassword', 'KARAKEEP_OAUTH_CLIENT', vault='Homelab') }}"
```

This matches the new OAuth client credentials pattern saved to memory: `patterns/oauth-client-credentials-pattern-for-1-password`

### Updated Instructions for User
1. **In Authentik Admin** (https://auth.nobasura.org/if/admin/):
   - Create OAuth2 Provider: Client ID `karakeep`, generate secure secret
   - Create Application: Link to provider, slug `karakeep`

2. **In 1Password** (Homelab vault):
   - Create item: `KARAKEEP_OAUTH_CLIENT`
   - Username: `karakeep` (Client ID)
   - Password: Generated client secret from Authentik

3. **Deploy**: `ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml --limit apps-vm --tags tools`

Configuration files are now ready for deployment once OAuth provider is created in Authentik.
## Session 2: OAuth Implementation Debugging (June 18, 2025)

### Current Status: NEXTAUTH_URL_INTERNAL Fix Applied
- **Time**: 09:15 UTC
- **Issue**: Persistent "User settings not found" error (digest: 4237581454)
- **Root Cause Identified**: `NEXTAUTH_URL_INTERNAL=http://localhost:3000` instead of `http://karakeep:3000`

### Key Findings This Session

#### 1. Environment Variable Analysis
**Correct Variables in Container:**
- ✅ `DISABLE_PASSWORD_AUTH=true`
- ✅ `DISABLE_SIGNUPS=false` 
- ✅ `LOG_LEVEL=debug`
- ✅ All OAuth variables present and correct
- ❌ `NEXTAUTH_URL_INTERNAL=http://localhost:3000` (WRONG)

#### 2. Database Initialization Discovery
- Issue: OAuth-only mode (`DISABLE_PASSWORD_AUTH=true`) prevents initial page load
- Solution: Temporarily enabled password auth, created initial user, re-enabled OAuth-only
- Database now properly initialized with user schema

#### 3. Critical OAuth Pattern Established
**1Password OAuth Credentials Pattern (Standardized):**
```
Item Name: {SERVICE_NAME}_OAUTH_CLIENT
Username: OAuth Client ID  
Password: OAuth Client Secret
```

**Ansible Lookup Pattern:**
```yaml
oauth_client_id: "{{ lookup('community.general.onepassword', 'SERVICE_OAUTH_CLIENT', field='username', vault='Homelab') }}"
oauth_client_secret: "{{ lookup('community.general.onepassword', 'SERVICE_OAUTH_CLIENT', vault='Homelab') }}"
```

### Applied Fixes This Session

#### 1. OAuth Credentials Pattern (COMPLETED)
- Updated `ansible/inventory.yml` to use standardized 1Password pattern
- Pattern documented in `memory://patterns/oauth-client-credentials-pattern-for-1-password`

#### 2. NEXTAUTH_URL_INTERNAL Fix (IN PROGRESS)
- **File**: `ansible/files/apps-vm/tools/karakeep.yml`
- **Change**: Added `NEXTAUTH_URL_INTERNAL: http://karakeep:3000`
- **Status**: Deployment in progress (timing out but continuing)

### Current Deployment Status
- Ansible deployment running but timing out (normal for large deployments)
- Tools stack being updated with corrected NEXTAUTH_URL_INTERNAL
- Expected: Fixed OAuth callback handling

### Next Steps When Resuming
1. **Verify deployment completed** - check container environment has `NEXTAUTH_URL_INTERNAL=http://karakeep:3000`
2. **Test OAuth flow** - clear browser cookies and attempt login at https://karakeep.nobasura.org
3. **Monitor debug logs** during OAuth attempt for detailed callback processing
4. **If successful**: Document completion and disable debug logging

### Configuration Files Status
- ✅ `ansible/inventory.yml` - OAuth credentials pattern updated
- ✅ `ansible/files/apps-vm/tools/karakeep.yml` - NEXTAUTH_URL_INTERNAL added, debug logging enabled
- ✅ Authentik OAuth2 provider configured (Client ID: karakeep)
- ✅ 1Password credentials stored as `KARAKEEP_OAUTH_CLIENT`

### Integration Readiness
All OAuth infrastructure properly configured:
- Authentik provider/application created
- Karakeep environment variables correct
- Database initialized
- Internal URL fix applied

**Status**: Ready for final OAuth testing once deployment completes.

## Session 3: OAuth Bug Identified - Waiting for Fix (June 18, 2025)

### Issue Resolution: Known Upstream Bug
- **Time**: 09:25 UTC
- **Root Cause**: GitHub issue #1583 - OAuth user creation broken in Karakeep v0.25.0
- **Status**: Blocked by upstream bug, waiting for v0.26.0 release

### Key Findings

#### 1. OAuth Infrastructure Working Correctly
- ✅ Authentik OAuth2 provider configured properly
- ✅ Karakeep environment variables correct 
- ✅ `NEXTAUTH_URL_INTERNAL=http://karakeep:3000` applied successfully
- ✅ OAuth authentication flow reaches Karakeep

#### 2. Upstream Bug Confirmed
**GitHub Issue**: https://github.com/karakeep-app/karakeep/issues/1583
- **Bug**: User settings table not created during OAuth user creation
- **Error**: "User settings not found" (digest: 4237581454) 
- **Affected Version**: v0.25.0
- **Fix Scheduled**: v0.26.0 release
- **Priority**: High priority, status approved

#### 3. Official Workaround Rejected
- Manual user creation defeats automatic onboarding purpose
- Decision: Wait for proper fix in v0.26.0

### Configuration Status
- **OAuth Provider**: Fully configured in Authentik
- **Environment Variables**: All correct, including NEXTAUTH_URL_INTERNAL fix
- **Authentication Mode**: OAuth-only (`DISABLE_PASSWORD_AUTH=true`)
- **Database**: Initialized with persistent volumes

### Next Steps
1. **Monitor Release**: Watch for Karakeep v0.26.0 release
2. **Update Version**: Change `KARAKEEP_VERSION` when available
3. **Test**: Verify automatic OAuth user creation after upgrade

### Files Status
- ✅ `ansible/inventory.yml` - OAuth credentials configured
- ✅ `ansible/files/apps-vm/tools/karakeep.yml` - Environment variables correct
- ✅ Authentik OAuth2 provider - Active and functional
- ✅ 1Password credentials - Stored as `KARAKEEP_OAUTH_CLIENT`

**Implementation Status**: OAuth infrastructure complete, blocked by upstream bug #1583