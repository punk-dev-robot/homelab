---
title: Infrastructure Workflow Refactoring Complete - Eliminated site.yml
type: note
permalink: decisions/infrastructure-workflow-refactoring-complete-eliminated-site-yml
tags:
- '["infrastructure-refactoring"'
- '"workflow-improvement"'
- '"auth-bypass-fix"'
- '"architecture-cleanup"'
- '"deployment-workflow"]'
---

# Infrastructure Workflow Refactoring Complete - Eliminated site.yml

## Session Date: June 17, 2025

## ✅ MAJOR ARCHITECTURE IMPROVEMENT COMPLETED

### Problem Solved: Auth Bypass Deployment Bug
**Root Cause**: `site.yml` orchestrated multiple concerns without adding value, causing auth bypass to be missing when deploying to gateway-vps
**Solution**: Eliminated unnecessary orchestration, implemented targeted playbooks

### New Clean Architecture

#### **Targeted Playbook Approach**
1. **`provision.yml`** - Initial infrastructure setup
   - Hostname configuration
   - Basic utilities installation
   - One-time setup concern

2. **`deploy_docker.yml`** - Local VM deployments  
   - Target: apps-vm, media-vm, obs-vm
   - Includes NFS mounting for media-vm
   - Complete docker setup + deployment

3. **`deploy_vps.yml`** - Gateway VPS deployment
   - Target: gateway-vps only
   - VPS-specific tasks (secrets, crowdsec)
   - **Includes auth bypass post_tasks**
   - Complete solution for VPS

### Implementation Details

#### **deploy_docker.yml Enhanced**
```yaml
- name: Mount data from nfs server
  hosts: media-vm
  become: true
  tasks:
    - name: Mount shared data
      ansible.posix.mount:
        # NFS configuration moved from site.yml

- name: Deploy docker apps  
  hosts: docker
  roles:
    - role: docker
      vars:
        docker_setup: true    # Now handles both setup and deployment
        docker_deploy: true
        docker_restart: true
```

#### **Updated Commands**
```bash
# New recommended workflow (eliminates auth bypass bug)
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml    # Local VMs
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml        # Gateway VPS

# Initial setup (separate concern)  
ansible-playbook -i ansible/inventory.yml ansible/provision.yml         # Infrastructure setup
```

### Validation Results

#### **deploy_docker.yml Testing**
- ✅ **NFS Mounting**: Successfully mounted for media-vm
- ✅ **Docker Deployment**: All stacks deployed (oam, servarr, jelly)
- ✅ **Multi-VM Support**: Works for apps-vm, media-vm, obs-vm
- ✅ **Performance**: 45 tasks, 18 changes, 0 failures

#### **deploy_vps.yml Testing**  
- ✅ **Docker Deployment**: Pangolin stack deployed successfully
- ✅ **Auth Bypass Generation**: bypass-routers.yml created (3365 bytes)
- ✅ **VPS-Specific Tasks**: Secrets, crowdsec, all completed
- ✅ **Performance**: 32 tasks, 8 changes, 0 failures

#### **Auth Bypass Verification**
- ✅ **File Created**: `/opt/docker/compose/pangolin/traefik_rules/bypass-routers.yml`
- ✅ **Traefik Restart**: Container restarted, config loaded
- ✅ **No Manual Intervention**: Auth bypass included automatically

### Benefits Achieved

#### **Eliminated Complexity**
- ❌ **Removed**: Artificial separation between docker setup and deployment
- ❌ **Removed**: Unnecessary orchestration in site.yml  
- ❌ **Removed**: Auth bypass deployment bug
- ❌ **Removed**: Confusion about which playbook to use when

#### **Clear Separation of Concerns**
- ✅ **Single Responsibility**: Each playbook has one clear purpose
- ✅ **Predictable Behavior**: No unexpected task omissions
- ✅ **Faster Deployments**: No irrelevant tasks (e.g., NFS on gateway-vps)
- ✅ **Maintainable**: Clear logic, easy to understand and modify

### Documentation Updates

#### **CLAUDE.md Updated**
- **Essential Commands**: Updated with targeted playbook approach
- **Infrastructure Workflow**: Reflects new deployment pattern
- **Consistent Paths**: All commands use `ansible/` prefix
- **Clear Guidance**: When to use which playbook

#### **Memory System**
- **Critical Lessons**: Auth bypass bug root cause documented
- **Workflow Patterns**: Clean architecture principles captured
- **Operational Knowledge**: New commands and procedures updated

## 🎯 INFRASTRUCTURE STATUS

### Current State: Production Ready
- ✅ **Local VMs**: Deployable via deploy_docker.yml
- ✅ **Gateway VPS**: Deployable via deploy_vps.yml (includes auth bypass)
- ✅ **Auth Bypass**: Fully functional, no manual intervention required
- ✅ **Documentation**: Comprehensive, up-to-date

### Eliminated Issues
- ❌ **Auth Bypass Bug**: Solved by eliminating site.yml
- ❌ **Workflow Confusion**: Clear playbook separation
- ❌ **Manual Steps**: Auth bypass now automatic in VPS deployment
- ❌ **Unnecessary Complexity**: Clean, purpose-driven architecture

### Quality Metrics
- **Zero Failures**: All test deployments successful
- **Pattern Compliance**: Each playbook has single responsibility
- **Documentation Complete**: CLAUDE.md reflects new workflow
- **Memory Updated**: All knowledge captured and searchable

## 🚀 OUTCOME

**Major Infrastructure Improvement**: Eliminated auth bypass deployment bug through clean architecture refactoring. New targeted playbook approach provides predictable, maintainable deployments with clear separation of concerns.

**Status**: Production ready, fully tested, comprehensively documented.