---
title: VPS Security Review - Authentik Permission Fix June 18, 2025
type: note
permalink: decisions/vps-security-review-authentik-permission-fix-june-18-2025
---

# VPS Security Review - Authentik Permission Fix June 18, 2025

## Current Situation
- **Issue**: Authentik containers failing due to UID/GID mismatch
- **Root Cause**: Container hardcoded to UID/GID 1000, but VPS infrastructure uses ubuntu:docker (1001:106)
- **Security Concern**: We made changes that could affect authentication security

## Changes Made
1. **Container Configuration**: Added `user: "1001:106"` to Authentik server and worker
2. **Directory Ownership**: Set `/authentik/media` and `/opt/docker/appdata/authentik` to ubuntu:docker
3. **Certs Security**: Ensured `/authentik/certs` remains root:root with 700 permissions

## Security Review Checklist

### ✅ Container User Configuration
- **Good**: Using explicit UID/GID instead of privileged defaults
- **Good**: Matching infrastructure user (ubuntu) instead of container default
- **Security**: Non-root user reduces container privilege escalation risk

### ⚠️ Directory Permissions (NEEDS VERIFICATION)
- **Media Directory**: `/authentik/media` - should be ubuntu:docker 755 (readable but not world-writable)
- **Appdata Directory**: `/opt/docker/appdata/authentik` - should be ubuntu:docker 750 (group readable only)
- **Certs Directory**: `/authentik/certs` - MUST remain root:root 700 (no access except root)

### 🔒 Critical Security Requirements
1. **Certs Protection**: Certificate files must remain root-only accessible
2. **Database Access**: Ensure PostgreSQL data is not exposed
3. **Media Restrictions**: Authentik media should not be world-readable
4. **Log Security**: Ensure logs don't expose sensitive information

## Action Plan
1. **Verify Current Permissions**: Check all directory permissions on VPS
2. **Secure Media Directory**: Ensure proper 750 permissions (not 755)
3. **Validate Certs Security**: Confirm certificates remain protected
4. **Test Authentication**: Verify Authentik works without security compromise
5. **Run Security Tests**: Execute full security validation suite

## Security Commands to Execute
```bash
# Check current permissions
ls -la /authentik/
ls -la /opt/docker/appdata/authentik/

# Secure media directory (group access only)
sudo chmod 750 /authentik/media
sudo chmod 750 /opt/docker/appdata/authentik

# Verify certs remain secure
sudo chmod 700 /authentik/certs
sudo chown root:root /authentik/certs
```

## Validation Required
- [ ] Directory permissions properly restricted
- [ ] Certificates remain root-only
- [ ] Container starts with correct non-root user
- [ ] Authentication works without privilege escalation
- [ ] No world-readable sensitive files