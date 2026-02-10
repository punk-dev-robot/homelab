---
title: Test Infrastructure Discovery - Validation Tests Update
type: note
permalink: decisions/test-infrastructure-discovery-validation-tests-update
---

# Test Infrastructure Discovery - Validation Tests Update

## Available Test Categories

### Test Suites
- `ansible/tests/suites/gateway_vps_test_suite.yml` - Gateway VPS testing
- `ansible/tests/suites/homelab_vms_test_suite.yml` - Homelab VM testing

### Validation Tests (NEW DISCOVERY)
- `ansible/tests/validation/container_standardization.yml` - Container standards validation
- `ansible/tests/validation/crowdsec_firewall_bouncer.yml` - CrowdSec firewall validation

### Individual Test Files
- `ansible/tests/homelab/test_direct_access.yml` - Direct .lan access tests
- `ansible/tests/homelab/test_proxy_access.yml` - Caddy proxy .lab access tests
- Various security and functionality tests

## Current Issues Found

### Test Execution Problems
1. **Missing Inventory**: Tests need `-i ansible/inventory.yml` parameter
2. **Missing Auth Bypass**: Gateway tests fail on missing `roles/pangolin/vars/auth_bypass.yml`
3. **Path Issues**: Homelab tests can't find test files (path resolution)

### Ansible-Lint Violations (37 total)
- **Formatting**: YAML spacing, newlines, trailing spaces
- **Jinja2**: Template spacing issues
- **Shell Commands**: Missing pipefail, changed-when conditions
- **Naming**: Template usage in task names

## Required Actions
1. Fix ansible-lint violations for code quality
2. Run tests with proper inventory: `-i ansible/inventory.yml`
3. Investigate missing auth_bypass.yml file
4. Validate container standardization with proper hosts
5. Update CLAUDE.md with validation test discovery

## Memory Update
Added validation tests to test infrastructure knowledge - these are critical for container standards compliance.