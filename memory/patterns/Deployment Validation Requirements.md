---
title: Deployment Validation Requirements
type: note
permalink: patterns/deployment-validation-requirements
---

# Deployment Validation Requirements

## CRITICAL RULE
**ALWAYS confirm ALL services on changed VM are running and accessible before claiming deployment success!**

## Extended Validation Rule
When deploying to a VM, validate **every service** on that VM, not just the new/changed service. Deployments can affect other containers through:
- Resource conflicts
- Network changes  
- Docker daemon restarts
- Volume/dependency issues

## Required Validation Steps

### 1. Complete VM Container Status Verification
```bash
# Check ALL containers are running on target VM
ansible <target-vm> -i inventory.yml -m shell -a "docker ps --filter 'status=running'"

# Verify expected container count (compare to baseline)
ansible <target-vm> -i inventory.yml -m shell -a "docker ps --filter 'status=running' | wc -l"

# Check for restart loops or failed containers
ansible <target-vm> -i inventory.yml -m shell -a "docker ps -a --filter 'status=restarting'"
ansible <target-vm> -i inventory.yml -m shell -a "docker ps -a --filter 'status=exited'"

# Verify specific new service
ansible <target-vm> -i inventory.yml -m shell -a "docker ps --filter 'name=<service-name>'"
```

### 2. Service Accessibility Tests
```bash
# Test direct access
curl -I http://<vm>.lan:<port>/

# Test service health endpoint if available
curl -I http://<vm>.lan:<port>/health
```

### 3. Container Logs Review
```bash
# Check for startup errors
ansible <target-vm> -i inventory.yml -m shell -a "docker logs <container-name> --tail 20"
```

### 4. Integration Tests
```bash
# Run homelab test suite
ansible-playbook test_homelab_vms.yml

# Run gateway tests if applicable
ansible-playbook test_gateway_vps.yml
```

## Success Criteria Checklist
- [ ] **ALL containers on target VM running** (not restarting/exited)
- [ ] **Container count matches expected** (baseline + new services)
- [ ] Target service container running (not restarting/exited)
- [ ] **ALL existing services on VM still accessible**
- [ ] New service responds to HTTP requests
- [ ] No critical errors in container logs
- [ ] Integration tests pass
- [ ] No regression in existing services

## Never Claim Success Without
1. Verifying **ALL containers on target VM** are running
2. Confirming **expected container count** (baseline + new)
3. Testing **ALL services on VM** are accessible 
4. Testing new service accessibility specifically
5. Checking container logs for errors
6. Confirming no existing services broken

## Anti-Pattern: Assuming Success
❌ "Deployment completed" without verification
❌ "Service should be working" without testing
❌ Ignoring container restart loops
❌ Not checking logs for startup errors