# Homelab Infrastructure - Infrastructure Project

## 💾 Memory Configuration

**Memory Project**: `lab-feat` (must be set as active on session start)

## 📚 Memory Organization

**Structure**: Standard 6-folder organization with purposeful content

```
memory/
├── architecture/     # System design and patterns
├── decisions/        # ADRs and critical choices
├── guides/          # Step-by-step procedures
├── patterns/        # Reusable implementations
├── research/        # Future investigations
└── archive/         # Historical context
```

**Quality**: Findable, actionable, well-linked, maintained

## 🔴 Critical Rules

### Infrastructure Workflow

- 🚨 MANDATORY: Run tests before commits:
  - `ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml` (gateway changes) ✅
  - `ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml` (homelab changes) ✅
  - `ansible-playbook -i ansible/inventory.yml ansible/tests/validation/container_standardization.yml` (container standards) ✅
- 🔧 Deployment: Use targeted playbooks - `deploy_docker.yml` for local VMs, `deploy_vps.yml` for gateway
- 📦 Dependencies: Use `uv tool install` on Arch (never `pip install`)

### Infrastructure Standards

- ✅ ALWAYS: Docker services extend `base` or `socket-base` from common.yml
- 🔒 Security: Never direct changes to gateway-vps, use ansible only
- 📋 Quality: Container standardization mandatory, VM snapshots before major changes

### Service Architecture

- **Homelab VMs**: Direct .lan + Caddy proxy .lab.nobasura.org
- **Gateway VPS**: CrowdSec protection, external .nobasura.org (Traefik + Pangolin)
- **Proxmox**: Configuration preserved for reference only (not active)

## 🟢 Current Status

**Version**: Production | **Environment**: Homelab + Gateway VPS
**Latest Change**: CrowdSec bouncer fix - entrypoint-level middleware for all routes (March 23, 2026)
**Health**: All 27+ services accessible, zero ansible-lint violations

## 🔗 Quick Navigation

- **Architecture**: `memory://architecture/system-architecture-overview`
- **Setup Guide**: `memory://guides/operations-guide`
- **Development**: `memory://guides/troubleshooting-guide`
- **Patterns**: `memory://patterns/container-standardization-patterns`
- **Critical Rules**: `memory://decisions/critical-infrastructure-rules`

## 🔗 Detailed Knowledge Base

- **Container Architecture**: `memory://architecture/container-service-architecture`
- **Container Decisions**: `memory://decisions/adr-001-container-availability-improvements`
- **Commands**: `memory://patterns/ansible-commands-quick-reference`

## 📋 Essential Commands

```bash
# Testing Infrastructure (mandatory pre-commit)
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml         # Test gateway VPS ✅
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml       # Test homelab VMs ✅
ansible-playbook -i ansible/inventory.yml ansible/tests/validation/container_standardization.yml  # Container standards ✅
ansible-playbook -i ansible/inventory.yml ansible/tests/validation/crowdsec_firewall_bouncer.yml # CrowdSec validation
ansible-lint ansible/                                       # Check playbook quality

# Quick smoke tests (use --tags smoke for faster validation)
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml --tags smoke
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml --tags smoke

# Build & Deploy
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml    # Deploy local VMs
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml        # Deploy gateway VPS
ansible gateway -a "docker restart traefik"                     # Restart gateway services
ansible docker -a "docker compose -f /opt/docker/compose/homepage/compose.yml restart homepage"  # Restart homelab services

# System Health
systemctl status                                     # Check local system health
```

## 🌐 Environment Access

- **Homepage**: <https://homepage.lab.nobasura.org> (service index)
- **Monitoring**: <https://grafana.lab.nobasura.org>
- **Logs**: <https://dozzle.lab.nobasura.org>

## 🔬 Infrastructure Development

- **Operational Procedures**: `memory://guides/operations-guide` - daily management workflows
- **System Design**: `memory://architecture/system-architecture-overview` - infrastructure patterns
- **Troubleshooting**: `memory://guides/troubleshooting-guide` - problem resolution steps
- **Container Standards**: `memory://patterns/container-standardization-patterns` - implementation guidelines
- **SSO Research**: `memory://research/sso-implementation-research-overview` - future authentication

## 📚 Archive & History

- **Completed Tasks**: `memory://archive/completed-tasks-history`
- **Technical Investigations**: `memory://archive/technical-investigations-archive`
- **Implementation Details**: `memory://archive/implementation-details-archive`
- **Deployment Issues**: `memory://archive/deployment-issues-archive`

@./TASKMASTER.md
