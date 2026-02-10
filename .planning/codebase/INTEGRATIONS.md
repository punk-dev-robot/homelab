# External Integrations

**Analysis Date:** 2026-02-05

## APIs & External Services

**AI/LLM Providers:**
- OpenAI GPT-4 and GPT-4o-mini
  - SDK: LiteLLM proxy (`ansible/files/apps-vm/ai/litellm.yml`)
  - Auth: `OPENAI_API_KEY` env var
  - Usage: LiteLLM model serving, Karakeep inference
  - Configured in: `ansible/inventory.yml` lines 38, 54, 57-58

- Anthropic Claude
  - SDK: LiteLLM proxy
  - Auth: `ANTHROPIC_API_KEY` env var
  - Usage: LiteLLM model serving
  - Configured in: `ansible/inventory.yml` line 39

- Google Gemini
  - SDK: LiteLLM proxy
  - Auth: `GEMINI_API_KEY` env var
  - Usage: LiteLLM model serving
  - Configured in: `ansible/inventory.yml` line 40

- Perplexity API
  - SDK: Firecrawl integration
  - Auth: `PERPLEXITY_API_KEY` env var
  - Usage: Web search and crawling via Firecrawl
  - Configured in: `ansible/inventory.yml` line 43

- GitHub Copilot API
  - Auth: `GITHUB_API_KEY` env var
  - Usage: LiteLLM integration
  - Configured in: `ansible/inventory.yml` line 41

**Email & Communication:**
- Resend Email API
  - Service: Transactional email
  - Auth: `RESEND_API_KEY` env var
  - Usage:
    - Authentik email notifications (`ansible/files/gateway-vps/authentik/compose.yml` lines 38-42)
    - Pangolin email notifications (`ansible/files/gateway-vps/pangolin/pangolin.yml` line 8)
  - SMTP: smtp.resend.com:587 with TLS
  - From address: auth@nobasura.org
  - Configured in: `ansible/inventory.yml` lines 151, 155

**Security & DDoS Protection:**
- Cloudflare DNS API
  - Service: DNS management for Let's Encrypt ACME challenges
  - Auth: `CLOUDFLARE_API_TOKEN` env var
  - Usage: Traefik automatic certificate renewal (wildcard *.nobasura.org)
  - Configured in:
    - `ansible/files/gateway-vps/pangolin/pangolin.yml` line 56
    - `ansible/inventory.yml` line 146

**Web Scraping & Crawling:**
- Firecrawl API
  - Service: Web scraping and crawling
  - Auth: `FIRECRAWL_API_KEY` env var
  - Usage: It-Tools, Firecrawl service (`ansible/files/apps-vm/tools/firecrawl.yml`)
  - Configured in: `ansible/inventory.yml` line 46

## Data Storage

**Databases:**

**PostgreSQL 16:**
- Provider: Docker image (postgres:16-alpine, postgres:16)
- Instances:
  - Authentik: `ansible/files/gateway-vps/authentik/compose.yml` lines 4-19
    - Database: authentik
    - User: authentik (configurable)
    - Password: `AUTHENTIK_PG_PASS` env var
  - LiteLLM: `ansible/files/apps-vm/ai/litellm.yml` lines 42-62
    - Database: litellm
    - User: llmproxy
    - Password: `LITELLM_DB_PASS` env var
- Connection: TCP localhost:5432 (PostgreSQL default)
- Client: Docker Compose native connection via service name

**MongoDB (Graylog):**
- Provider: Docker image (mongo:latest)
- Instance: `ansible/files/obs-vm/graylog/mongodb.yml`
- Purpose: Backend storage for Graylog log data
- Connection: mongodb://graylog-mongodb:27017/graylog
- Auth: Environment variables (configured in compose)

**Neo4j Graph Database:**
- Provider: Docker image (neo4j:latest)
- Instance: `ansible/files/apps-vm/dbs/neo4j.yml`
- Purpose: Knowledge graph and relationship storage
- Ports:
  - HTTP: 7474
  - Bolt protocol: 7687
- Auth: `NEO4J_AUTH` env var (format: neo4j/password)
- Configured in: `ansible/inventory.yml` line 67

