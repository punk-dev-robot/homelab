---
title: CrowdSec Deployment Patterns
type: note
permalink: patterns/crowd-sec-deployment-patterns
---

# CrowdSec Deployment Patterns

## Progressive Implementation Strategy

### Phase 1: Foundation (Day 1 Pattern)
**Objective**: Establish basic SSH protection with minimal complexity
**Duration**: 1 day
**Scope**: Single responsibility, conservative configuration

#### Core Pattern
```yaml
# Minimal Docker Compose Configuration
services:
  crowdsec:
    image: crowdsecurity/crowdsec:latest-debian
    environment:
      COLLECTIONS: "crowdsecurity/linux crowdsecurity/sshd"
      # No enrollment initially
    volumes:
      - /var/log:/var/log/host:ro
      - crowdsec-data:/var/lib/crowdsec/data
      - crowdsec-config:/etc/crowdsec
    ports:
      - "8080:8080"  # API access
      - "6060:6060"  # Metrics
```

#### Validation Checkpoints
1. **Container Health**: `docker ps | grep crowdsec`
2. **API Functionality**: `docker exec crowdsec cscli version`
3. **Log Processing**: `docker exec crowdsec cscli metrics`
4. **Manual Controls**: `docker exec crowdsec cscli decisions add/delete`

#### Success Criteria
- [success] Container starts and stays running #container-stability
- [success] SSH parsers loading and processing logs #log-processing
- [success] Manual ban/unban commands working #control-functionality
- [success] 30-second startup time acceptable #performance-baseline

### Phase 2: Intelligence & Protection (Day 2 Pattern)
**Objective**: Add community intelligence and admin protection
**Duration**: 1 day  
**Scope**: Enhanced detection with safety measures

#### Enhanced Configuration
```yaml
# Community Intelligence Integration
services:
  crowdsec:
    environment:
      COLLECTIONS: "crowdsecurity/linux crowdsecurity/sshd"
      ENROLL_KEY: "${CROWDSEC_ENROLLMENT_KEY}"
      ENROLL_INSTANCE_NAME: "pangolin-gateway"
```

#### Multi-Layer Admin Protection Pattern
```yaml
# Custom parser whitelist
name: admin-ip-parser-whitelist
filter: "evt.Parsed.remote_addr == '<ADMIN_HOME_IP>'"
onsuccess: next_stage

# Profile protection
name: admin-ip-profile  
filter: "evt.Meta.source_ip == '<ADMIN_HOME_IP>'"
decisions: []

# Scenario protection
name: admin-networks-whitelist
filter: "evt.Meta.source_ip matches '^(185\\.24\\.123\\.11|10\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.|192\\.168\\.)'"
onsuccess: next_stage
```

#### Validation Enhancements
1. **Community Connection**: `docker exec crowdsec cscli console status`
2. **Admin Protection**: Test admin IP access with simulated attacks
3. **Intelligence Feeds**: Verify threat data consumption
4. **Protection Depth**: Validate multiple protection layers

### Phase 3: Production Integration (Full Pattern)
**Objective**: Complete web protection with Traefik integration
**Duration**: 1-2 days
**Scope**: Production-ready security with selective protection

#### Complete Architecture Pattern
```yaml
# Production Docker Compose
services:
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
      - pangolin-network  # Shared with Traefik
    healthcheck:
      test: ["CMD", "cscli", "version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

#### Traefik Integration Pattern
```yaml
# Plugin Configuration
experimental:
  plugins:
    crowdsec-bouncer:
      moduleName: "github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin"
      version: "v1.3.5"

# Middleware Configuration
middlewares:
  crowdsec-bouncer:
    plugin:
      crowdsec-bouncer:
        enabled: true
        logLevel: "INFO"
        crowdsecLapiKeyFile: "/secrets/crowdsec-api-key"
        clientTrustedIPs:
          - "10.0.0.0/8"
          - "172.16.0.0/12"
          - "192.168.0.0/16"
          - "<ADMIN_HOME_IP>/32"
```

#### Production Validation Framework
1. **Architecture Health**: All containers in shared network
2. **Attack Detection**: 48+ active scenarios loaded
3. **Protection Testing**: Real attack simulation with curl
4. **Performance Impact**: Sub-200ms response time maintained
5. **Selective Protection**: Internal services unaffected

## Implementation Anti-Patterns (Avoid These)

### Common Mistakes
- [anti-pattern] **Big Bang Deployment** #avoid-complexity
  - **Problem**: Implementing all features simultaneously
  - **Solution**: Use progressive implementation approach
  
- [anti-pattern] **Template Syntax in API Keys** #avoid-template-conflicts
  - **Problem**: Traefik template conflicts with Go templates
  - **Solution**: Use file-based API key approach
  
- [anti-pattern] **Universal Middleware Application** #avoid-internal-blocking
  - **Problem**: Applying CrowdSec to all services including internal
  - **Solution**: Selective middleware application pattern

- [anti-pattern] **Immediate Enrollment** #avoid-early-complexity  
  - **Problem**: Adding enrollment before basic functionality verified
  - **Solution**: Establish foundation first, then add intelligence

### Configuration Pitfalls
```yaml
# WRONG: Template syntax conflicts
crowdsecLapiKey: "{{ .Env.CROWDSEC_API_KEY }}"

