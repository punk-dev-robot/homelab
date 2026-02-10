---
title: Troubleshooting Guide
type: note
permalink: guides/troubleshooting-guide
tags:
- '["troubleshooting"'
- '"debugging"'
- '"problem-resolution"'
- '"diagnostics"]'
---

# Troubleshooting Guide

## Common Issues & Solutions
- [purpose] Systematic problem resolution for homelab infrastructure #troubleshooting
- [scope] Ansible testing, service connectivity, authentication, deployment #comprehensive
- [approach] Root cause analysis with proven solutions #systematic

## Ansible Testing Failures

### User-Agent Rejection (arr stack)
- [problem] *arr applications reject `User-Agent: ansible-httpget` #user-agent-issue
- [impact] Jellyseerr, Sonarr, Radarr return 400 Bad Request #http-errors
- [root-cause] Applications filter non-browser user agents #filtering

**Solution**:
```yaml
headers:
  User-Agent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
```

### Test Framework Status Code Issues
- [problem] Tests failing due to unexpected status codes #status-code-issues
- [approach] Systematic investigation pattern #investigation-pattern

**Investigation Steps**:
1. [step] Check direct access: `curl -I https://service.nobasura.org` #direct-test
2. [step] Verify bypass: `curl -H "traefik-auth-bypass-key: KEY" https://service.nobasura.org` #bypass-test
3. [step] Expected: 200 (direct) or 307 (app login redirect) #expected-results

## Neo4j Browser Issues

### HTTPS Protocol Problems
- [problem] "Database access not available" via HTTPS #neo4j-https-issue
- [root-cause] Browser enforces `bolt+s://` with HTTPS access #protocol-enforcement
- [impact] Admin interface inaccessible via external HTTPS #access-blocked

**Solutions**:
- [solution] Admin Interface: `http://apps.lan:7474/browser/` (internal HTTP) #internal-access
- [solution] External API: `https://neo4j.lab.nobasura.org` (HTTPS via Caddy) #external-access
- [authentication] 1Password for both access methods #credential-management

### Memory Configuration Issues
- [issue] Memory allocation problems affecting performance #memory-issues
- [configuration] Proper heap and pagecache sizing #memory-config

**Configuration**:
```yaml
environment:
  - NEO4J_server_memory_pagecache_size=1G
  - NEO4J_server_memory_heap_max__size=1G
```

## Pangolin Connectivity Issues

### Component Version Conflicts
- [problem] Auth headers not working with mobile bypass #version-conflict
- [impact] Mobile applications cannot authenticate #mobile-auth-failure
- [solution] Pin specific compatible versions #version-pinning

**Version Requirements**:
- [version] Pangolin: 1.5.0 #pangolin-version
- [version] Badger: 1.2.0 (critical auth header fix) #badger-version  
- [version] Newt: 1.2.1 (stability improvements) #newt-version

### Site Registration Problems
- [problem] Services not registering with Pangolin properly #registration-issues
- [debug] Systematic debugging approach #debug-process

**Debug Steps**:
1. [debug] Check Pangolin logs: `docker logs pangolin` #log-check
2. [debug] Verify API connectivity: `curl http://pangolin:3001/api/v1/status` #api-test
3. [debug] Check resource registration in Pangolin UI #ui-verification

### 502 Gateway Issues - CRITICAL ARCHITECTURAL SOLUTION
- [problem] 502 Bad Gateway timeouts preventing service access #gateway-timeouts
- [root-cause] Network namespace isolation between Pangolin and Gerbil services #namespace-isolation
- [impact] VPS proxy services unable to reach tunnel targets #connectivity-failure

**BREAKTHROUGH SOLUTION**:
- [solution] Network mode sharing: `network_mode: service:gerbil` in pangolin.yml #network-mode-fix
- [solution] Remove circular dependency: eliminate `depends_on` between services #dependency-resolution
- [solution] Unified network stack: all proxy components share network namespace #namespace-sharing

**Implementation**:
```yaml
# /files/gateway-vps/pangolin/pangolin.yml
pangolin:
  image: fosrl/pangolin:1.4.0
  container_name: pangolin
  restart: unless-stopped
  network_mode: service:gerbil  # KEY FIX: Share network with exit node
  volumes:
    - ./config:/app/config
    - pangolin_db:/app/config/db

gerbil:
  image: fosrl/gerbil:1.0.0
  container_name: gerbil
  restart: unless-stopped
  # Removed: depends_on pangolin (prevents circular dependency)
```

**Verification**:
- [verification] docker ps shows Pangolin/Traefik with no named network #network-verification
- [verification] Response progression: 502 Bad Gateway → 404 Not Found → Working proxy #progress-verification
- [verification] Proxy chain established: Traefik → Pangolin → Target (~40ms) #chain-verification

**Root Cause Analysis**:
- [analysis] VPS runs proxy services (Traefik + Pangolin API) #proxy-architecture
- [analysis] Local machine has WireGuard tunnel access to targets #tunnel-access
- [analysis] Architecture mismatch: VPS services couldn't reach tunnel targets #mismatch-issue
- [analysis] Network namespace sharing resolves connectivity gap #connectivity-solution

## Traefik Routing Issues

### Priority Routing Failures
- [problem] Auth bypass routes not matching correctly #priority-routing-issue
- [impact] Mobile/API access fails to bypass authentication #bypass-failure

