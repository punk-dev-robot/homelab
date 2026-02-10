# Homelab Infrastructure - Active Context

## 🔴 Critical Rules

### All Infrastructure
- 🚨 MANDATORY: Run appropriate test before commits:
  - `ansible-playbook tests/suites/gateway_vps_test_suite.yml` (gateway changes)
  - `ansible-playbook tests/suites/homelab_vms_test_suite.yml` (homelab changes)
- ❌ NEVER: `pip install` on Arch (use `uv tool install` instead)

### Homelab VMs (apps-vm, media-vm, obs-vm)
- ✅ ALWAYS: Services extend `base` or `socket-base` from common.yml
- 🔧 Access methods: 
  - Direct: .lan addresses (apps.lan, media.lan, obs.lan)
  - Caddy proxy: .lab.nobasura.org (via OpnSense/Unbound)
- 🐳 Container standardization mandatory

### Gateway VPS (External Infrastructure)
- 🚨 NEVER make direct changes to gateway-vps (use ansible only)
- 🔒 Special: CrowdSec protection, external IP, ubuntu user
- 🌐 External access: .nobasura.org (Traefik + Pangolin)

### Proxmox (Hypervisor Level)
- 📚 Configuration preserved for reference only (not active)
- 💾 VM snapshots before major changes (when using Proxmox)

## 🟢 Current Status

**Status**: Production operational, all 27+ services accessible  
**Latest**: Container availability improvements completed (June 11, 2025)  
**Memory**: Migrated from Atlas MCP to Basic Memory MCP

## 🔗 Knowledge Base Links

- **Architecture**: `memory://homelab/reference/infrastructure-architecture-patterns`
- **Operations**: `memory://homelab/reference/operations-guide`
- **Troubleshooting**: `memory://homelab/reference/troubleshooting-guide`
- **Patterns**: `memory://homelab/patterns/container-standardization-patterns`
- **Quick Fixes**: `memory://homelab/core/common-issues-and-quick-fixes`
- **Commands**: `memory://homelab/patterns/ansible-commands-quick-reference`

## 📋 Essential Commands

```bash
# Testing (mandatory pre-commit - choose appropriate scope)
ansible-playbook ansible/tests/suites/gateway_vps_test_suite.yml         # Gateway VPS auth/SSO testing
ansible-playbook ansible/tests/suites/homelab_vms_test_suite.yml       # Homelab VM service testing

# Targeted deployments (recommended approach)
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml    # Local VMs (apps-vm, media-vm, obs-vm)
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml        # Gateway VPS (includes auth bypass)

# Initial infrastructure setup (run once)
ansible-playbook -i ansible/inventory.yml ansible/provision.yml         # Basic setup (hostname, utils)

# Service restart
ansible gateway -a "docker restart traefik"                     # Restart gateway services
ansible docker -a "docker restart homepage"                         # Restart homelab services

# Container validation  
ansible-playbook -i ansible/inventory.yml ansible/tests/validation/container_standardization.yml
```

## 🎯 Current Work Context

- Atlas MCP temporarily disabled for debugging
- Memory system successfully migrated to Basic Memory MCP
- All detailed documentation accessible via `memory://` URLs
- Zero ansible-lint violations maintained

## 🌐 Service Access

- **Homepage**: <https://homepage.lab.nobasura.org> (service index)
- **Monitoring**: <https://grafana.lab.nobasura.org>
- **Logs**: <https://dozzle.lab.nobasura.org>

## 📚 Archive References

- **Completed Tasks**: `memory://homelab/archive/completed-tasks-history`
- **Technical Investigations**: `memory://homelab/archive/technical-investigations-archive`
- **Implementation Details**: `memory://homelab/archive/implementation-details-archive`

## 📋 Documentation Planning

### Current Workflow
- **Active Context**: CLAUDE.md (this file) - Essential rules and quick access
- **Knowledge Base**: Basic Memory MCP - Searchable detailed documentation
- **Quick Access**: Use `memory://` URLs for specific topics

### Adding New Documentation
1. Use Basic Memory tools to create/update notes in appropriate categories:
   - `homelab/core/` - Critical operational knowledge
   - `homelab/patterns/` - Reusable implementation patterns  
   - `homelab/reference/` - Detailed guides and procedures
   - `homelab/archive/` - Historical context and completed work

2. Update CLAUDE.md memory:// links if new essential topics emerge

---

*All detailed documentation, architecture patterns, troubleshooting guides, and historical context are stored in Basic Memory and accessible via the memory:// URLs above.*

