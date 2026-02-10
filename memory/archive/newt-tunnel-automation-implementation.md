---
title: Newt Tunnel Automation Implementation
type: note
permalink: decisions/newt-tunnel-automation-implementation
---

# Newt Tunnel Automation Implementation

## Overview

Comprehensive automation solution for Pangolin tunnel infrastructure using Ansible and Docker compose patterns. Resolves production issue where media site showed "Offline" in Pangolin UI due to missing tunnel automation.

## Key Design Decisions

### 1. Conditional Deployment with Safety Flags

**Problem**: Tunnel services are critical infrastructure - accidental recreation during routine deployments could cause outages.

**Solution**: Explicit safety flags with conservative defaults
```yaml
- name: Deploying newt tunnel stack
  include_tasks: deploy_stack.yml
  when: docker_deploy and deploy_tunnels | default(false) and pangolin_newt_enabled | default(false)
  vars:
    cur_stack: newt
```

**Benefits**:
- Prevents tunnel disruption during targeted stack deployments
- Requires explicit opt-in via `deploy_tunnels=true`
- Host-level toggle via `pangolin_newt_enabled`
- Separates tunnel lifecycle from application deployments

### 2. Discovery-Based Stack Loading

**Problem**: Previous approach used hardcoded logic for special cases, reducing maintainability.

**Solution**: Elegant file discovery with fallback hierarchy
```yaml
- name: Copy stack files {{ cur_stack }}
  copy:
    src: "{{ item }}"
    dest: "{{ docker_compose_dir }}"
    mode: "0664"
  with_first_found:
    - "{{ inventory_hostname }}/{{ cur_stack }}"
    - "common/{{ cur_stack }}"
```

**Benefits**:
- Host-specific overrides take precedence automatically
- Common templates provide consistent defaults
- Eliminates conditional logic and hardcoded paths
- Future-proof for new stack types

### 3. Environment Variable Management

**Problem**: Docker compose templating conflicts with Ansible template engine.

**Solution**: Leverage existing per-stack .env file generation
```yaml
# In inventory.yml
env_vars:
  newt:
    NEWT_ID: "{{ newt_id }}"
    NEWT_SECRET: "{{ newt_secret }}"
    PANGOLIN_ENDPOINT: "https://pangolin.nobasura.org"
```

**Variable Inheritance Hierarchy** (later overrides earlier):
1. `docker_env_vars.common` - Global Docker defaults
2. `docker_env_vars[stack]` - Stack-specific Docker vars
3. `env_vars.common` - Host-specific global vars  
4. `env_vars[stack]` - Host-specific stack vars

**Benefits**:
- No template conflicts (uses standard environment variable substitution)
- Follows existing codebase patterns
- Credentials managed via 1Password lookups
- Per-stack isolation

## Implementation Files

### Service Template (`ansible/files/common/newt/compose.yml`)
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
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    labels:
      - "deunhealth.restart.on.unhealthy=true"
```

**Design Notes**:
- Follows container standardization pattern (extends `base`)
- Uses `network_mode: host` for tunnel requirements
- Environment variables from .env file (${VARIABLE} syntax)
- Health check validates external Pangolin connectivity
- Auto-restart on health failure via deunhealth

### Inventory Configuration Pattern
```yaml
# Per-VM configuration
media-vm:
  # ... existing config ...
  pangolin_newt_enabled: true
  newt_id: "{{ lookup('community.general.onepassword', 'PANGOLIN_MEDIA_SITE_NEWT', field='username', vault='Homelab') }}"
  newt_secret: "{{ lookup('community.general.onepassword', 'PANGOLIN_MEDIA_SITE_NEWT', vault='Homelab') }}"
  env_vars:
    newt:
      NEWT_ID: "{{ newt_id }}"
      NEWT_SECRET: "{{ newt_secret }}"
      PANGOLIN_ENDPOINT: "https://pangolin.nobasura.org"
```

## Deployment Usage

### Safe Tunnel Deployment
```bash
# Deploy with tunnel automation
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml -e deploy_tunnels=true

# Target specific VM
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml -e deploy_tunnels=true --limit media-vm
```

### Regular Application Deployment
```bash
# Normal deployment (tunnels unchanged)
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml
```

## Validation Results

**Production Issue Resolution**: ✅ **RESOLVED**
- Media site status: "Offline" → "Online" in Pangolin UI
- Tunnel connectivity: 8 TCP proxies active with 3-4ms latency
- Services accessible: Radarr, Readarr, Bazarr, qBittorrent, Jellyfin, Overseerr, Homepage, Jackett

**Container Health**: ✅ **HEALTHY**
```
CONTAINER ID   IMAGE              STATUS
b164a00a3bc9   fosrl/newt:1.2.1   Up 3 minutes (healthy)
```

**Credentials**: ✅ **VERIFIED**
- NEWT_ID: <redacted> (correct from 1Password)
- NEWT_SECRET: [verified match]
- PANGOLIN_ENDPOINT: https://pangolin.nobasura.org

## Benefits Achieved

1. **Production Stability**: Eliminated manual tunnel fixes
2. **Safe Automation**: Prevents accidental tunnel disruption  
3. **Code Consistency**: Follows existing Docker role patterns
4. **Credential Security**: 1Password integration maintained
5. **Maintainability**: Declarative configuration in inventory
6. **Monitoring**: Health checks and auto-restart capabilities

## Related Documentation

- **Container Standards**: `memory://patterns/container-standardization-patterns`
- **Critical Rules**: `memory://decisions/critical-infrastructure-rules`
- **Docker Role**: `ansible/roles/docker/` - Core deployment automation
- **Root Cause Analysis**: `decisions/Media Site Offline Root Cause Analysis - June 19, 2025.md`