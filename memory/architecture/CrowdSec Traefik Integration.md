---
title: CrowdSec Traefik Integration
type: note
permalink: architecture/crowd-sec-traefik-integration
---

# CrowdSec Traefik Integration

## Integration Architecture Overview
- [architecture] CrowdSec integrated into Pangolin/Traefik stack via Docker networking #docker-integration
- [approach] Plugin-based integration using crowdsec-bouncer-traefik-plugin #plugin-approach
- [security] File-based API key management with secure mounting #api-key-security
- [selectivity] Middleware applied selectively to prevent internal service disruption #selective-protection

## Core Integration Components

### Traefik Plugin Configuration
```yaml
# traefik_config.yml - Plugin Configuration
experimental:
  plugins:
    crowdsec-bouncer:
      moduleName: "github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin"
      version: "v1.3.5"

# JSON Access Logs for CrowdSec Analysis
accessLog:
  format: "json"
  filePath: "/var/log/traefik/access.log"
```

### Middleware Configuration Pattern
```yaml
# dynamic_config.yml - Middleware Definition
http:
  middlewares:
    crowdsec-bouncer:
      plugin:
        crowdsec-bouncer:
          enabled: true
          logLevel: "INFO"
          crowdsecLapiHost: "crowdsec:8080"
          crowdsecLapiScheme: "http"
          crowdsecAppsecHost: "crowdsec:7422"
          crowdsecLapiKeyFile: "/secrets/crowdsec-api-key"
          clientTrustedIPs:
            - "10.0.0.0/8"
            - "172.16.0.0/12"
            - "192.168.0.0/16"
            - "<ADMIN_HOME_IP>/32"  # Admin IP
```

### Docker Network Integration
```yaml
# pangolin.yml - Service Integration
services:
  crowdsec:
    image: crowdsecurity/crowdsec:latest-debian
    networks:
      - pangolin-network  # Shared with Traefik
    volumes:
      - ./secrets:/secrets:ro
      - /var/log/journal:/var/log/host:ro

  traefik:
    volumes:
      - ./secrets:/secrets:ro  # Shared secrets access
    networks:
      - pangolin-network
```

## Configuration Architecture

### API Key Management Pattern
- [security] File-based approach: `/secrets/crowdsec-api-key` #file-based-key
- [security] Read-only mount with 600 permissions #secure-mounting  
- [security] Ansible-generated from 1Password secrets #automated-generation
- [security] Avoids Traefik template syntax conflicts #template-compatibility

```yaml
# Ansible API Key Generation
- name: Generate CrowdSec API key file
  copy:
    content: "{{ stack_env_vars.CROWDSEC_BOUNCER_API_KEY }}"
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/secrets/crowdsec-api-key"
    mode: "0600"
  when: cur_stack == "pangolin"
```

### Network Communication Architecture
- [networking] CrowdSec API: `crowdsec:8080` (LAPI) #lapi-communication
- [networking] AppSec API: `crowdsec:7422` (Application Security) #appsec-communication
- [networking] Shared Docker network for container-to-container communication #container-networking
- [networking] No external API exposure required #internal-communication

## Protection Strategy Architecture

### Selective Middleware Application
- [strategy] Internal services: CrowdSec middleware DISABLED #internal-safety
- [strategy] External-facing services: CrowdSec middleware ENABLED selectively #external-protection
- [strategy] Admin interfaces: Multi-layer protection with IP whitelisting #admin-protection

### Trusted IP Configuration
```yaml
# Trust Network Architecture
clientTrustedIPs:
  - "10.0.0.0/8"          # Private networks
  - "172.16.0.0/12"       # Docker networks  
  - "192.168.0.0/16"      # Local networks
  - "<ADMIN_HOME_IP>/32"    # Admin home IP
```

### Service Integration Pattern
```yaml
# Example: External Service Protection
http:
  routers:
    external-service:
      middlewares:
        - crowdsec-bouncer  # Apply protection
        - other-middleware
      
    internal-service:
      middlewares:
        - other-middleware  # No CrowdSec protection
```

## Logging Architecture

### JSON Access Log Integration
- [logging] Format: JSON for structured analysis #json-format
- [logging] Location: `/var/log/traefik/access.log` #log-location
- [logging] Purpose: CrowdSec web attack pattern detection #attack-detection
- [logging] Processing: Real-time analysis by CrowdSec parsers #real-time-processing

### Log Analysis Pattern
```json
{
  "ClientAddr": "192.168.1.100",
  "RequestMethod": "GET", 
  "RequestPath": "/admin/login",
  "RequestProtocol": "HTTP/1.1",
  "ResponseCode": 404,
  "RequestDuration": 1234567
}
```

## Plugin Architecture Details

### Version Management Strategy
- [versioning] Pinned plugin version: `v1.3.5` #version-pinning
- [versioning] Experimental plugin loading in Traefik configuration #experimental-features
- [versioning] GitHub-based module resolution #github-modules

### Configuration File Structure
```
config/traefik/
├── traefik_config.yml     # Plugin loading + access logs
├── dynamic_config.yml     # Middleware definitions
└── docker-compose.yml     # Service integration
```

## Integration Validation

### Health Check Architecture
- [validation] CrowdSec API connectivity via health checks #health-monitoring
- [validation] Plugin loading verification at Traefik startup #plugin-verification
- [validation] API key file existence and permissions #key-validation
- [validation] Network connectivity between containers #network-validation

### Testing Pattern
```bash
# API Connectivity Test
curl -H "X-Api-Key: $(cat secrets/crowdsec-api-key)" \
     http://crowdsec:8080/v1/decisions

# Plugin Status Verification  
docker logs traefik | grep "crowdsec-bouncer"
```

## Operational Configuration

### Deployment Integration
- [deployment] Ansible automation for configuration generation #ansible-integration
- [deployment] Template-based configuration with variable substitution #template-config
- [deployment] Environment-specific secret management #env-secrets
- [deployment] Validation steps in deployment pipeline #deployment-validation

### Emergency Procedures
- [emergency] Middleware disable: Remove from router configuration #emergency-disable
- [emergency] API key rotation: Update file and restart Traefik #key-rotation
- [emergency] Plugin disable: Comment out plugin loading #plugin-disable
- [emergency] Local API access for decision management #local-api

## Performance Characteristics

### Response Time Impact
- [performance] Sub-200ms additional latency for protected requests #latency-impact
- [performance] Cached decisions for improved performance #decision-caching
- [performance] Async processing for non-blocking operation #async-processing

### Resource Utilization
- [performance] Minimal CPU overhead for plugin processing #cpu-minimal
- [performance] Memory-efficient decision caching #memory-efficient
- [performance] Network-optimized API communication #network-optimized

## Relations
- implements [[CrowdSec Security Architecture]]
- integrates_with [[System Architecture Overview]]
- configured_in [[CrowdSec Pangolin Integration]]
- troubleshooting_in [[CrowdSec Troubleshooting]]
- patterns_in [[CrowdSec Deployment Patterns]]