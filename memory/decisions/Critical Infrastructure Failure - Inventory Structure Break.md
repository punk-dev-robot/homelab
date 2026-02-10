---
title: Critical Infrastructure Failure - Inventory Structure Break
type: note
permalink: decisions/critical-infrastructure-failure-inventory-structure-break
---

# Critical Infrastructure Failure - Inventory Structure Break

## Incident Date: June 18, 2025

### Root Cause
Broken Ansible inventory structure where `media-vm` and `obs-vm` were incorrectly nested inside the `vars:` section instead of `hosts:`

### Impact Assessment

#### 🔴 CONFIRMED DAMAGE
1. **Jellyfin Data Loss** (media-vm)
   - Complete loss of configuration, users, libraries
   - No backups for 18 days
   - Fresh initialization occurred

2. **VM Connectivity Lost**
   - apps-vm: UNREACHABLE (SSH timeout)
   - media-vm: UNREACHABLE (SSH timeout)  
   - obs-vm: UNREACHABLE (SSH timeout)
   - gateway-vps: OK ✅

#### 🟡 POTENTIAL DAMAGE (Unknown Status)

**apps-vm Services:**
- AI services (LiteLLM, etc.)
- Tools (Karakeep with SSO, Atuin, etc.)
- Databases (Neo4j)

**media-vm Services:**
- Servarr stack (Sonarr, Radarr, etc.)
- Media management tools
- Download clients

**obs-vm Services:**
- Grafana monitoring
- Graylog logging
- TICK stack metrics

### Inventory Structure Error

**Broken (Committed):**
```yaml
docker:
  hosts:
    apps-vm: ...
  vars:
    docker_data_dir: /opt/docker/appdata
    media-vm:  # ❌ WRONG - Inside vars!
      ansible_host: media.lan
    obs-vm:    # ❌ WRONG - Inside vars!
      ansible_host: obs.lan
```

**Fixed (Uncommitted):**
```yaml
docker:
  hosts:
    apps-vm: ...
    media-vm: ...  # ✅ Correct location
    obs-vm: ...    # ✅ Correct location
  vars:
    docker_data_dir: /opt/docker/appdata
```

### Timeline
1. Inventory structure was broken in a previous commit
2. Deployment was run with broken inventory
3. Ansible couldn't properly recognize hosts or resolve variables
4. Services were reinitialized with wrong/empty paths
5. Data loss occurred
6. Inventory was fixed (current uncommitted changes)
7. VMs became unreachable

### Critical Questions
1. Why are all VMs unreachable via SSH?
2. Did the deployment break networking configuration?
3. Are the VMs still running in Proxmox?
4. What's the extent of data loss beyond Jellyfin?

### Recovery Priority
1. **Restore VM connectivity** - Can't assess damage without access
2. **Check VM status in Proxmox** - Verify VMs are running
3. **Assess data loss** - Once connected, check all services
4. **Restore from backups** - If any exist
5. **Manual rebuild** - For services without backups

### Lessons Learned
1. Always validate inventory syntax before deployment
2. Implement pre-deployment checks
3. Ensure backup systems are monitored and working
4. Create snapshots before configuration changes
5. Test deployments in staging first

---

*This represents a critical infrastructure failure requiring immediate attention*