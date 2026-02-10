---
title: Media Site Offline Root Cause Analysis - June 19, 2025
type: note
permalink: decisions/media-site-offline-root-cause-analysis-june-19-2025
---

# Media Site Offline Root Cause Analysis - June 19, 2025

## 🔍 Investigation Summary

**Issue**: Media site shows as "Offline" in Pangolin UI while apps and obs sites are "Online"

## 🕵️ Root Cause Discovery

### Key Findings

1. **✅ Credentials are NOT the issue**
   - 1Password credentials match exactly yesterday's working manual fix
   - ID: `<redacted>`
   - Secret: `<redacted>`

2. **❌ Newt tunnel container missing entirely**
   - `docker ps` on media-vm shows no newt container running
   - No newt-related files found in `/opt/docker/compose/`
   - Media-vm has 7 containers but newt is not among them

3. **❌ Pangolin role not being deployed**
   - Inventory defines `pangolin_newt_enabled: true` for all VMs
   - Pangolin role exists in `/ansible/roles/pangolin/`
   - **Critical Gap**: Pangolin role is NOT called in any deployment playbook
   - `deploy_docker.yml` only calls the `docker` role
   - Newt tunnel deployment is completely missing from automation

### Detailed Evidence

**Pangolin UI Status**:
- Apps: ✅ Online (female-greater-naked-tailed-armadillo)
- Media: ❌ Offline (trivial-san-diego-pocket-mouse) 
- Obs: ✅ Online (obedient-african-striped-weasel)

**Media-VM Container Status**:
```bash
# Running containers (7 total):
- dozzle-agent
- docker-gc  
- watchtower
- jellystat
- jellystat-db
- stash
- notifiarr
- recyclarr

# Missing: newt tunnel container
```

**Configuration Analysis**:
- Inventory has `pangolin_newt_enabled: true` for media-vm
- Ansible roles directory contains complete pangolin role
- No playbook actually calls the pangolin role for tunnel deployment

## 🚨 Conclusion

**The media site is offline because newt tunnel automation is fundamentally broken:**

1. **Manual fix yesterday worked** because credentials were applied directly to a manually configured newt container
2. **Current failure** is because no newt container exists at all - the pangolin role that should deploy tunnels is never called
3. **Apps and obs working** suggests they might have pre-existing tunnel configurations or different deployment method

## 🔧 Required Fix

**Immediate**: Deploy newt tunnel container to media-vm
**Long-term**: Fix ansible automation to properly deploy pangolin tunnels

## 📋 Next Steps

1. Investigate how apps and obs tunnels are currently deployed (if at all)
2. Fix pangolin role integration in deployment playbooks
3. Deploy newt tunnel to media-vm  
4. Validate tunnel connectivity
5. Ensure automation prevents future regression

## 🎯 Impact

- **Critical**: External access to media services (Jellyfin, Servarr) broken
- **Infrastructure**: Tunnel automation incomplete, risk of similar failures
- **Recovery Time**: Manual deployment possible, automation fix needed for permanence

---

This analysis shows our tunnel infrastructure is more fragile than expected. The successful yesterday recovery was masking a deeper automation gap.