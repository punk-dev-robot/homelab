---
title: Critical Infrastructure Discoveries - Auth Bypass & Service Patterns
type: note
permalink: decisions/critical-infrastructure-discoveries-auth-bypass-service-patterns
---

# Critical Infrastructure Discoveries - Auth Bypass & Service Patterns

## Session Date: June 17, 2025

## 🎯 Major Discovery 1: Auth Bypass Template System Already Exists

### Complete Infrastructure Found
- **Template**: `ansible/roles/pangolin/templates/bypass-routers.yml.j2`
- **Variables**: `ansible/roles/pangolin/vars/auth_bypass.yml` 
- **Task**: `ansible/roles/pangolin/tasks/auth_bypass.yml`
- **Integration**: `ansible/deploy_vps.yml` post-tasks (lines 35-50)

### How It Works
```yaml
# Template generates: /opt/docker/compose/pangolin/traefik_rules/bypass-routers.yml
# For each service in pangolin_auth_bypass_services:
service-mobile-bypass:
  rule: "Host(`service.nobasura.org`) && Header(`traefik-auth-bypass-key`, `${TRAEFIK_AUTH_BYPASS_KEY}`)"
  priority: 300
  service: "service-direct"
```

### All 9 Services Already Defined
```yaml
pangolin_auth_bypass_services:
  - name: jellyseerr
  - name: sonarr  
  - name: radarr
  - name: lidarr
  - name: readarr
  - name: bazarr
  - name: prowlarr
  - name: sabnzbd
  - name: nzbget
```

### Root Cause of Failures
- Template system exists but generated file likely missing
- Auth bypass should work via: `ansible-playbook deploy_vps.yml --tags auth-bypass`
- NOT via manual editing of `dynamic_config.yml`

## 🎯 Major Discovery 2: Service Access Architecture

### Internal vs External Access Clarified
- **Caddy Proxy**: Internal homelab only (`https://service.lab.nobasura.org`)
  - Via OpnSense/Unbound DNS
  - Only accessible from home network
  - NOT related to Pangolin
- **Pangolin/Traefik**: External access (`https://service.nobasura.org`)
  - Via gateway VPS
  - CrowdSec protection
  - Auth bypass for mobile apps

### Service Registration Patterns
- **Auth Bypass Services**: Use template system (`bypass-routers.yml.j2`)
- **Regular External Services**: Pattern unclear - likely Pangolin API registration
- **Static Config**: `dynamic_config.yml` should contain minimal base routes only

## 🎯 Major Discovery 3: Infrastructure Pattern Violations

### Enclosed Service Implementation Issue
- **Problem**: Added directly to `dynamic_config.yml` 
- **Violation**: No other services exist there
- **Pattern**: Should follow proper service registration (likely `group_vars/all.yml` integration)

### Configuration Drift Cause
- Docker role force-replaces entire directories
- Live-only configurations are permanently lost
- All changes must be in source files

## 🔧 Immediate Actions Required

### 1. Auth Bypass Fix
```bash
# Deploy auth bypass template system
ansible-playbook deploy_vps.yml --tags auth-bypass
```

### 2. Enclosed Service Fix
- Remove from `dynamic_config.yml`
- Add to proper service registration pattern
- Follow established homelab integration

### 3. Infrastructure Validation
- Ensure all services follow consistent patterns
- Document correct implementation approaches
- Test comprehensive functionality

## 📋 Key Variables Discovered
```yaml
# In group_vars/all.yml
auth_bypass_key: "{{ lookup('community.general.onepassword', 'TRAEFIK_AUTH_BYPASS_KEY', vault='Homelab') }}"
organization_domain: "nobasura.org"

# In roles/pangolin/vars/auth_bypass.yml  
pangolin_auth_bypass_header: "traefik-auth-bypass-key"
pangolin_auth_bypass_priority: 300
```

## 🎖️ Impact
- **Immediate**: Auth bypass can be restored via existing system
- **Strategic**: Infrastructure patterns clarified and standardized
- **Maintenance**: Configuration drift prevention understanding

#critical-discoveries #auth-bypass #infrastructure-patterns #service-registration #session-breakthroughs