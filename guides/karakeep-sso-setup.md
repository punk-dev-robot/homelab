# Karakeep SSO Setup with Authentik

## Overview
Setting up Authentik SSO for karakeep.nobasura.org with auto-provisioning and proper group mappings.

## Step 1: Create OAuth2 Provider in Authentik

1. **Access Authentik Admin**: https://auth.nobasura.org/if/admin/
2. **Create Provider**:
   - Navigate to Applications → Providers → Create
   - Select "OAuth2/OpenID Provider"
   - Configure:
     ```
     Name: Karakeep OAuth2
     Authentication flow: default-authentication-flow
     Authorization flow: default-provider-authorization-implicit-consent
     
     Protocol Settings:
     - Client type: Confidential
     - Client ID: karakeep (or auto-generated)
     - Client Secret: [Generate secure secret]
     - Redirect URIs: 
       https://karakeep.nobasura.org/api/auth/callback/authentik
       https://karakeep.nobasura.org/api/auth/callback
     
     Scopes:
     - openid
     - email
     - profile
     - groups (custom scope for group mapping)
     
     Subject mode: Based on the User's Email
     Include claims in id_token: ✓
     
     Signing Key: authentik Self-signed Certificate
     ```

## Step 2: Create Application in Authentik

1. **Create Application**:
   - Navigate to Applications → Applications → Create
   - Configure:
     ```
     Name: Karakeep
     Slug: karakeep
     Provider: Karakeep OAuth2
     Policy engine mode: any
     
     UI Settings:
     - Launch URL: https://karakeep.nobasura.org
     - Icon: [Optional - Karakeep logo]
     ```

## Step 3: Configure Group Mappings for Auto-Provisioning

1. **Create Property Mappings**:
   - Navigate to Customization → Property Mappings → Create
   - Create "Karakeep Groups" mapping:
     ```python
     # Expression for groups claim
     return {
         "groups": [group.name for group in user.ak_groups.all()],
         "is_admin": any(group.name in ["karakeep-admins", "nobasura-admin"] for group in user.ak_groups.all()),
         "organization": "nobasura"
     }
     ```

2. **Add to Provider Scopes**:
   - Edit the Karakeep OAuth2 provider
   - Under "Scopes", add the custom groups mapping

## Step 4: Configure Karakeep Environment Variables

Based on the Karakeep documentation, add these environment variables:

```yaml
# OAuth2/OIDC Configuration
OAUTH_WELLKNOWN_URL: "https://auth.nobasura.org/application/o/karakeep/.well-known/openid-configuration"
OAUTH_CLIENT_ID: "karakeep"  # From Step 1
OAUTH_CLIENT_SECRET: "[YOUR_CLIENT_SECRET]"  # From Step 1
OAUTH_SCOPE: "openid email profile"  # Add more scopes if needed
OAUTH_PROVIDER_NAME: "Authentik"  # Shows as "Sign in with Authentik"

# Optional: Allow linking existing accounts (only if you trust Authentik)
OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING: "true"  # Default is false

# Optional: Increase timeout if needed
OAUTH_TIMEOUT: "3500"  # Default is 3500ms
```

## Step 5: Create Groups in Authentik

1. **Create Groups**:
   - Navigate to Directory → Groups → Create
   - Create:
     - `karakeep-admins` - Full admin access to Karakeep
     - `karakeep-editors` - Editor access
     - `karakeep-viewers` - Read-only access

2. **Assign Users**:
   - Add yourself to `karakeep-admins` group
   - Add other users as needed

## Step 6: Update Karakeep Docker Compose

Add the environment variables to your Karakeep deployment:

```yaml
services:
  karakeep:
    environment:
      # Existing config...
      
      # SSO Configuration
      OAUTH_WELLKNOWN_URL: "https://auth.nobasura.org/application/o/karakeep/.well-known/openid-configuration"
      OAUTH_CLIENT_ID: "${KARAKEEP_OAUTH_CLIENT_ID}"
      OAUTH_CLIENT_SECRET: "${KARAKEEP_OAUTH_CLIENT_SECRET}"
      OAUTH_SCOPE: "openid email profile"
      OAUTH_PROVIDER_NAME: "Authentik"
      OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING: "true"
      OAUTH_TIMEOUT: "3500"
```

## Step 7: Test the Integration

1. **Clear browser cookies** for karakeep.nobasura.org
2. **Navigate to**: https://karakeep.nobasura.org
3. **Click "Sign in with Authentik"** (or similar SSO button)
4. **Authenticate** with your Authentik credentials
5. **Verify**:
   - You're redirected back to Karakeep
   - Your user is auto-provisioned
   - Admin rights are granted if you're in the admin group

## Troubleshooting

### Common Issues:

1. **Redirect URI Mismatch**:
   - Ensure the callback URL in Authentik matches exactly
   - Check for trailing slashes

2. **Groups Not Syncing**:
   - Verify the groups scope is included
   - Check the property mapping expression

3. **User Not Auto-Provisioned**:
   - Ensure `AUTH_AUTHENTIK_ALLOW_SIGNUP` is true
   - Check Authentik logs for errors

### Debug URLs:
- Authentik OIDC Discovery: https://auth.nobasura.org/application/o/karakeep/.well-known/openid-configuration
- Authentik Admin: https://auth.nobasura.org/if/admin/
- Test Authorization: https://auth.nobasura.org/application/o/authorize/karakeep/

## Next Steps

1. Set up automated user provisioning workflows
2. Configure SCIM if Karakeep supports it
3. Add more granular permission mappings
4. Set up SSO for other services