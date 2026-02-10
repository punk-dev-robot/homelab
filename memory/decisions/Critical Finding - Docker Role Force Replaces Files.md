---
title: Critical Finding - Docker Role Force Replaces Files
type: note
permalink: decisions/critical-finding-docker-role-force-replaces-files
---

# Critical Finding - Docker Role Force Replaces Files

## Root Cause of Auth Bypass Failure

### What Happened
When deploying the enclosed service, the auth bypass routes for jellyseerr, sonarr, and radarr **disappeared completely**. The cause was NOT our changes, but the deployment mechanism itself.

### Critical Discovery: Force File Replacement
The `docker` role deployment **force replaces all files**, causing configuration drift to be lost:

```yaml
# roles/docker/tasks/deploy_stack.yml
- name: Remove existing compose folder for {{ cur_stack }}
  file:
    path: "{{ docker_compose_dir }}/{{ cur_stack }}"
    state: absent

- name: Copy stack files {{ cur_stack }}
  copy:
    src: "{{ inventory_hostname }}/{{ cur_stack }}"
    dest: "{{ docker_compose_dir }}"
```

### The Problem
1. **Live Configuration Drift**: Auth bypass routes were configured live on gateway VPS but NOT in source files
2. **Force Replacement**: Docker role deletes entire folder then copies source files
3. **Lost Configuration**: Any live-only configurations are permanently lost on deployment
4. **No Merging**: No mechanism to preserve live changes

### Evidence
- **Previous git version**: `dynamic_config.yml` had NO bypass routes in source
- **Live system**: Had working bypass routes (tests were passing before)
- **After deployment**: Bypass routes gone, only source routes remain

### Critical Implications
⚠️ **Any live configuration changes not captured in source files will be LOST on deployment**

This affects:
- Traefik routing configurations
- Any manually added services
- Live configuration tweaks
- Hot fixes not committed to git

### Required Actions
1. **Immediate**: Restore missing auth bypass routes to source files
2. **Process**: Always commit live changes to git before deployment
3. **Architecture**: Consider if files should be templated vs static
4. **Documentation**: Update deployment warnings about force replacement

### Memory Tags
#critical-finding #deployment #configuration-drift #docker-role #debugging #force-replacement