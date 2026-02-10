<p align="center">
  <img src="images/fsociety_transparent.png" alt="fsociety" />
</p>

<h1 align="center">Homelab</h1>

<p align="center">
  Ansible-managed homelab infrastructure running 49+ Docker services across 3 VMs and a gateway VPS, with 1Password for secrets management.
</p>

---

## Architecture

A hybrid infrastructure spanning a local Proxmox cluster and a remote Oracle Cloud VPS, connected via encrypted WireGuard tunnels.

**Proxmox VE Cluster**
- OPNsense firewall with HA failover
- TrueNAS ZFS-based network storage
- Proxmox Backup Server for automated VM backups

**Gateway VPS (Oracle Cloud)**
- Traefik reverse proxy with automatic HTTPS
- Pangolin + Gerbil WireGuard tunnels for secure homelab connectivity
- CrowdSec collaborative intrusion prevention
- Authentik SSO and identity provider

**Docker VMs**
- **Apps** (apps.lan) -- AI services (LiteLLM, OpenWebUI), tools (Firecrawl, Karakeep), databases
- **Media** (media.lan) -- Jellyfin streaming, full Servarr ecosystem (Radarr, Sonarr, Prowlarr, and more)
- **Observability** (obs.lan) -- Grafana, Prometheus, Loki monitoring stack, Beszel, Uptime Kuma

**Routing**
- Internal: Caddy proxy serving `*.lab.nobasura.org`
- External: Traefik + Pangolin serving `*.nobasura.org`

## Tech Stack

| Category | Tools |
|----------|-------|
| Infrastructure | Proxmox VE, Ansible, 1Password |
| Networking | OPNsense, WireGuard (Gerbil), Traefik, Caddy |
| Security | CrowdSec, Authentik SSO |
| Monitoring | Grafana, Prometheus, Loki, Beszel, Uptime Kuma |
| Media | Jellyfin, Servarr ecosystem (Radarr, Sonarr, Prowlarr, Bazarr, Lidarr) |
| AI | LiteLLM, OpenWebUI |

See [HOMELAB_SERVICES.md](HOMELAB_SERVICES.md) for the full service catalog with descriptions and links.

## Repository Structure

```
ansible/          Playbooks, roles, inventory, and test suites
guides/           Operational procedures and setup guides
memory/           Architecture decisions, patterns, and knowledge base
images/           Branding assets
```

## Deployment

All infrastructure is managed through Ansible with 1Password integration for secrets -- no plaintext credentials in the repository.

```bash
# Deploy to local Docker VMs
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml

# Deploy to gateway VPS
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml
```

Test suites validate infrastructure before deployment:

```bash
# Gateway VPS tests
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml

# Homelab VM tests
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml

# Container standardization validation
ansible-playbook -i ansible/inventory.yml ansible/tests/validation/container_standardization.yml
```

## License

MIT License