# CORRECT: File-based approach
crowdsecLapiKeyFile: "/secrets/crowdsec-api-key"

# WRONG: Universal protection
http:
  routers:
    all-services:
      middlewares:
        - crowdsec-bouncer  # Blocks internal services

# CORRECT: Selective protection
http:
  routers:
    external-service:
      middlewares:
        - crowdsec-bouncer
    internal-service:
      middlewares: []  # No CrowdSec protection
```

## Ansible Automation Patterns

### Secret Management Pattern
```yaml
# 1Password Integration
- name: Generate CrowdSec API key file
  copy:
    content: "{{ stack_env_vars.CROWDSEC_BOUNCER_API_KEY }}"
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/secrets/crowdsec-api-key"
    mode: "0600"
  when: cur_stack == "pangolin"

- name: Template enrollment key in docker-compose
  template:
    src: pangolin.yml.j2
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/pangolin.yml"
  vars:
    crowdsec_enrollment_key: "{{ op_crowdsec_enrollment_key }}"
```

### Conditional Deployment Pattern
```yaml
# Stack-specific deployment
- name: Deploy CrowdSec configuration
  template:
    src: "{{ item }}.j2"
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/{{ item }}"
  loop:
    - docker-compose.yml
    - config/crowdsec/acquis.yaml
  when: 
    - cur_stack == "pangolin"
    - crowdsec_enabled | default(false)
```

## Testing and Validation Patterns

### Progressive Testing Strategy
#### Phase 1 Testing
```bash
# Basic functionality
docker exec crowdsec cscli version
docker exec crowdsec cscli parsers list | grep ssh
docker exec crowdsec cscli metrics

# Manual decision testing
docker exec crowdsec cscli decisions add --ip 1.2.3.4 --type ban -d 1h
docker exec crowdsec cscli decisions list
docker exec crowdsec cscli decisions delete --ip 1.2.3.4
```

#### Phase 2 Testing
```bash
# Community connection
docker exec crowdsec cscli console status
docker exec crowdsec cscli bouncers list

# Admin protection testing
# (Simulate attack from admin IP - should be blocked at parser level)
```

#### Phase 3 Testing  
```bash
# Web protection testing
curl -H "User-Agent: sqlmap" https://protected-service.domain.com
curl https://protected-service.domain.com/../../../etc/passwd
curl https://protected-service.domain.com/.env

# Performance testing
time curl -s https://protected-service.domain.com > /dev/null
```

## Configuration Management Patterns

### File Structure Pattern
```
project/
├── files/gateway-vps/pangolin/
│   ├── pangolin.yml                 # Main docker-compose
│   ├── secrets/
│   │   └── crowdsec-api-key         # Generated by Ansible
│   └── config/
│       ├── traefik/
│       │   ├── traefik_config.yml   # Plugin configuration
│       │   └── dynamic_config.yml   # Middleware configuration
│       └── crowdsec/
│           ├── acquis.yaml          # Log acquisition
│           ├── profiles.yaml        # Remediation profiles
│           └── whitelists.yaml      # Custom whitelists
```

### Version Control Pattern
```bash
# Branch strategy
git checkout -b crowdsec-integration    # Feature branch
git commit -m "feat: add Phase 1 SSH protection"
git commit -m "feat: add Phase 2 community intelligence"  
git commit -m "feat: add Phase 3 web protection"
git checkout main && git merge crowdsec-integration
```

## Deployment Verification Patterns

### Health Check Sequence
1. **Container Status**: All containers running and healthy
2. **Network Connectivity**: Traefik can reach CrowdSec API
3. **Log Processing**: CrowdSec parsing logs correctly
4. **Decision Enforcement**: Bouncer applying decisions
5. **Performance Impact**: Response times within acceptable range

### Rollback Pattern
```bash
# Emergency rollback sequence
docker compose down                          # Stop services
git checkout HEAD~1 -- docker-compose.yml  # Revert configuration  
docker compose up -d                        # Restart without CrowdSec
# Verify service restoration
```

### Monitoring Pattern
```bash
# Regular health monitoring
docker exec crowdsec cscli status
docker exec crowdsec cscli bouncers list
docker exec crowdsec cscli decisions list | wc -l
docker stats --no-stream crowdsec
```

## Success Metrics and KPIs

### Phase 1 Success Metrics
- [metric] Container uptime: >99% #uptime-target
- [metric] SSH brute force detection: >0 events per day #detection-rate
- [metric] False positive rate: 0% on admin IP #accuracy-target
- [metric] Deployment time: <1 hour from start to verification #speed-target

### Phase 2 Success Metrics  
- [metric] Community intelligence: Active feed consumption #intelligence-active
- [metric] Admin protection: 0 false positives across 3 protection layers #admin-safety
- [metric] Threat detection: Enhanced scenarios from community #threat-coverage

### Phase 3 Success Metrics
- [metric] Web attack detection: >40 active scenarios #scenario-coverage
- [metric] Response time impact: <200ms additional latency #performance-target
- [metric] Service availability: 100% uptime for legitimate users #availability-target
- [metric] Attack prevention: Verified blocking of common attack patterns #protection-verified

## Relations
- implements [[CrowdSec Security Architecture]]
- supports [[CrowdSec Traefik Integration]]
- supports [[CrowdSec Pangolin Integration]]  
- troubleshooting_in [[CrowdSec Troubleshooting]]