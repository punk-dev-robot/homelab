---
title: CrowdSec Pangolin Integration
type: note
permalink: architecture/crowd-sec-pangolin-integration
---

# CrowdSec Pangolin Integration

## Integration Architecture Overview
- [architecture] CrowdSec integrated into Pangolin Docker stack with shared networking #docker-stack-integration
- [deployment] Ansible-automated deployment with secret management #ansible-deployment
- [configuration] Manual Docker Compose integration for existing Pangolin systems #manual-integration
- [security] Multi-layer IP whitelisting with Pangolin tunnel network support #tunnel-security

## Core Infrastructure Components

### Docker Stack Integration
```yaml
# pangolin.yml - CrowdSec Service Definition
services:
  crowdsec:
    image: crowdsecurity/crowdsec:latest-debian
    container_name: crowdsec
    restart: unless-stopped
    environment:
      COLLECTIONS: "crowdsecurity/linux crowdsecurity/sshd crowdsecurity/traefik crowdsecurity/http-cve"
      ENROLL_KEY: "${CROWDSEC_ENROLLMENT_KEY}"
      ENROLL_INSTANCE_NAME: "pangolin-gateway"
    volumes:
      - /var/log/journal:/var/log/host:ro
      - ./secrets:/secrets:ro
      - crowdsec-data:/var/lib/crowdsec/data
      - crowdsec-config:/etc/crowdsec
    ports:
      - "8080:8080"  # LAPI for bouncers
      - "6060:6060"  # Metrics endpoint  
    expose:
      - "7422"       # AppSec WAF endpoint
    networks:
      - pangolin-network
    healthcheck:
      test: ["CMD", "cscli", "version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

### Network Architecture
- [networking] Shared `pangolin-network` for Traefik-CrowdSec communication #shared-networking
- [networking] Internal API communication via container names #container-networking
- [networking] External port exposure for metrics and API access #port-mapping
- [networking] Secure tunnel integration with Pangolin networks #tunnel-integration

## Log Acquisition Architecture

### System Log Integration
```yaml
# acquis.yaml - Log Source Configuration
filenames:
  - /var/log/journal
labels:
  type: journald

