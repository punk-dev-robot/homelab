---
title: CrowdSec Authentik Protection Implementation
type: note
permalink: decisions/crowd-sec-authentik-protection-implementation
---

# CrowdSec Authentik Protection Implementation

## Summary
Successfully implemented CrowdSec authentication protection for the newly deployed Authentik SSO service on June 18, 2025. This addresses the security gap that existed from June 6-18 when CrowdSec was temporarily disabled.

## Key Implementation Details

### Docker Socket Access Fix
- **File**: `ansible/files/gateway-vps/pangolin/pangolin.yml:80`
- **Change**: Added `/var/run/docker.sock:/var/run/docker.sock:ro` to CrowdSec container volumes
- **Purpose**: Enables CrowdSec to monitor Docker container logs for authentication attacks

### Authentik Acquisition Configuration
- **File**: `ansible/files/gateway-vps/crowdsec/config/crowdsec/acquis.d/acquis-authentik.yaml`
- **Monitors**: Both `authentik-server` and `authentik-worker` containers
- **Collection**: `firix/authentik` with `firix/authentik-bf` brute force scenario
- **Status**: Successfully processing 244 log lines from Authentik containers

### Infrastructure Fixes
- **Validation Test**: Fixed case sensitivity in `ansible/tests/validation/crowdsec_firewall_bouncer.yml` (line 31)
  - Changed from `'crowdsec'` to `'CROWDSEC_CHAIN'` for proper iptables rule detection
- **Environment Variables**: Added missing `docker_env_vars` structure to gateway group in `ansible/inventory.yml`

## Protection Status (June 18, 2025)

### Active Bouncers
1. **CrowdSec Firewall Bouncer**: Network-level IP blocking (2.42k malicious IPs blocked)
2. **Traefik Bouncer**: HTTP-level protection via plugin
3. **Authentik Protection**: Dedicated auth attack detection via `firix/authentik-bf`

### Attack Statistics
- SSH brute force: 871 blocked attacks
- HTTP brute force: 1,448 blocked attacks  
- Network packets: 16 blocked (960 bytes)
- Community blocklist: 2.42k active IP bans

### Validation Results
- All CrowdSec firewall bouncer tests pass ✅
- Both bouncers coexist properly ✅
- Authentik container monitoring active ✅
- IPTables rules properly configured ✅

## Technical Architecture

### CrowdSec Data Flow
```
Authentik Containers → Docker Socket → CrowdSec → firix/authentik-bf Scenario → Ban Decisions → Firewall/Traefik Bouncers
```

### Container Integration
- **CrowdSec**: Monitors via Docker socket at `/var/run/docker.sock`
- **Authentik**: Logs processed by `firix/authentik-logs` parser
- **Traefik**: Access logs monitored at `/var/log/traefik/access.log`

## Deployment Information
- **Commit**: `452ce99` - "feat: enable CrowdSec Docker container monitoring for Authentik protection"
- **Branch**: `authentik`
- **Date**: June 18, 2025
- **Environment**: Gateway VPS (141.147.93.212)

## Related Files
- `ansible/files/gateway-vps/pangolin/pangolin.yml` - CrowdSec container config
- `ansible/files/gateway-vps/crowdsec/config/crowdsec/acquis.d/acquis-authentik.yaml` - Authentik monitoring
- `ansible/tests/validation/crowdsec_firewall_bouncer.yml` - Validation tests
- `ansible/inventory.yml` - Environment variables

## Monitoring Commands
```bash
# Check CrowdSec metrics
ansible -i ansible/inventory.yml gateway-vps -a "docker exec crowdsec cscli metrics"

# View Authentik container monitoring
ansible -i ansible/inventory.yml gateway-vps -a "docker logs crowdsec --tail 20"

# Validate firewall bouncer
ansible-playbook -i ansible/inventory.yml ansible/tests/validation/crowdsec_firewall_bouncer.yml

# Check blocked IPs
ansible -i ansible/inventory.yml gateway-vps -a "docker exec crowdsec cscli decisions list"
```

## Security Impact
- **Closed Gap**: 11-day security gap (June 6-18) now resolved
- **Enhanced Protection**: Authentik SSO now protected against brute force attacks
- **Multi-Layer Defense**: Network (firewall), application (Traefik), and authentication (Authentik) levels
- **Community Intelligence**: Leveraging CrowdSec community blocklist (2.42k IPs)

## Next Steps
- Monitor Authentik authentication attempts for attack patterns
- Consider adding additional auth scenarios for other web services
- Regular validation testing to ensure continued protection