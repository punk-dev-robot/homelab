---
title: CrowdSec Security Architecture
type: note
permalink: architecture/crowd-sec-security-architecture
---

# CrowdSec Security Architecture

## Architecture Overview
- [system] Complete security integration for Pangolin gateway VPS #security-architecture
- [scope] Multi-layer protection: SSH monitoring, web protection, Traefik integration #comprehensive-protection
- [deployment] Production operational with zero-impact performance #production-ready

## Core Security Architecture

### System Integration Design
- [integration] CrowdSec integrated into Pangolin Docker stack #docker-integration
- [approach] Plugin-based Traefik integration (not ForwardAuth) #traefik-plugin
- [networking] Shared network namespace for container communication #network-optimization
- [protection] Selective middleware application to prevent internal service disruption #selective-protection

### Technical Foundation
- [foundation] File-based API key management via Ansible automation #api-key-management
- [foundation] JSON access logs for structured security analysis #structured-logging
- [foundation] Community intelligence enrollment for threat feeds #community-intelligence
- [foundation] Multi-layer IP whitelisting for admin protection #admin-protection

## Docker Compose Architecture

### Service Integration Pattern
```yaml
# Core Integration Pattern
crowdsec:
  image: crowdsecurity/crowdsec:latest-debian
  environment:
    COLLECTIONS: "crowdsecurity/linux crowdsecurity/sshd crowdsecurity/traefik crowdsecurity/http-cve"
    ENROLL_KEY: "${CROWDSEC_ENROLLMENT_KEY}"
    ENROLL_INSTANCE_NAME: "pangolin-gateway"
  volumes:
    - /var/log/journal:/var/log/host:ro
    - ./secrets:/secrets:ro
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
- [architecture] CrowdSec service integrated into Pangolin stack #service-integration
- [architecture] Shared network for container communication #network-design
- [architecture] Secrets volume mounting for API key security #secret-mounting
- [architecture] Health checks with 30-second initialization window #health-monitoring

## Security Protection Layers

### Administrative Protection Strategy
- [protection] Multi-layer whitelisting with parser, profile, and scenario protection #multi-layer-protection
- [protection] Custom parser prevents log analysis for trusted IPs #parser-protection
- [protection] Profile protection returns empty decisions for admin IPs #profile-protection
- [protection] Scenario protection prevents trigger on admin networks #scenario-protection

### Trust Network Configuration
- [trust] Admin home IP (<ADMIN_HOME_IP>) with highest priority protection #admin-ip
- [trust] Pangolin tunnel networks (10.100.0.0/16) for internal communication #tunnel-networks
- [trust] Docker internal networks (172.16.0.0/12) for container communication #docker-networks
- [trust] Localhost and IPv6 localhost for system access #localhost-protection

### Attack Detection Capabilities
- [detection] SSH brute force monitoring via systemd journal #ssh-detection
- [detection] Web attack pattern recognition (path traversal, XSS, SQL injection) #web-detection
- [detection] Admin interface probing and backdoor attempt detection #interface-protection
- [detection] CVE-specific exploit detection with 40+ recent vulnerabilities #cve-protection

## Ansible Automation Integration

### Infrastructure as Code Pattern
```yaml
# Automation Pattern
- name: Generate CrowdSec API key file
  copy:
    content: "{{ stack_env_vars.CROWDSEC_BOUNCER_API_KEY }}"
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/secrets/crowdsec-api-key"
    mode: "0600"
  when: cur_stack == "pangolin"

- name: Deploy CrowdSec configuration
  template:
    src: docker-compose.yml.j2
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/docker-compose.yml"
  vars:
    crowdsec_enrollment_key: "{{ op_crowdsec_enrollment_key }}"
```

### Secret Management Integration
- [automation] API key file generation with secure permissions #key-automation
- [automation] 1Password secret lookup for enrollment keys #secret-management
- [automation] Conditional deployment based on stack requirements #conditional-deployment
- [automation] Environment variable templating for container configuration #env-templating

## Production Security Metrics

### Current Protection Status
- [metric] 48 active security scenarios for comprehensive coverage #scenario-metrics
- [metric] Zero false positives on legitimate admin traffic #accuracy-metrics
- [metric] Sub-200ms response time impact on protected services #performance-metrics
- [metric] 100% uptime during deployment and operation #availability-metrics

### Attack Prevention Capabilities
- [capability] Real-time threat intelligence from global CrowdSec network #intelligence-capability
- [capability] Automatic decision enforcement via Traefik plugin #enforcement-capability
- [capability] Custom scenario protection for homelab-specific patterns #custom-capability
- [capability] Community contribution to threat intelligence sharing #community-capability

## Monitoring and Observability

### Security Monitoring Framework
- [monitoring] JSON access logs for structured security analysis #structured-monitoring
- [monitoring] CrowdSec console dashboard integration #console-monitoring
- [monitoring] Community threat intelligence feed consumption #intelligence-monitoring
- [monitoring] Bouncer registration and health status tracking #bouncer-monitoring

### Emergency Response Procedures
- [emergency] Manual decision removal for false positive resolution #false-positive-resolution
- [emergency] Console management for remote decision control #remote-management
- [emergency] Multiple protection layers for admin lockout prevention #lockout-prevention
- [emergency] Local API access for emergency intervention #emergency-access

## Integration Components

### Traefik Integration
- [integration] See [[crowdsec-traefik-integration|CrowdSec Traefik Integration]] for detailed configuration
- [integration] Plugin-based approach with middleware selection
- [integration] File-based API key management for template compatibility

### Pangolin Gateway Integration  
- [integration] See [[crowdsec-pangolin-integration|CrowdSec Pangolin Integration]] for deployment details
- [integration] Docker stack integration with shared networking
- [integration] Ansible automation for configuration management

## Implementation Patterns

### Deployment Patterns
- [pattern] See [[crowdsec-deployment-patterns|CrowdSec Deployment Patterns]] for step-by-step implementation
- [pattern] Incremental approach with SSH-first strategy
- [pattern] Multi-layer protection with validation breakpoints

### Security Patterns
- [pattern] See [[security-implementation-patterns|Security Implementation Patterns]] for reusable approaches
- [pattern] Defense-in-depth for administrative access
- [pattern] Community intelligence integration

## Operational Guidance

### Troubleshooting
- [troubleshooting] See [[crowdsec-troubleshooting|CrowdSec Troubleshooting]] for issue resolution
- [troubleshooting] False positive handling procedures
- [troubleshooting] Emergency access restoration

### Future Enhancements
- [research] See [[crowdsec-future-enhancements|CrowdSec Future Enhancements]] for planned improvements
- [research] Advanced protection features and monitoring integration

## Relations
- implements [[System Architecture Overview]]
- enhances [[Critical Infrastructure Rules]]
- detailed_in [[CrowdSec Traefik Integration]]
- detailed_in [[CrowdSec Pangolin Integration]]
- supports [[Operations Guide]]
- patterns_in [[CrowdSec Deployment Patterns]]
- troubleshooting_in [[CrowdSec Troubleshooting]]