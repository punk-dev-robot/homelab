---
title: Tunnel Infrastructure Automation Patterns
type: note
permalink: patterns/tunnel-infrastructure-automation-patterns
---

# Tunnel Infrastructure Automation Patterns

## Overview

Design patterns and best practices for automating tunnel infrastructure in homelab environments. Focuses on safe, maintainable, and consistent deployment of critical networking services.

## Core Patterns

### 1. Conditional Deployment with Safety Flags

**Purpose**: Protect critical infrastructure from accidental changes during routine deployments.

**Implementation**:
```yaml
- name: Deploying newt tunnel stack
  include_tasks: deploy_stack.yml
  when: docker_deploy and deploy_tunnels | default(false) and pangolin_newt_enabled | default(false)
  vars:
    cur_stack: newt
```

**Safety Mechanisms**:
- `deploy_tunnels | default(false)` - Explicit opt-in required
- `pangolin_newt_enabled | default(false)` - Host-level toggle
- Conservative defaults (false) prevent accidents

**Usage Patterns**:
```bash
# Safe: Regular deployment (tunnels unchanged)
ansible-playbook deploy_docker.yml

# Explicit: Deploy with tunnel changes
ansible-playbook deploy_docker.yml -e deploy_tunnels=true

# Targeted: Single VM with tunnels  
ansible-playbook deploy_docker.yml -e deploy_tunnels=true --limit media-vm
```

### 2. Discovery-Based File Resolution

**Purpose**: Flexible file loading with fallback hierarchy for maintainability.

**Pattern**:
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

**Resolution Order**:
1. Host-specific override: `files/media-vm/newt/`
2. Common template: `files/common/newt/`

**Benefits**:
- Eliminates hardcoded conditionals
- Host-specific customization when needed
- Consistent defaults across infrastructure
- Future-proof for new services

### 3. Per-Stack Environment Variable Management

**Purpose**: Isolate service configuration while maintaining inheritance hierarchy.

**Hierarchy** (later values override earlier):
```yaml
stack_env_vars: >-
  {{ docker_env_vars.common | combine(
    docker_env_vars[cur_stack] | default({}),
    env_vars.common | default({}),
    env_vars[cur_stack] | default({})
  ) }}
```

**Variable Sources**:
1. `docker_env_vars.common` - Global Docker defaults (PUID/PGID/TZ)
2. `docker_env_vars[stack]` - Stack-specific Docker vars
3. `env_vars.common` - Host-specific global vars
4. `env_vars[stack]` - Host-specific stack vars (credentials, endpoints)

**Configuration Example**:
```yaml
# In inventory.yml
env_vars:
  newt:
    NEWT_ID: "{{ newt_id }}"
    NEWT_SECRET: "{{ newt_secret }}"
    PANGOLIN_ENDPOINT: "https://pangolin.nobasura.org"
```

**Template Usage**:
```yaml
# In compose.yml
environment:
  - NEWT_ID=${NEWT_ID}
  - NEWT_SECRET=${NEWT_SECRET}
  - PANGOLIN_ENDPOINT=${PANGOLIN_ENDPOINT}
```

### 4. Infrastructure Service Composition

**Purpose**: Apply container standards while accommodating infrastructure requirements.

**Template Pattern**:
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

**Design Principles**:
- **Standards Compliance**: Extends `base` service for consistency
- **Infrastructure Needs**: Uses `network_mode: host` for tunnel requirements
- **Health Monitoring**: External connectivity validation
- **Auto-Recovery**: Restart on health check failure
- **Environment Isolation**: Variables from .env file

## Deployment Safety Patterns

### Targeted vs Full Deployment

**Problem**: How to deploy specific services without affecting critical infrastructure.

**Solution**: Separate tunnel lifecycle from application lifecycle.

```bash
# Application deployment (safe)
ansible-playbook deploy_docker.yml --limit media-vm

# Application with tunnel updates (explicit)  
ansible-playbook deploy_docker.yml -e deploy_tunnels=true --limit media-vm

# Multiple VMs with tunnels
ansible-playbook deploy_docker.yml -e deploy_tunnels=true --limit "apps-vm,media-vm"
```

### Rollback Strategy

**Preparation**: Always capture current state before tunnel changes.
```bash
# Pre-deployment validation
ansible media-vm -a "docker ps --filter name=newt"
ansible media-vm -a "docker logs newt --tail 10"

# Deployment with logging
ansible-playbook deploy_docker.yml -e deploy_tunnels=true --limit media-vm -v
```

**Recovery**: Standard Docker compose rollback.
```bash
# Manual rollback if needed
ansible media-vm -a "docker compose -f /opt/docker/compose/newt/compose.yml down"
# Fix configuration, then redeploy
```

## Security Patterns

### Credential Management
- **1Password Integration**: Credentials never stored in plaintext
- **Per-Service Isolation**: Each tunnel has unique credentials
- **Environment Variable Injection**: Runtime credential loading

### Network Security
- **Host Network Mode**: Required for tunnel functionality
- **Health Check Validation**: Continuous connectivity monitoring
- **Endpoint Verification**: External service reachability

## Monitoring and Observability

### Health Check Strategy
```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --quiet --spider --timeout=10 --tries=1 https://pangolin.nobasura.org || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

### Automated Recovery
```yaml
labels:
  - "deunhealth.restart.on.unhealthy=true"
```

### Log Monitoring
```bash
# Real-time tunnel monitoring
ansible media-vm -a "docker logs -f newt"

# Health status check
ansible media-vm -a "docker ps --filter name=newt --format 'table {{.Names}}\t{{.Status}}'"
```

## Anti-Patterns to Avoid

1. **Hardcoded File Paths**: Use discovery-based loading instead
2. **Template Conflicts**: Use environment variables instead of Ansible templating in Docker compose
3. **Implicit Tunnel Updates**: Always require explicit flags for infrastructure changes
4. **Manual Credential Management**: Always use 1Password lookups
5. **Missing Health Checks**: Infrastructure services must validate external connectivity

## Related Documentation

- **Implementation Details**: `memory://decisions/newt-tunnel-automation-implementation`
- **Container Standards**: `memory://patterns/container-standardization-patterns`
- **Ansible Commands**: `memory://patterns/ansible-commands-quick-reference`
- **Critical Rules**: `memory://decisions/critical-infrastructure-rules`