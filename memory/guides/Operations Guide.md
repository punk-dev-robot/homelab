---
title: Operations Guide
type: note
permalink: guides/operations-guide
tags:
- '["operations"'
- '"procedures"'
- '"infrastructure-management"'
- '"troubleshooting"]'
---

# Operations Guide

## Critical Operational Procedures
- [purpose] Essential procedures for running homelab infrastructure #operations
- [scope] Gateway VPS, homelab VMs, testing, deployment, troubleshooting #comprehensive
- [audience] Infrastructure operators and maintainers #operators

## Infrastructure Immutability Procedures

### Gateway VPS Operations
- [rule] NEVER make direct changes to gateway-vps #immutability
- [reasoning] Audit trail preservation, configuration drift prevention #audit-trail
- [reasoning] Infrastructure as Code compliance #iac-compliance

**Correct Approach**:
```bash
# ✅ Ansible automation only
ansible-playbook -i inventory.yml deploy_vps.yml --tags auth-bypass
ansible-playbook -i inventory.yml restart_services.yml --limit gateway-vps
```

**Prohibited Actions**:
```bash
# ❌ Manual changes bypass version control
ssh gateway-vps "vim /some/config/file"
ansible gateway-vps -m shell -a "docker compose restart traefik"
```

## Testing Framework Procedures

### Architecture-First Testing Philosophy
- [principle] Tests validate architecture, not accommodate bugs #testing-philosophy
- [principle] Define expected behavior, don't accept arbitrary responses #expected-behavior

```yaml
# ❌ Wrong: Accept anything to pass
status_code: [200, 302, 401, 403]

# ✅ Right: Define expected behavior  
expected_statuses: [200, 307]  # 200=direct, 307=app login
```

### Pre-Commit Testing (MANDATORY)
- [procedure] Run before every infrastructure commit #pre-commit
- [requirement] Gateway VPS testing is mandatory #gateway-testing
- [requirement] Homelab VM testing when available #homelab-testing

**Essential Commands**:
```bash
# 🚨 MANDATORY: Before infrastructure commits
ansible-playbook test_gateway_vps.yml               # Gateway VPS auth/SSO testing
ansible-playbook test_homelab_vms.yml               # Homelab VM service testing (🚧 WIP)

# Quick smoke test (30 seconds)
ansible-playbook test_gateway_vps.yml --tags smoke

# Security validation only
ansible-playbook test_gateway_vps.yml --tags security
```

## Deployment Procedures

### Full Infrastructure Deployment
- [procedure] Complete infrastructure deployment across all systems #full-deployment

```bash
# Full infrastructure deployment
ansible-playbook -i inventory.yml site.yml

# Specific VM deployment
ansible-playbook -i inventory.yml deploy_vps.yml --limit gateway-vps

# Service-specific updates
ansible-playbook -i inventory.yml deploy_vps.yml --tags auth-bypass
```

### Service Management Procedures
- [procedure] Individual service and stack management #service-management

```bash
# Service restart with check mode
ansible-playbook -i inventory.yml restart_services.yml --check

# Container log inspection
ansible gateway-vps -m shell -a "docker logs traefik --tail 50"

# Connectivity testing
ansible-playbook test_gateway_vps.yml --tags connectivity
```

## Quality Assurance Procedures

### Ansible Linting Standards
- [status] Zero violations maintained across 60 core files #lint-compliance
- [achievement] 159→0 violations resolved #lint-achievement

**Critical Standards**:
- [standard] No trailing whitespace in YAML #yaml-formatting
- [standard] Files end with newline #file-formatting
- [standard] Role-prefixed variables to prevent conflicts #variable-naming
- [standard] Capitalized handler names #handler-naming
- [standard] FQCN usage for community collections #fqcn-usage

**Linting Procedure**:
```bash
# Install requirements first
ansible-galaxy install -r ansible/requirements.yaml --force

# Run linting validation
ansible-lint ansible/
```

### System Administration Standards
- [rule] NEVER use pip install on Arch Linux #package-management
- [reasoning] Breaks system package management #system-integrity
- [solution] ALWAYS use uv tool install for Python tools #isolated-tools

**Correct Tool Installation**:
```bash
# ✅ Isolated environment installation
uv tool install package-name

# ❌ System-breaking approach
pip install package-name
```

## Secret Management Procedures

### 1Password Integration Pattern
- [procedure] Secure secret management via 1Password vault #secret-management
- [vault] Homelab vault for all infrastructure secrets #vault-organization

```yaml
# Template with secret lookup
config_value: "{{ lookup('community.general.onepassword', 'SECRET_NAME', vault='Homelab') }}"

# Secure template processing
- name: "Process config template"
  template:
    src: config.yml.j2
    dest: /path/config.yml
  no_log: true  # Prevent secret exposure in logs
```

### Secret Organization Standards
- [standard] Clear, descriptive secret names #naming-convention
- [standard] Environment injection for container secrets #env-injection
- [standard] Zero secrets in version control #no-hardcoding

## Communication & Notification Procedures

### Email/Notification System Operations
- [system] Resend SMTP integration for notifications #smtp-integration
- [domain] notify.nobasura.org for system notifications #notification-domain
- [flow] Admin invite → User email → Password setup → Access #user-onboarding

**DNS Requirements**:
- [requirement] SPF record to authorize Resend #spf
- [requirement] DKIM for email authentication #dkim  
- [requirement] DMARC for policy enforcement #dmarc

## Monitoring & Alerting Procedures

### Key Service Access Points
- [service] Grafana: Primary dashboard (grafana.lab.nobasura.org) #grafana
- [service] Uptime Kuma: Service monitoring (uptime.lab.nobasura.org) #uptime-monitoring
- [service] Gotify: Notifications (gotify.lab.nobasura.org) #notifications
- [service] Dozzle: Container logs (dozzle.lab.nobasura.org) #log-viewing

### Performance Targets & Monitoring
- [target] Tunnel Latency: <5ms via Pangolin #latency-target
- [target] Service Accessibility: 100% via *.nobasura.org #accessibility-target
- [automation] Container Updates: Automated via Watchtower #update-automation
- [security] Security Response: Real-time via CrowdSec #security-monitoring

## Troubleshooting Procedures

### Infrastructure Health Diagnostics
```bash
# Full connectivity test
ansible-playbook test_infrastructure.yml --tags connectivity

# Service availability check
ansible-playbook test_infrastructure.yml --tags smoke

# Security validation
ansible-playbook test_infrastructure.yml --tags security
```

### Service-Specific Debugging
```bash
# Traefik routing diagnostics
docker logs traefik | grep ERROR

# Pangolin connectivity check
docker logs pangolin | tail -50

# CrowdSec security decisions
sudo cscli decisions list

# Neo4j memory usage monitoring
docker stats neo4j
```

### Network Troubleshooting
```bash
# Container networking inspection
docker network inspect NETWORK_NAME

# Port accessibility testing
nmap -p PORT HOST

# DNS resolution verification
dig SERVICE.nobasura.org
```

## Emergency Procedures

### Service Recovery Procedures
- [procedure] Container restart and recovery #service-recovery
- [procedure] Configuration rollback via git #rollback-procedure
- [procedure] Manual intervention protocols #manual-intervention

### Escalation Procedures
- [procedure] When to bypass automation #escalation-criteria
- [procedure] Manual override procedures #manual-override
- [procedure] Recovery documentation requirements #recovery-documentation

## Relations
- implements [[Critical Infrastructure Rules]]
- uses [[System Architecture Overview]]
- references [[Ansible Commands Quick Reference]]
- supports [[Troubleshooting Guide]]