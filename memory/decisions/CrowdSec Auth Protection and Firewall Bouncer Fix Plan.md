---
title: CrowdSec Auth Protection and Firewall Bouncer Fix Plan
type: note
permalink: decisions/crowd-sec-auth-protection-and-firewall-bouncer-fix-plan
---

# CrowdSec Auth Protection + Firewall Bouncer Fix Plan

## Current Analysis
Now that we have Authentik SSO deployed, we should enhance CrowdSec protection AND fix the inactive firewall bouncer that's been down for 11 days.

## Current CrowdSec Status
✅ **Already Configured:**
- SSH brute force protection (`crowdsecurity/sshd`)
- HTTP/web protection (`crowdsecurity/traefik`, `crowdsecurity/http-cve`)  
- Generic HTTP brute force (`crowdsecurity/http-generic-bf`)
- CVE protection scenarios (44+ CVE-specific scenarios active)

❌ **Problem Identified:**
- Firewall bouncer inactive for 11 days (likely since our recent deployments)

## Part 1: Auth Protection Enhancement

### 1. Add Authentik Collection
**Collection:** `firix/authentik` 
- **Purpose:** Parser and brute-force detection specifically for Authentik
- **Includes:** 
  - `authentik-logs` parser (parses Authentik log format)
  - `authentik-bf` scenario (detects Authentik brute force attacks)

### 2. Configure Authentik Log Monitoring
- Add acquisition configuration to monitor Authentik container logs
- Enable CrowdSec to parse authentication attempts, failures, and suspicious patterns

## Part 2: Firewall Bouncer Investigation & Fix

### 1. Root Cause Analysis
**Investigate why bouncer went inactive 11 days ago:**
- Check bouncer service status and logs
- Review if recent deployments affected bouncer configuration
- Verify API connectivity between CrowdSec and bouncer
- Check if bouncer API keys are still valid

### 2. Firewall Bouncer Diagnostics
- Check bouncer service status on gateway-vps
- Verify CrowdSec LAPI connectivity
- Review bouncer logs for connection errors
- Test bouncer API key validity

### 3. Fix Bouncer Issues
- Restart bouncer service if needed
- Regenerate API keys if expired/invalid
- Update bouncer configuration if deployment changed settings
- Verify iptables rules are being applied correctly

## Implementation Steps

### Step 1: Install Authentik Collection
```bash
docker exec crowdsec cscli collections install firix/authentik
```

### Step 2: Diagnose Firewall Bouncer
```bash
# Check bouncer status and logs
systemctl status crowdsec-firewall-bouncer
journalctl -u crowdsec-firewall-bouncer -f
# Check CrowdSec API connectivity
docker exec crowdsec cscli machines list
docker exec crowdsec cscli bouncers list
```

### Step 3: Fix Bouncer Configuration
- Regenerate bouncer API key if needed
- Update bouncer config with correct LAPI endpoints
- Restart bouncer service
- Verify active blocking functionality

### Step 4: Configure Authentik Logs
- Add Authentik container log monitoring to CrowdSec
- Update acquisition configuration

### Step 5: Test & Validate
- Run CrowdSec validation test suite
- Test both Authentik protection and firewall bouncer
- Generate test attacks to verify blocking works

## Critical Priority
**Firewall bouncer fix is HIGH PRIORITY** - our gateway protection may be compromised with inactive bouncer.

## Benefits
- **Restored Protection:** Working firewall bouncer blocking malicious IPs
- **Enhanced Auth Security:** Authentik-specific attack detection
- **Root Cause Understanding:** Prevent future bouncer failures
- **Coordinated Defense:** Full CrowdSec + firewall integration restored

## Context Links
- **Authentik Collection**: https://app.crowdsec.net/hub/author/firix/collections/authentik
- **Current Config**: `ansible/files/gateway-vps/pangolin/pangolin.yml` (CrowdSec container)
- **Bouncer Role**: `ansible/roles/crowdsec_firewall_bouncer/`