filenames:
  - /var/log/traefik/*.log
labels:
  type: traefik

# AppSec WAF Configuration
listen_addr: 0.0.0.0:7422
appsec_config: crowdsecurity/appsec-default
name: pangolin-appsec
source: appsec
labels:
  type: appsec
```

### Journal Integration Pattern
- [logging] systemd journal mounting: `/var/log/journal:/var/log/host:ro` #journal-mounting
- [logging] Debian image for journalctl binary compatibility #debian-compatibility
- [logging] SSH authentication monitoring via journald #ssh-monitoring
- [logging] Web access log processing via Traefik JSON logs #web-monitoring

## Security Configuration Architecture

### IP Whitelisting Strategy
```yaml
# Multiple protection layers for Pangolin networks
clientTrustedIPs:
  - "10.0.0.0/8"          # Private networks
  - "172.16.0.0/12"       # Docker networks
  - "192.168.0.0/16"      # Local networks
  - "100.89.137.0/20"     # Pangolin tunnel networks
  - "10.100.0.0/16"       # Homelab tunnel networks
  - "<ADMIN_HOME_IP>/32"    # Admin home IP

forwardedHeadersTrustedIPs:
  - "0.0.0.0/0"           # Required for Traefik plugin
```

### Protection Profiles
```yaml
# profiles.yaml - Remediation Configuration
name: captcha_web_attacks
filters:
  - Alert.Remediation == true && Alert.GetScope() == "Ip" && Alert.GetScenario() contains "http"
decisions:
  - type: captcha
    duration: 4h

name: ban_ssh_attacks
filters:
  - Alert.Remediation == true && Alert.GetScope() == "Ip" && Alert.GetScenario() contains "ssh"
decisions:
  - type: ban
    duration: 24h
```

## Ansible Automation Architecture

### Deployment Integration
```yaml
# deploy_stack.yml - Pangolin CrowdSec Tasks
- name: Generate CrowdSec API key file
  copy:
    content: "{{ stack_env_vars.CROWDSEC_BOUNCER_API_KEY }}"
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/secrets/crowdsec-api-key"
    mode: "0600"
  when: cur_stack == "pangolin"

- name: Template CrowdSec enrollment key
  template:
    src: pangolin.yml.j2
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/pangolin.yml"
  vars:
    crowdsec_enrollment_key: "{{ op_crowdsec_enrollment_key }}"
  when: cur_stack == "pangolin"
```

### Secret Management Pattern
- [secrets] 1Password integration for enrollment keys #1password-integration
- [secrets] API key file generation with secure permissions #secure-keys
- [secrets] Environment variable templating for Docker Compose #env-templating
- [secrets] Conditional deployment based on stack requirements #conditional-deployment

## Collections and Scenarios

### Essential Collection Architecture
```yaml
# Environment configuration for comprehensive protection
COLLECTIONS: |
  crowdsecurity/linux
  crowdsecurity/sshd
  crowdsecurity/traefik
  crowdsecurity/http-cve
  crowdsecurity/appsec-virtual-patching
  crowdsecurity/appsec-generic-rules
```

### Scenario Coverage
- [scenarios] SSH brute force detection and mitigation #ssh-scenarios
- [scenarios] Web attack pattern recognition (XSS, SQLi, path traversal) #web-scenarios
- [scenarios] CVE-specific exploit detection and blocking #cve-scenarios
- [scenarios] Admin interface probing and backdoor detection #admin-scenarios

## Bouncer Architecture

### Traefik Plugin Bouncer
- [bouncer] Plugin-based integration with Traefik middleware #plugin-bouncer
- [bouncer] File-based API key configuration #file-api-key
- [bouncer] Selective middleware application for service protection #selective-protection
- [bouncer] Real-time decision enforcement for web traffic #real-time-enforcement

### Firewall Bouncer (Optional)
- [bouncer] Host-level iptables integration for SSH protection #firewall-bouncer
- [bouncer] System-wide IP blocking for severe threats #system-blocking
- [bouncer] Complementary protection to Traefik middleware #complementary-protection

## Monitoring and Health Architecture

### Health Check Strategy
```yaml
# Container health monitoring
healthcheck:
  test: ["CMD", "cscli", "version"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### Operational Monitoring
```bash
# Status monitoring commands
docker exec crowdsec cscli status
docker exec crowdsec cscli metrics
docker exec crowdsec cscli bouncers list
docker exec crowdsec cscli decisions list
```

### Performance Metrics
- [metrics] Prometheus endpoint on port 6060 #prometheus-metrics
- [metrics] Decision processing latency monitoring #latency-metrics
- [metrics] Bouncer registration and health status #bouncer-health
- [metrics] Community intelligence feed consumption #intelligence-metrics

## Volume and Data Architecture

### Persistent Data Strategy
```yaml
volumes:
  - crowdsec-data:/var/lib/crowdsec/data      # Decision database
  - crowdsec-config:/etc/crowdsec             # Configuration files
  - ./secrets:/secrets:ro                     # API keys and secrets
  - /var/log/journal:/var/log/host:ro         # System logs
```

### Data Persistence Requirements
- [persistence] Decision database for offline operation #decision-persistence
- [persistence] Configuration files for custom scenarios #config-persistence
- [persistence] API key storage with secure mounting #key-persistence
- [persistence] Log access for real-time analysis #log-access

## Testing and Validation Architecture

### Attack Simulation Framework
```bash
# Web attack testing
curl -H "User-Agent: nikto" https://domain.com/admin
curl https://domain.com/../../../etc/passwd
curl https://domain.com/.env

# SSH attack simulation
ssh -o PreferredAuthentications=password invalid@domain.com
```

### Decision Management
```bash
# Emergency decision management
docker exec crowdsec cscli decisions add --ip THREAT_IP --type ban -d 1h
docker exec crowdsec cscli decisions delete --ip ADMIN_IP
```

## Integration Validation

### Deployment Verification Steps
1. [validation] Container health check confirmation #health-validation
2. [validation] API connectivity between Traefik and CrowdSec #api-validation
3. [validation] Log acquisition from journal and Traefik #log-validation
4. [validation] Community enrollment and intelligence feed connection #community-validation
5. [validation] Attack detection and decision enforcement testing #protection-validation

### Emergency Procedures
- [emergency] Admin IP whitelisting via console management #emergency-whitelist
- [emergency] Decision removal for false positive resolution #false-positive-fix
- [emergency] Service isolation for troubleshooting #service-isolation
- [emergency] Configuration rollback procedures #config-rollback

## Relations
- implements [[CrowdSec Security Architecture]]
- integrates_with [[CrowdSec Traefik Integration]]
- supports [[System Architecture Overview]]
- deployed_via [[CrowdSec Deployment Patterns]]
- troubleshooting_in [[CrowdSec Troubleshooting]]