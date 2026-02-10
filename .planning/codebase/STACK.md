# Technology Stack

**Analysis Date:** 2026-02-05

## Languages

**Primary:**
- YAML - Ansible playbooks, Docker Compose files, and configuration
- Bash - Shell scripts for deployment and configuration management

**Secondary:**
- Jinja2 - Template language for dynamic Ansible configuration
- Python - Ansible execution environment

## Runtime

**Environment:**
- Linux (Debian/Ubuntu-based VMs and gateway VPS)
- Docker Engine - Container runtime for all services
- Ansible - Infrastructure automation framework

**Package Manager:**
- Docker Compose - Container orchestration
- Ansible - Configuration management
- pip/uv - Python package management (used for Ansible plugins)

## Frameworks

**Core Infrastructure:**
- Ansible - Complete infrastructure-as-code automation
  - Versions: community.general plugins, Ansible 2.9+
  - Location: `ansible/` directory
  - Used for: VM provisioning, Docker deployment, configuration management

**Reverse Proxy & Gateway:**
- Traefik v3.6.0 - Dynamic reverse proxy and load balancer
  - Location: `ansible/files/gateway-vps/pangolin/pangolin.yml`
  - Uses Gerbil for VPN tunnel management
  - Dynamic configuration: `ansible/files/gateway-vps/pangolin/traefik_rules/`

**Security & Threat Detection:**
- CrowdSec - Collaborative security detection and response
  - Version: latest-debian
  - Location: `ansible/files/gateway-vps/pangolin/pangolin.yml`
  - Collections: crowdsecurity/linux, crowdsecurity/sshd, crowdsecurity/traefik, crowdsecurity/http-cve
  - Bouncers: Traefik bouncer, Firewall bouncer

**Authentication & SSO:**
- Authentik 2025.10.1 - Identity provider and SSO solution
  - Location: `ansible/files/gateway-vps/authentik/compose.yml`
  - Backend: PostgreSQL 16
  - Email: Resend SMTP integration

**VPN & Tunnel Management:**
- Pangolin 1.12.2 - VPN configuration and management
  - Gerbil 1.2.2 - WireGuard integration with Pangolin
  - Location: `ansible/files/gateway-vps/pangolin/`

## Key Dependencies

**Critical:**
- Docker - Container runtime (all VMs)
- PostgreSQL 16 - Database for Authentik and LiteLLM
  - Authentik: `ansible/files/gateway-vps/authentik/compose.yml`
  - LiteLLM: `ansible/files/apps-vm/ai/litellm.yml`
- Neo4j:latest - Graph database for knowledge management
  - Location: `ansible/files/apps-vm/dbs/neo4j.yml`
  - Auth via environment variables

**AI/ML Stack:**
- LiteLLM - LLM proxy and unified API
  - Version: ghcr.io/berriai/litellm:main-stable
  - Location: `ansible/files/apps-vm/ai/litellm.yml`
  - Database: PostgreSQL 16
  - Prometheus metrics: Port 9090
  - Dependencies: OpenAI, Anthropic, Gemini APIs (external)

**Media Services:**
- Jellyfin:latest - Media server with hardware transcoding
  - Location: `ansible/files/media-vm/jelly/jellyfin.yml`
  - Hardware: Intel GPU via /dev/dri
  - SSO: Authentik integration (OIDC)
- Jellyseerr:preview-OIDC - Media request management with OIDC
  - Location: `ansible/files/media-vm/jelly/jellyseerr.yml`
- Jellstat - Jellyfin statistics
  - Location: `ansible/files/media-vm/jelly/jellystat.yml`

**Monitoring & Logging:**
- Grafana - Visualization and dashboards
  - Location: `ansible/files/obs-vm/grafana/compose.yml`
  - Data sources: Prometheus, Loki
- Prometheus - Metrics collection
  - LiteLLM: `ansible/files/apps-vm/ai/prometheus.yml`
  - OBS VM: `ansible/files/obs-vm/grafana/prometheus.yml`
  - Retention: 15 days for LiteLLM
- Loki - Log aggregation
  - Location: `ansible/files/obs-vm/grafana/loki.yml`
- Graylog 6.1 (Enterprise) - Log analysis and management
  - Location: `ansible/files/obs-vm/graylog/compose.yml`
  - Backend: MongoDB, Graylog DataNode
  - Prometheus exporter: Port 9833

**Infrastructure Observability:**
- Dozzle - Docker container logs viewer
  - Deployed on: apps-vm, media-vm, gateway-vps
- Portainer - Docker management UI
  - Location: `ansible/files/obs-vm/obs-apps/portainer.yml`
- Beszel Agent - System monitoring agent
  - Location: `ansible/files/gateway-vps/pangolin/beszel-agent.yml`
- Uptime Kuma - Uptime monitoring
  - Location: `ansible/files/obs-vm/obs-apps/uptime-kuma.yml`

**Media Management (Servarr Stack):**
- Radarr - Movie collection management
- Sonarr - TV series management
- Lidarr - Music library management
- Whisparr - Adult content management
- Prowlarr - Indexer management
- Bazarr - Subtitle management
- Recyclarr - Configuration synchronization
  - Location: `ansible/files/media-vm/servarr/`
- Deluge - Torrent client (via Gluetun VPN)
- NZBGet, SABnzbd - Usenet download clients
- Notifiarr - Notification and media management
  - Location: `ansible/files/media-vm/servarr/notifiarr.yml`

**Tools & Utilities:**
- Karakeep - Karaoke management with OIDC
  - Location: `ansible/files/apps-vm/tools/karakeep.yml`
  - LiteLLM integration for AI features
  - Meilisearch for full-text search
- Firecrawl - Web scraping service
  - Location: `ansible/files/apps-vm/tools/firecrawl.yml`