**File Storage:**
- NFS (TrueNAS backend):
  - Source: `truenas.lan:/mnt/hddpool/data`
  - Mount point: `/mnt/nas-data` on media-vm
  - Configuration: `ansible/deploy_docker.yml` lines 1-14
  - Mount options: NFSv4.1, soft mount, auto-mount, 10s timeout
  - Usage: Shared media library for Jellyfin, Jellyseerr, Sonarr, Radarr
  - Variable reference: `ansible/inventory.yml` line 6

- Docker volumes:
  - Authentik media: `authentik_db`, `authentik/media`
  - LiteLLM: `postgres_data`, `prometheus_data`
  - Neo4j: `neo4j-data`
  - Graylog: `graylog-data`, `graylog-mongodb`, `graylog-datanode`

**Caching:**
- None detected in current configuration
- Potential: Redis could be added for session caching

## Authentication & Identity

**Auth Provider:**
- Authentik 2025.10.1 (Self-hosted OpenID Connect provider)
  - Deployment: `ansible/files/gateway-vps/authentik/compose.yml`
  - Database: PostgreSQL 16-alpine
  - Base domain: auth.nobasura.org
  - OIDC endpoint: https://auth.nobasura.org/application/o/{app}/.well-known/openid-configuration

**OAuth 2.0 / OIDC Applications:**
- Karakeep (Karaoke app)
  - OIDC client: `KARAKEEP_OAUTH_CLIENT` from 1Password
  - Well-known: https://auth.nobasura.org/application/o/karakeep/.well-known/openid-configuration
  - Scope: openid email profile
  - Configuration: `ansible/inventory.yml` lines 60-65

- Jellyseerr (Media requests)
  - Image: fallenbagel/jellyseerr:preview-OIDC (OIDC-enabled fork)
  - Configuration: `ansible/files/media-vm/jelly/jellyseerr.yml`
  - Requires: Authentik OIDC provider setup

- Jellyfin (Media server)
  - SSO integration planned via Authentik
  - Status: OIDC integration in progress
  - Reference: `/home/kuba/dev/lab/AUTHENTIK_IMPLEMENTATION_STATE.md`

**Credential Storage:**
- 1Password (via Ansible lookup plugin)
  - Vault: "Homelab"
  - Integration: `community.general.onepassword` Ansible lookup
  - Usage: All secrets retrieved at deploy time
  - Examples:
    - Database passwords
    - API keys (OpenAI, Anthropic, Gemini, etc.)
    - OAuth client credentials
    - CrowdSec enrollment keys
  - Configured in: `ansible/inventory.yml` (extensive usage throughout)

## Monitoring & Observability

**Metrics Collection:**
- Prometheus (Time-series metrics database)
  - Apps-VM: `ansible/files/apps-vm/ai/prometheus.yml`
  - OBS-VM: `ansible/files/obs-vm/grafana/prometheus.yml`
  - Retention: 15 days (LiteLLM configured explicitly)
  - Ports: 9090 (both instances)
  - Scrape targets:
    - LiteLLM: localhost:4000
    - Graylog: 9833 (Prometheus exporter)
    - CrowdSec: 8080 (LAPI with metrics)

**Log Aggregation:**
- Graylog Enterprise 6.1
  - Deployment: `ansible/files/obs-vm/graylog/compose.yml`
  - Backend: MongoDB + Graylog DataNode
  - Port: 9000 (HTTP)
  - Prometheus metrics: 9833
  - SIEM-like capabilities for log analysis

- Loki (Log aggregation with Grafana)
  - Deployment: `ansible/files/obs-vm/grafana/loki.yml`
  - Purpose: Log storage and querying
  - Integration: Grafana data source

**Visualization:**
- Grafana
  - Deployment: `ansible/files/obs-vm/grafana/compose.yml`
  - Data sources: Prometheus, Loki
  - Dashboards: Monitoring homelab services
  - Configuration: `ansible/files/obs-vm/grafana/`

