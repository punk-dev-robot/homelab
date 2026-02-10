---
title: Authentik SSO Integration Complete
type: note
permalink: decisions/authentik-sso-integration-complete
---

# Authentik SSO Integration - Successfully Completed

## 🎉 Implementation Status: COMPLETE

Successfully implemented and tested Authentik SSO integration with Pangolin on gateway VPS. OAuth2/OIDC authentication is now fully operational with proper auto-provisioning.

## ✅ Key Success Metrics

**Authentication Flow**: Users can login via Authentik OAuth2 and automatically get proper permissions
**Auto-Provisioning**: Working correctly with group-based role assignment
**Security**: JWS-signed tokens (no encryption), proper scopes configured
**Integration**: Seamless user experience with organization membership and Admin role assignment

## 🔧 Final Working Configuration

### Authentik OAuth2 Provider Settings

```yaml
# Core Settings
Name: "Pangolin OAuth2"
Authorization Flow: "default-provider-authorization-explicit-consent"
Client Type: Confidential
Client ID: xBkFfwClk8lXtDSChh2AIX8bC62mjYzFplZHw7DM
Redirect URI: https://pangolin.nobasura.org/auth/idp/1/oidc/callback

# Security Settings
Subject Mode: "Based on the User's Email"
Signing Key: "authentik Self-signed Certificate"
Encryption Key: [Empty - No encryption]
Include claims in id_token: ✅ Enabled

# Scopes (CRITICAL - includes custom groups scope)
Selected Scopes:
- authentik default OAuth Mapping: OpenID 'email'
- authentik default OAuth Mapping: OpenID 'openid' 
- authentik default OAuth Mapping: OpenID 'profile'
- Groups (Custom scope mapping)
```

### Custom Groups Scope Mapping (Essential)

```python
# Authentik Property Mapping
Name: Groups
Scope name: groups
Expression: return {"groups": [group.name for group in request.user.ak_groups.all()]}
```

### Pangolin Identity Provider Settings

```yaml
# OAuth2 Configuration
Token URL: http://authentik-server:9000/application/o/token/ (Internal Docker network)
Authorization URL: https://auth.nobasura.org/application/o/authorize/
User Info URL: https://auth.nobasura.org/application/o/userinfo/
Scopes: openid profile email groups

# Token Paths
Username Path: preferred_username
Email Path: email  
Name Path: name

# Auto-Provisioning (CRITICAL - Group-based)
Auto Provision Users: ✅ Enabled
Default Role Mapping: contains(groups, 'nobasura-admin') && 'Admin' || 'Member'
Default Organization Mapping: contains(groups, 'nobasura-admin')
```

## 🔍 Root Cause Analysis

**Original Issue**: OAuth users could authenticate but had no organization membership
**Root Cause**: Default mappings were using literal strings instead of JMESPath expressions evaluating JWT token claims
**Solution**: Configure Authentik to send groups in JWT tokens, then use JMESPath expressions to map groups to roles/organizations

## 📋 Critical Implementation Steps

1. **Configure Groups Scope**: Created custom scope mapping in Authentik to include groups in JWT tokens
2. **Group Assignment**: Added OAuth users to `nobasura-admin` group in Authentik
3. **JMESPath Mappings**: Used proper expressions to evaluate group membership:
   - Role: `contains(groups, 'nobasura-admin') && 'Admin' || 'Member'`
   - Organization: `contains(groups, 'nobasura-admin')`

## 🎯 Verification Logs

```bash
# Successful auto-provisioning logs
2025-06-18T07:21:07.962Z [debug]: Hydrated Org Mapping {"hydratedOrgMapping":" contains(groups, 'nobasura-admin')"}
2025-06-18T07:21:07.963Z [debug]: Extraced Org ID {"orgId":true}
2025-06-18T07:21:07.964Z [debug]: User org info {"userOrgInfo":[{"orgId":"nobasura","roleId":1}]}
```

**JWT Token Claims Received**:
```json
{
  "email": "kuba@nobasura.org",
  "groups": ["nobasura-admin", "nobasura-admin"],
  "name": "Punk Dev", 
  "preferred_username": "punkdev"
}
```

## 🚀 What's Working Now

- ✅ OAuth2/OIDC authentication via Authentik
- ✅ Automatic user creation on first login
- ✅ Group-based role assignment (Admin for nobasura-admin group members)
- ✅ Organization membership auto-provisioning
- ✅ Proper JWT token signing (no encryption issues)
- ✅ Internal Docker network communication
- ✅ User management through Authentik groups

## 📚 Related Documentation

- **Implementation**: `memory://archive/authentik-sso-implementation-complete`
- **Troubleshooting**: `memory://guides/troubleshooting-guide`
- **Security Config**: `memory://decisions/adr-sso-security-configuration`

## 🔮 Next Steps (Optional)

- Disable local authentication in Pangolin (user preference)
- Add additional groups for different role levels
- Configure session management and timeout policies
- Set up audit logging for authentication events

---

**Status**: ✅ COMPLETE - Production Ready
**Testing**: ✅ Verified with real user login and proper permissions
**Documentation**: ✅ Updated implementation state and memory