- Atuin - Shell history management
  - Location: `ansible/files/apps-vm/tools/atuin.yml`
  - Database: PostgreSQL
- IT-Tools - Various IT utilities
  - Location: `ansible/files/apps-vm/tools/it-tools.yml`
- Enclosed - Secure file sharing
  - Location: `ansible/files/apps-vm/tools/enclosed.yml`

**Operations & Maintenance:**
- Watchtower - Automated container updates
  - Deployed on: apps-vm, media-vm, obs-vm
- Docker-gc - Docker garbage collection
  - Deployed on: apps-vm, media-vm, obs-vm
- Deunhealth - Container health management
  - Location: `ansible/files/*/oam/deunhealth.yml`
  - Auto-restart unhealthy containers
- Homepage - Service dashboard and index
  - Location: `ansible/files/apps-vm/lab/homepage.yml`
  - Config: `ansible/files/apps-vm/lab/homepage-config/`

**VPN & Networking:**
- Gluetun - VPN client container
  - Location: `ansible/files/media-vm/servarr/gluetun.yml`
  - Used by: Deluge, other services requiring VPN
- Newt (Defined Networking) - VPN tunnel client
  - Common: `ansible/files/common/newt/compose.yml`
  - Deployed to: apps-vm, media-vm, obs-vm
  - Connects to Pangolin gateway

**Container Standards:**
- Base service template: `ansible/files/common.yml`
  - All containers extend `base` or `socket-base`
  - Standard env: PUID, PGID, TZ, UMASK, LOG_LEVEL
  - Socket proxy for Docker access via DOCKER_HOST=tcp://socket-proxy:2375

## Configuration

**Environment:**
- 1Password integration via Ansible lookup
  - Critical credentials stored in: Homelab vault
  - Variables resolved at deploy time
  - Location: `ansible/inventory.yml` (lines 16-156)

**Build & Deployment:**
- Ansible playbooks:
  - `ansible/deploy_docker.yml` - Deploy local VMs (apps-vm, media-vm, obs-vm)
  - `ansible/deploy_vps.yml` - Deploy gateway VPS (Pangolin, Authentik, CrowdSec)
  - `ansible/deploy_crowdsec_firewall_bouncer.yml` - CrowdSec firewall protection
- Docker Compose:
  - Location: `ansible/files/*/` (VM-specific stacks)
  - Each VM has stacks directory: `apps-vm`, `media-vm`, `obs-vm`
  - Gateway stacks: `gateway-vps/pangolin/`, `gateway-vps/authentik/`

**Configuration Files:**
- Traefik: `ansible/files/gateway-vps/pangolin/traefik_static_config/traefik_config.yml`
- Traefik dynamic rules: `ansible/files/gateway-vps/pangolin/traefik_rules/`
  - `dynamic_config.yml` - Service routing
  - `bypass-routers.yml` - Auth bypass rules (generated at deploy)
  - `resource-overrides.yml` - Resource limits
- CrowdSec: `ansible/files/gateway-vps/crowdsec/config/crowdsec/`
  - `acquis.d/acquis-authentik.yaml` - Log sources
  - Custom profiles and scenarios for firewall protection
- Pangolin: `ansible/files/gateway-vps/pangolin/config/config.yml.j2`
- Homepage config: `ansible/files/apps-vm/lab/homepage-config/`

## Platform Requirements

**Development/Deployment:**
- Ansible 2.9+
- Python 3.8+ (for Ansible)
- community.general plugin collection
- SSH access to VMs and gateway
- 1Password CLI for credential lookup
- Docker CLI for container management

**Production - Homelab VMs:**
- KVM/Proxmox hypervisor
- Debian/Ubuntu Linux (apps-vm, media-vm, obs-vm)
- Docker Engine
- NFS mount to TrueNAS for shared media
  - Mount point: `ansible/files/media-vm/jelly/` uses `/mnt/nas-data`
  - Source: `truenas.lan:/mnt/hddpool/data`

**Production - Gateway VPS:**
- Linux VPS (Ubuntu 20.04+)
- Docker Engine
- Public IP and domain (nobasura.org)
- Cloudflare DNS API access for Let's Encrypt
- Hardware requirements: Minimal (Pangolin/Traefik/CrowdSec are lightweight)

**Network Requirements:**
- Local network connectivity (.lan domains via DNS)
- External internet connectivity for VPS
- DNS: OPNsense Unbound for .lab.nobasura.org resolution
- SSH: Port 22 on all hosts
- Docker Compose networks: socket_proxy, pangolin, authentik, obs-shared

## Infrastructure Architecture

**Homelab (Internal):**
- **apps-vm** (.lab.nobasura.org):
  - Stacks: oam, ai, tools, dbs
  - Services: LiteLLM, OpenWebUI, Karakeep, Neo4j, Homepage, Atuin, Firecrawl
  - Direct .lan access: apps.lan

- **media-vm** (.lab.nobasura.org):
  - Stacks: oam, servarr, jelly
  - Services: Jellyfin, Jellyseerr, Radarr, Sonarr, Deluge, NZBGet
  - Direct .lan access: media.lan
  - NFS mount from TrueNAS for media library

- **obs-vm** (.lab.nobasura.org):
  - Stacks: oam, obs-apps, grafana, graylog, tick
  - Services: Grafana, Prometheus, Loki, Graylog, Portainer, Uptime Kuma
  - Direct .lan access: obs.lan

**Gateway (External):**
- **gateway-vps** (Public IP, .nobasura.org):
  - Stacks: pangolin, authentik
  - Services: Traefik, Pangolin, Gerbil, CrowdSec, Authentik
  - Public DNS: *.nobasura.org routes through Traefik
  - Newt tunnel connects homelab VMs to external gateway

---

*Stack analysis: 2026-02-05*