**Container Logging:**
- Dozzle (Container log viewer)
  - Deployed on: apps-vm, media-vm, gateway-vps
  - Purpose: Real-time Docker container logs
  - Access: https://dozzle.lab.nobasura.org (homelab) or dozzle.nobasura.org (gateway)

**Error Tracking:**
- None detected in current configuration
- Potential integration point for error reporting

**System Monitoring:**
- Beszel Agent
  - Deployed: `ansible/files/gateway-vps/pangolin/beszel-agent.yml`
  - Purpose: System-level resource monitoring
  - Integration: Sends metrics to central Beszel server

- Uptime Kuma
  - Deployment: `ansible/files/obs-vm/obs-apps/uptime-kuma.yml`
  - Purpose: Service uptime and health monitoring
  - Features: Status page, alerts

## CI/CD & Deployment

**Hosting:**
- Homelab:
  - Proxmox cluster (3 nodes: px-cpu, px-net, px-nas)
  - VMs deployed via KVM
  - Ansible deployment targets: apps.lan, media.lan, obs.lan
  - Configuration: `ansible/inventory.yml` (proxmox group lines 164-223)

- External Gateway:
  - VPS provider (IP: 141.147.93.212, Ubuntu 20.04+)
  - SSH access: ubuntu user with SSH key
  - Ansible target: gateway-vps (SSH-based)
  - Configuration: `ansible/inventory.yml` lines 111-155

**Deployment Pipeline:**
- Ansible playbooks (manual execution):
  - `ansible/deploy_docker.yml` - Deploy homelab VMs
  - `ansible/deploy_vps.yml` - Deploy gateway VPS
  - `ansible/deploy_crowdsec_firewall_bouncer.yml` - Deploy firewall protection
- Pre-deployment: Ansible validation via tests
  - `ansible/tests/suites/gateway_vps_test_suite.yml`
  - `ansible/tests/suites/homelab_vms_test_suite.yml`
  - `ansible/tests/validation/container_standardization.yml`

**Container Updates:**
- Watchtower (Automated image updates)
  - Deployed on: apps-vm, media-vm, obs-vm, gateway-vps
  - Purpose: Keep container images up-to-date

**Container Orchestration:**
- Docker Compose (local stacks per VM)
  - No Kubernetes
  - Each VM runs independent compose stacks
  - Networking: Docker bridge networks (local) + Traefik reverse proxy (external)

## Environment Configuration

**Required Environment Variables:**

**Common (all VMs):**
- PUID: Docker user ID (1000 for homelab, 1001 for VPS)
- PGID: Docker group ID (1000 for homelab, 999 for VPS)
- TZ: Europe/London
- UMASK: 022
- LOG_LEVEL: info
- APP_DATA: /opt/docker/appdata

**Gateway VPS - Pangolin:**
- DOMAIN: pangolin.nobasura.org
- LETSENCRYPT_EMAIL: letsencrypt.a0f@nobasura.org
- CLOUDFLARE_API_TOKEN: For DNS validation
- PANGOLIN_ROOT_API_KEY: Root API authentication
- CROWDSEC_BOUNCER_API_KEY: Traefik bouncer registration
- CROWDSEC_ENROLLMENT_KEY: CrowdSec cloud enrollment
- TRAEFIK_AUTH_BYPASS_KEY: Authentication bypass configuration
- RESEND_API_KEY: Email notifications

**Gateway VPS - Authentik:**
- AUTHENTIK_PG_PASS: PostgreSQL password
- AUTHENTIK_SECRET_KEY: Secret key for encryption
- AUTHENTIK_VERSION: 2025.10.1 (or later)
- RESEND_API_KEY: Email notifications

**Homelab - Apps-VM (AI/Tools):**
- LITELLM_DB_USER: llmproxy
- LITELLM_DB_PASS: Database password
- LITELLM_MASTER_KEY: LiteLLM authentication
- LITELLM_SALT_KEY: Password hashing salt
- OPENAI_API_KEY: OpenAI authentication
- ANTHROPIC_API_KEY: Claude API authentication
- GEMINI_API_KEY: Google Gemini authentication
- GITHUB_API_KEY: GitHub Copilot API
- PERPLEXITY_API_KEY: Perplexity search API
- FIRECRAWL_API_KEY: Web scraping service
- KARAKEEP_OAUTH_CLIENT: Authentik OAuth credentials
- KARAKEEP_OPENAI_API_KEY: Karaoke AI features
- NEXTAUTH_SECRET: NextAuth session encryption
- NEXTAUTH_URL: https://karakeep.nobasura.org
- MEILI_MASTER_KEY: Meilisearch authentication
- ATUIN_DB_PASS: Shell history database

