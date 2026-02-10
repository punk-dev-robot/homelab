---
title: CrowdSec Bouncer Failure Root Cause Analysis & Resolution
type: note
permalink: decisions/crowd-sec-bouncer-failure-root-cause-analysis-resolution
---

# CrowdSec Bouncer Failure Root Cause Analysis & Resolution

## 🚨 Issue Summary
Both CrowdSec bouncers (firewall + Traefik) stopped working **June 6, 2025 ~22:45 UTC** - 11+ days of compromised security.

## 🔍 Root Cause Confirmed
**VPS deployments recreate CrowdSec container → Database reset → Bouncer registrations lost**

### Evidence Timeline
1. **June 6, 22:45:38 UTC**: `pangolin_crowdsec_db` volume created during VPS deployment
2. **Since then**: Continuous `HTTP/1.1 403 Forbidden` errors from bouncers
3. **Git commits**: Extensive infrastructure changes around June 6th (Authelia removal, Pangolin upgrades)
4. **Ansible logs**: `deploy_vps.yml` execution with Docker directory restructuring

### Technical Details
- **CrowdSec database**: SQLite stored in Docker volume
- **Volume recreation**: Wipes all bouncer registrations
- **API keys preserved**: Files exist but not registered in database
- **Result**: Valid config files but 403 authentication failures

## ✅ Resolution Applied (June 18, 2025)

### Immediate Fixes
1. **Re-registered bouncers** with existing API keys:
   - `crowdsec-firewall-bouncer`: `Uoo4DT/xBWTrI7NcnrWFq92DfI6mV6tP9Yw5dhGzRBA`
   - `traefik-bouncer`: `zOrOSBeL6nsJkZiGegoragEhOr1GU7V1feAX8k00OLw`
2. **Restarted firewall bouncer** service
3. **Verified connectivity** - both bouncers now operational

### Status Verification
```
crowdsec-firewall-bouncer  172.18.0.1  ✔️  2025-06-18T09:46:26Z  crowdsec-firewall-bouncer        v0.0.33  api-key
traefik-bouncer            172.18.0.5  ✔️  2025-06-18T09:44:15Z  Crowdsec-Bouncer-Traefik-Plugin  1.X.X    api-key
```

### Enhanced Protection
- **Authentik collection** installed (`firix/authentik`) for auth-specific protection
- **API communication**: `HTTP/1.1 200` responses (vs previous 403 errors)
- **Web protection**: All services responding through protected Traefik

## 🚨 Critical Prevention Needed

### Problem in deploy_vps.yml
**Current behavior**: Creates API key files but doesn't register bouncers in CrowdSec database

**Required fix**:
```yaml
# Add to deploy_vps.yml post_tasks:
- name: Register CrowdSec bouncers after deployment
  shell: |
    docker exec crowdsec cscli bouncers add traefik-bouncer --key {{ traefik_api_key }}
    docker exec crowdsec cscli bouncers add crowdsec-firewall-bouncer --key {{ firewall_api_key }}
```

### Test Suite Enhancement
**Expand** `ansible/tests/validation/crowdsec_firewall_bouncer.yml`:

**Current tests** (firewall only):
- Service status check ✅
- iptables rules validation ✅
- ipset lists verification ✅

**Required additions**:
- **CrowdSec API connectivity**: Verify both bouncers registered and responding
- **Traefik bouncer validation**: Plugin loaded, middleware active  
- **Authentication verification**: Test 200 responses (not 403)
- **Decision enforcement**: Validate actual IP blocking functionality

### Integration Requirements
- Add bouncer validation to `gateway_vps_test_suite.yml`
- Run after every VPS deployment
- Include in smoke tests for quick validation

## 📊 Impact Assessment
- **Duration**: 11-12 days of compromised protection
- **Services affected**: All gateway VPS services (auth.nobasura.org, pangolin.nobasura.org, api.nobasura.org)
- **Protection lost**: 
  - No automatic IP blocking from CrowdSec
  - No Traefik middleware protection  
  - SSH brute force protection compromised

## 🎯 Future Prevention Strategy

### Deployment Protocol
**When updating CrowdSec**:
1. Export bouncer keys before container changes
2. Auto-register bouncers after deployment
3. Test bouncer connectivity as part of deployment validation
4. Monitor for 403 authentication failures

### Monitoring Enhancements
1. **Bouncer health checks** in test suites
2. **Monitor bouncer registration status** in CrowdSec
3. **Alert on authentication failures** from bouncers
4. **Configure Authentik log monitoring** in CrowdSec acquisition

## 🔗 Related Files
- **Bouncer configs**: `/etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml`
- **Traefik config**: `/opt/docker/compose/pangolin/traefik_rules/dynamic_config.yml`
- **API keys**: `/opt/docker/appdata/pangolin/secrets/crowdsec-api-key`
- **CrowdSec volume**: `pangolin_crowdsec_db`
- **Test file**: `ansible/tests/validation/crowdsec_firewall_bouncer.yml`

## 📅 Resolution Status
- **Date resolved**: June 18, 2025
- **Security status**: ✅ FULLY RESTORED
- **Prevention status**: 🚨 IMPLEMENTATION REQUIRED
- **Test coverage**: 🔄 ENHANCEMENT NEEDED

**Critical lesson**: CrowdSec database persistence is essential - volume recreation loses all bouncer authentication.