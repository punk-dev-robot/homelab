---
title: Ansible Deployment Optimization
type: note
permalink: patterns/ansible-deployment-optimization
---

# Ansible Deployment Optimization

## Key Optimization Rule
**When adding a service to only one VM, deploy only to that VM - not all infrastructure**

## Problem
- Current practice: Running `ansible-playbook -i inventory.yml site.yml` deploys to ALL VMs
- Inefficient when changes only affect one VM (e.g., adding Enclosed to apps-vm only)
- Wastes time and resources deploying unchanged infrastructure

## Solution: VM-Specific Deployment
Use `--limit` flag to target specific VMs:

```bash
# Deploy only to apps-vm
ansible-playbook -i inventory.yml site.yml --limit apps-vm

# Deploy only to specific VMs  
ansible-playbook -i inventory.yml site.yml --limit "apps-vm,media-vm"

# Deploy only gateway changes
ansible-playbook -i inventory.yml site.yml --limit gateway-vps
```

## When to Use Full Deployment vs Limited
- **Limited Deployment**: Service additions/changes to specific VM
- **Full Deployment**: Cross-VM changes, infrastructure-wide updates, major configuration changes

## Examples
- Adding Enclosed to apps-vm: `--limit apps-vm`
- Updating Jellyfin on media-vm: `--limit media-vm`  
- Gateway security updates: `--limit gateway-vps`
- Cross-VM networking changes: Full deployment (no --limit)

## Best Practice Workflow
1. Identify which VMs are affected by changes
2. Use `--limit` for single-VM changes
3. Use full deployment only when necessary
4. Always run appropriate test first (gateway vs homelab)