**Homelab - Media-VM:**
- DATA_DIR: /mnt/nas-data (NFS mount)
- JELLYSTAT_DB_PASS: Statistics database password
- JELLYSTAT_JWT_SECRET: JWT token signing
- WIREGUARD_PRIVATE_KEY: VPN tunnel for Deluge
- NewT configuration: NEWT_ID, NEWT_SECRET, PANGOLIN_ENDPOINT

**Homelab - OBS-VM (Monitoring):**
- PBS_API_TOKEN: Proxmox Backup Server
- PIHOLE_API_TOKEN: Pi-hole DNS filtering
- GRAYLOG_PASSWORD_SECRET: Graylog master password
- GRAYLOG_ROOT_PASSWORD_SHA2: Graylog root user (SHA2)

**Secrets Location:**
- 1Password vault: "Homelab"
- Ansible lookup: `community.general.onepassword` plugin
- No .env files committed (credentials via 1Password only)
- Deploy-time injection: Secrets populated during playbook execution

## Webhooks & Callbacks

**Incoming Webhooks:**
- Notifiarr (Media management notifications)
  - Integrated with: Radarr, Sonarr, Lidarr, Whisparr
  - Purpose: Unified notification system for media library changes
  - Deployment: `ansible/files/media-vm/servarr/notifiarr.yml`

- Gotify (Notification center)
  - Deployment: `ansible/files/obs-vm/obs-apps/gotify.yml`
  - Purpose: Push notifications for infrastructure events
  - Integration: Docker events, webhook targets
  - Token: `WT_GOTIFY_TOKEN` from 1Password
  - Configured in: `ansible/inventory.yml` line 16

**Outgoing Webhooks:**
- Traefik (Middleware manager integration)
  - Configuration: `ansible/files/gateway-vps/pangolin/middleware-manager.yml`
  - Purpose: Dynamic middleware and router configuration
  - Endpoint: Pangolin HTTP API

- CrowdSec (Traefik bouncer integration)
  - API calls to CrowdSec LAPI (port 8080)
  - Registration: `ansible/deploy_vps.yml` lines 94-113
  - Purpose: Real-time threat detection and blocking

**Service-to-Service Integration:**
- LiteLLM → OpenAI, Anthropic, Gemini (HTTP API calls)
- Karakeep → LiteLLM (Model serving)
- Jellyseerr → Jellyfin (Media server integration)
- Radarr/Sonarr → Prowlarr (Indexer management)
- Radarr/Sonarr → Deluge/NZBGet (Download clients)
- Recyclarr → Radarr/Sonarr (Configuration sync)
- Traefik → Authentik (Forward auth middleware)
- CrowdSec → Firewall rules (Bouncer integration)

## Network Isolation

**Docker Networks:**
- `socket_proxy`: Isolated socket access for services requiring Docker API
  - Used by: Watchtower, Portainer Agent, Docker-gc
  - Purpose: Reduce privileged container count

- `pangolin`: Gateway VPS network for Traefik and Pangolin
  - Services: Traefik, Pangolin, Gerbil, CrowdSec

- `authentik`: Authentik service network
  - Services: Authentik server, worker, PostgreSQL

- `obs-shared`: OBS-VM shared network for monitoring services
  - Services: Grafana, Prometheus, Loki

**Cross-Network Communication:**
- Traefik connects to both `pangolin` and service networks
- Services reach external APIs via container NAT
- Homelab → Gateway: Newt VPN tunnel (defined-networking)
  - Configured: `ansible/files/common/newt/compose.yml`
  - Per-VM configuration: `ansible/inventory.yml` (newt vars)

---

*Integration audit: 2026-02-05*
