# Ansible Commands Quick Reference

## Testing Commands (Pre-Commit Mandatory)

```bash
# 🚨 MANDATORY: Before infrastructure commits
ansible-playbook test_gateway_vps.yml               # Gateway VPS auth/SSO testing
ansible-playbook test_homelab_vms.yml               # Homelab VM service testing (🚧 WIP)

# Quick smoke test (30 seconds)
ansible-playbook test_gateway_vps.yml --tags smoke

# Security validation only
ansible-playbook test_gateway_vps.yml --tags security

# Container standardization validation
ansible-playbook validate_container_standardization.yml
```

## Deployment Commands

```bash
# Homelab VMs (apps-vm, media-vm, obs-vm)
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml

# Gateway VPS specific
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml

# Tunnel infrastructure (SAFE - requires explicit flag)
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml -e deploy_tunnels=true

# Target specific VM with tunnels
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml -e deploy_tunnels=true --limit media-vm

# Service restart examples
ansible gateway -a "docker restart traefik"
ansible docker -a "docker restart homepage"
```

## Troubleshooting Commands

```bash
# Service status check
ansible-playbook -i inventory.yml restart_services.yml --check

# Container logs (example)
ansible gateway-vps -m shell -a "docker logs traefik --tail 50"

# Connectivity test
ansible-playbook test_gateway_vps.yml --tags connectivity

# Check service health
ansible all -m ping
```

## Development & Linting

```bash
# Install ansible requirements
ansible-galaxy install -r ansible/requirements.yaml --force

# Run ansible linting
ansible-lint ansible/

# Check syntax
ansible-playbook site.yml --syntax-check

# Dry run (check mode)
ansible-playbook site.yml --check
```

## Target Patterns

```bash
# Target specific host
--limit gateway-vps
--limit apps-vm
--limit media-vm
--limit obs-vm

# Target groups
--limit docker  # All VMs
--limit proxmox # Proxmox hosts

# Multiple targets
--limit "apps-vm,media-vm"
```

## Tag Usage

```bash
# Common tags
--tags smoke        # Quick tests
--tags security     # Security tests only
--tags auth-bypass  # Auth bypass deployment
--tags critical     # Critical tests only

# Skip tags
--skip-tags slow
```

## Related Notes
- [Operations Guide](../reference/operations-guide.md) - Detailed operational procedures
- [Critical Infrastructure Rules](../core/critical-infrastructure-rules.md) - Must-follow rules
- [Troubleshooting Guide](../reference/troubleshooting-guide.md) - Issue resolution