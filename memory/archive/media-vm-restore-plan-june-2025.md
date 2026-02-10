---
title: Media-VM Restore Plan - June 18, 2025
type: note
permalink: decisions/media-vm-restore-plan-june-18-2025
---

# Media-VM Restore Plan - June 18, 2025

## Summary
Complete media-vm restore from 18-day backup to recover lost Jellyfin and Servarr data, then reapply git changes.

## Git Work Preserved
**Commit**: `9452f76` - "Pre-restore commit: preserve inventory fix and SSO work"
**Tag**: `pre-restore-june18`

### Changes Saved:
1. **Critical inventory fix** - media-vm/obs-vm moved from vars to hosts section
2. **Jellyfin SSO integration** - Configuration for Authentik OIDC
3. **Documentation** - Infrastructure failure analysis and recovery procedures
4. **CrowdSec integration** - Container monitoring and protection setup

## Restore Procedure

### Step 1: VM Restore (User Action Required)
- Restore media-vm from 18-day-old backup using Proxmox
- This will revert entire VM to working state with all application data

### Step 2: Post-Restore Git Reapply
After VM is restored, reapply the saved changes:

```bash
# Navigate to project directory
cd /home/kuba/dev/lab/feat

# Verify the tagged commit exists
git show pre-restore-june18 --name-only

# Apply the inventory fix
git checkout pre-restore-june18 -- ansible/inventory.yml

# Apply Jellyfin configuration  
git checkout pre-restore-june18 -- ansible/files/media-vm/jelly/jellyfin.yml

# Test deployment with fixed inventory
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml --check

# Deploy if check passes
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml
```

### Step 3: Verification
1. **Test all services**: Jellyfin, Radarr, Sonarr, Prowlarr, etc.
2. **Verify data integrity**: Users, libraries, configurations
3. **Test SSO integration**: Authentik → Jellyfin authentication flow
4. **Set up automated backups**: Prevent future data loss

## Expected Recovery
- **Jellyfin**: All users, libraries, watch history (18 days ago)
- **Servarr Stack**: All configurations, quality profiles, indexers
- **Download Clients**: All settings and download history
- **Jellyseerr**: User accounts and request management

## Data Loss
- **Recent 18 days**: Watch history, new downloads, recent configuration changes
- **Fresh work**: Any manual changes made between backup and today

## Critical Success Factors
1. **Inventory structure fix**: Prevents future deployment issues
2. **SSO integration**: Maintains modern authentication
3. **Backup implementation**: Ensures this never happens again

## Post-Restore Actions
1. Update documentation with lessons learned
2. Implement automated daily backups
3. Create VM snapshots before major changes
4. Test restore procedures regularly

---

*This restore plan preserves all development work while recovering critical application data*