**Debug Approach**:
1. [debug] Check router priority values (bypass should be >300) #priority-check
2. [debug] Verify header format: `traefik-auth-bypass-key` #header-format
3. [debug] Test header: `curl -H "traefik-auth-bypass-key: ACTUAL_KEY" URL` #header-test

### Dynamic Configuration Loading
- [issue] Traefik not loading configuration changes #config-loading
- [check] Traefik loads from `traefik_rules/dynamic_config.yml` #config-location
- [solution] Restart traefik container to reload config #reload-solution

## CrowdSec Protection Issues

### False Positive Blocking
- [problem] Legitimate traffic being blocked by CrowdSec #false-positives
- [impact] Users unable to access services #access-blocked

**Resolution Steps**:
```bash
# Check current decisions
sudo cscli decisions list

# Remove specific IP blocking
sudo cscli decisions delete --ip IP_ADDRESS

# Add to admin whitelist
# Edit whitelist in CrowdSec config
```

### Service Startup Failures
- [problem] CrowdSec service fails to start #startup-failure
- [debug] Container logs reveal configuration issues #log-analysis

**Debug Process**:
```bash
# Check service logs
docker logs crowdsec

# Common issues: parser/scenario syntax errors
# Validate YAML syntax in config files
```

## 1Password Integration Problems

### Lookup Failures
- [problem] `community.general.onepassword lookup could not find` #lookup-failure
- [impact] Ansible templates fail to process secrets #template-failure

**Debug Steps**:
```bash
# Check vault access
op vault list

# Verify item exists
op item list --vault Homelab

# Test direct lookup
op item get "ITEM_NAME" --vault Homelab
```

### Template Processing Issues
- [problem] Secrets not resolving in Ansible templates #template-processing
- [impact] Services deploy with missing configuration #config-incomplete

**Verification Checklist**:
1. [check] Ansible vault access: `op whoami` #vault-access
2. [check] Template syntax: Jinja2 formatting correct #syntax-check
3. [check] Use `no_log: true` for sensitive templates #security-check

## Docker Stack Issues

### Container Startup Failures
- [problem] Containers fail to start or enter restart loops #startup-failure
- [debug] Systematic container debugging approach #container-debug

**Debug Pattern**:
```bash
# Check container logs
docker logs CONTAINER_NAME

# Verify networking
docker network ls

# Check volumes
docker volume ls

# Test inter-container connectivity
docker exec CONTAINER ping TARGET
```

### Volume Permission Issues
- [problem] Permission denied errors in containers #permission-issues
- [root-cause] Host directory ownership mismatch #ownership-mismatch

**Solution**:
```bash
# Fix directory ownership
sudo chown -R 1000:1000 /path/to/volume
```

## Ansible Linting Violations

### Collection Dependencies Missing
- [error] `Couldn't resolve module/action` errors #dependency-missing
- [cause] Required Ansible collections not installed #missing-collections

**Fix**:
```bash
# Install all requirements
ansible-galaxy install -r ansible/requirements.yaml --force
```

### YAML Formatting Issues
- [issues] Common formatting problems affecting linting #yaml-issues

**Common Problems**:
- [issue] Trailing whitespace in YAML files #whitespace
- [issue] Missing newline at end of file #eof-newline
- [issue] Incorrect YAML indentation #indentation

**Prevention**: Use editor automation for consistent formatting #auto-formatting

## Diagnostic Command Reference

### Infrastructure Health Checks
```bash
# Full connectivity validation
ansible-playbook test_infrastructure.yml --tags connectivity

# Service availability testing
ansible-playbook test_infrastructure.yml --tags smoke

# Security validation
ansible-playbook test_infrastructure.yml --tags security
```

### Service-Specific Diagnostics
```bash
# Traefik routing analysis
docker logs traefik | grep ERROR

# Pangolin connectivity status
docker logs pangolin | tail -50

# CrowdSec security decisions
sudo cscli decisions list

# Neo4j performance monitoring
docker stats neo4j
```

### Network Troubleshooting Commands
```bash
# Container network inspection
docker network inspect NETWORK_NAME

# Port accessibility testing
nmap -p PORT HOST

# DNS resolution verification
dig SERVICE.nobasura.org
```

## Escalation Procedures

### When to Escalate Issues
- [criteria] Infrastructure-wide service failures #escalation-criteria
- [criteria] Security incidents requiring immediate response #security-escalation
- [criteria] Data integrity concerns #data-escalation

### Manual Override Procedures  
- [procedure] Bypassing automation when necessary #manual-override
- [procedure] Emergency access procedures #emergency-access
- [procedure] Recovery documentation requirements #recovery-docs

## Prevention Strategies

### Proactive Monitoring
- [strategy] Regular health checks prevent issues #proactive-monitoring
- [strategy] Automated testing catches problems early #early-detection
- [strategy] Performance monitoring identifies trends #trend-analysis

### Configuration Management
- [strategy] Version control prevents configuration drift #version-control
- [strategy] Automated validation catches errors #automated-validation
- [strategy] Documentation prevents knowledge loss #documentation

## Relations
- supports [[Operations Guide]]
- uses [[System Architecture Overview]]
- references [[Critical Infrastructure Rules]]
- integrates_with [[Ansible Commands Quick Reference]]