---
title: Tunnel Infrastructure Automation Resolution - June 19, 2025
type: note
permalink: archive/tunnel-infrastructure-automation-resolution-june-19-2025
---

# Tunnel Infrastructure Automation Resolution - June 19, 2025

**Status**: ✅ **RESOLVED** | **Priority**: **CRITICAL**  
**Tags**: production-issue, tunnel-automation, pangolin, newt, docker-role

## Issue Summary

**Problem**: Media site showing "Offline" in Pangolin UI despite working credentials and manual fixes from previous day.

**Root Cause**: Complete absence of newt tunnel container automation - containers were deployed manually and not included in Docker role automation.

**Impact**: Production infrastructure showing degraded status, potential service interruption for external users.

## Resolution Implementation

### 1. **Automation Design**
- **Conditional Deployment**: Explicit `deploy_tunnels=true` flag required for tunnel changes
- **Safety Mechanisms**: Conservative defaults prevent accidental tunnel disruption
- **Discovery Pattern**: Elegant file resolution with host-specific overrides

### 2. **Technical Implementation**

**Files Created/Modified**:
- `ansible/files/common/newt/compose.yml` - Common tunnel service template
- `ansible/roles/docker/tasks/main.yml` - Conditional tunnel deployment
- `ansible/roles/docker/tasks/deploy_stack.yml` - Discovery-based file loading
- `ansible/inventory.yml` - Credentials and environment variables for all VMs

**Key Patterns**:
```yaml
# Safe conditional deployment
- name: Deploying newt tunnel stack
  include_tasks: deploy_stack.yml
  when: docker_deploy and deploy_tunnels | default(false) and pangolin_newt_enabled | default(false)
  vars:
    cur_stack: newt

# Discovery-based file resolution
- name: Copy stack files {{ cur_stack }}
  copy:
    src: "{{ item }}"
    dest: "{{ docker_compose_dir }}"
  with_first_found:
    - "{{ inventory_hostname }}/{{ cur_stack }}"
    - "common/{{ cur_stack }}"
```

### 3. **Environment Variable Management**
- **Hierarchy**: Global → Stack → Host-global → Host-stack variables
- **Credentials**: 1Password integration maintained
- **Template Avoidance**: Used .env pattern to prevent Ansible/Docker conflicts

### 4. **Container Standardization**
```yaml
services:
  newt:
    extends:
      file: ../common.yml
      service: base
    image: fosrl/newt:1.2.1
    container_name: newt
    network_mode: host
    environment:
      - NEWT_ID=${NEWT_ID}
      - NEWT_SECRET=${NEWT_SECRET}
      - PANGOLIN_ENDPOINT=${PANGOLIN_ENDPOINT}
    healthcheck:
      test: ["CMD-SHELL", "wget --quiet --spider --timeout=10 --tries=1 https://pangolin.nobasura.org || exit 1"]
    labels:
      - "deunhealth.restart.on.unhealthy=true"
```

## Deployment and Validation

### **Deployment Success**
```bash
# Safe deployment command used
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml -e deploy_tunnels=true --limit media-vm
```

### **Container Health** ✅
```
CONTAINER ID   IMAGE              STATUS
b164a00a3bc9   fosrl/newt:1.2.1   Up 3 minutes (healthy)
```

### **Tunnel Connectivity** ✅
- **TCP Proxies**: 8 services actively proxied
- **Latency**: Consistent 3-4ms to Tailscale coordinator
- **Services**: Radarr, Readarr, Bazarr, qBittorrent, Jellyfin, Overseerr, Homepage, Jackett

### **Production Status** ✅
- **Pangolin UI**: Media site "Offline" → "Online"
- **External Access**: All services accessible via tunnel
- **Credentials**: Verified correct deployment from 1Password

## Benefits Achieved

1. **Production Stability**: Eliminated need for manual tunnel fixes
2. **Infrastructure Safety**: Explicit flags prevent accidental tunnel disruption
3. **Code Consistency**: Follows existing Docker role patterns and standards
4. **Maintainability**: Declarative configuration in inventory
5. **Security**: 1Password credential integration maintained
6. **Monitoring**: Health checks and auto-restart capabilities

## Deployment Usage Patterns

```bash
# Safe application deployment (tunnels unchanged)
ansible-playbook deploy_docker.yml

# Explicit tunnel deployment
ansible-playbook deploy_docker.yml -e deploy_tunnels=true

# Targeted VM with tunnels
ansible-playbook deploy_docker.yml -e deploy_tunnels=true --limit media-vm

# Multiple VMs with tunnels
ansible-playbook deploy_docker.yml -e deploy_tunnels=true --limit "apps-vm,media-vm,obs-vm"
```

## Documentation Created

- **Implementation Details**: `memory://decisions/newt-tunnel-automation-implementation`
- **Design Patterns**: `memory://patterns/tunnel-infrastructure-automation-patterns`
- **Root Cause Analysis**: `decisions/Media Site Offline Root Cause Analysis - June 19, 2025.md`

## Completion Requirements Met

- ✅ **Production Issue Resolved**: Media site status restored from "Offline" to "Online"
- ✅ **Automation Implemented**: No more manual tunnel deployment needed
- ✅ **Safety Mechanisms**: Explicit flags prevent accidental disruption
- ✅ **Code Standards**: Follows existing Docker role patterns
- ✅ **Documentation**: Comprehensive patterns and implementation guides
- ✅ **Monitoring**: Health checks and auto-recovery operational

## Related Tasks

- **Follow-up**: Test suite validation (pending)
- **Documentation**: Memory system updates (completed)
- **Code Quality**: Git commit with comprehensive changes (pending)

**Resolution Time**: ~2 hours from issue identification to production validation  
**Impact**: Zero downtime deployment with immediate service restoration