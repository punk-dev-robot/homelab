---
title: Service Distribution Architecture
type: note
permalink: architecture/service-distribution-architecture
---

# Service Distribution Architecture

## Overview
The homelab services are distributed across three specialized VMs, each optimized for specific workloads. All services run as Docker containers managed through Ansible, with consistent OAM (Operations, Administration, and Maintenance) stacks across all VMs.

## VM Service Distribution

### apps-vm (10.10.10.11)
**Purpose**: AI services, databases, and productivity tools
**Node**: px-nas (primary)
**Resources**: CPU and memory-intensive workloads
**Access**: apps.lan / apps.lab.nobasura.org

#### AI Stack
- **LiteLLM** (port 4000): AI model proxy and load balancer
- **Open WebUI** (port 3000): Chat interface for LLMs
- **OpenHands** (port 3001): AI development assistant

#### Database Stack
- **Neo4j** (ports 7474/7687): Graph database for relationships
- **PostgreSQL**: AI services database (port 5432)

#### Tools Stack
- **Atuin** (port 8888): Shell history sync across machines
- **Firecrawl** (port 3002): Web scraping API service
- **Karakeep** (port 3000): Knowledge base management
- **IT-Tools** (port 8080): Developer utilities collection
- **Enclosed** (port 8787): Secure file sharing

#### OAM Stack
- **Watchtower**: Automatic container updates
- **Deunhealth**: Health monitoring
- **Docker-GC**: Container cleanup
- **Dozzle Agent**: Log forwarding
- **Portainer Agent**: Container management

### media-vm (10.10.10.12)
**Purpose**: Media management and streaming services
**Node**: px-nas (primary)
**Resources**: Storage I/O and transcoding optimized
**Access**: media.lan / media.lab.nobasura.org

#### Media Frontend Stack
- **Jellyfin** (port 8096): Primary media server
- **Jellyseerr** (port 5055): Media request management
- **Jellystat** (port 3004): Viewing statistics
- **Stash** (port 9999): Media organizer

#### Servarr Stack
- **Radarr** (port 7878): Movie management
- **Sonarr** (port 8989): TV show management
- **Lidarr** (port 8686): Music management
- **Readarr** (port 8787): Book management
- **Whisparr** (port 6969): Adult content management
- **Prowlarr** (port 9696): Indexer management
- **Bazarr** (port 6767): Subtitle management

#### Download Stack
- **Deluge** (port 8112): Torrent client
- **SABnzbd** (port 8080): Primary Usenet client
- **NZBGet** (port 6789): Alternative Usenet client
- **Gluetun**: VPN gateway for downloads
- **FlareSolverr** (port 8191): Cloudflare captcha solver

#### OAM Stack
- Same as apps-vm for consistency

### obs-vm (10.10.10.13)
**Purpose**: Monitoring, logging, and observability
**Node**: px-nas (primary)
**Resources**: Data ingestion and querying optimized
**Access**: obs.lan / obs.lab.nobasura.org

#### Monitoring Stack
- **Grafana** (port 3000): Visualization dashboards
- **Prometheus** (port 9090): Metrics collection
- **Loki** (port 3100): Log aggregation
- **Promtail**: Log shipping agent
- **AlertManager** (port 9093): Alert routing

#### Management Stack
- **Portainer** (port 9000): Container management UI
- **Dozzle** (port 8080): Real-time log viewer
- **Homepage** (port 3000): Service dashboard
- **Scrutiny** (port 8080): Disk health monitoring

#### Health Stack
- **Uptime Kuma** (port 3001): Service uptime monitoring
- **Healthchecks** (port 8000): Cron job monitoring
- **Statping** (port 8080): Status page

#### OAM Stack
- Same as other VMs but acts as central collector

## Service Access Patterns

### Internal Access Routes
```
User Device (VLAN 40)
    ↓
OPNsense Router
    ↓
Service VLAN (10)
    ↓
Caddy Reverse Proxy (per VM)
    ↓
Docker Container
```

### External Access Routes
```
Internet
    ↓
Gateway VPS (Public IP)
    ↓
Traefik + Pangolin SSO
    ↓
WireGuard Tunnel
    ↓
Internal Service
```

## Port Allocation Strategy

### Reserved Port Ranges
- **3000-3999**: Web UIs and dashboards
- **4000-4999**: API services
- **5000-5999**: Media services
- **6000-6999**: Support services
- **7000-7999**: Servarr services
- **8000-8999**: Management tools
- **9000-9999**: System services

### Standard Ports
- **80/443**: Reserved for reverse proxies
- **22**: SSH (management only)
- **53**: DNS (OPNsense)
- **Database Ports**: PostgreSQL (5432), Neo4j (7474/7687)

## Resource Allocation

### CPU Allocation
- **apps-vm**: 8 vCPUs (AI workloads)
- **media-vm**: 6 vCPUs (transcoding)
- **obs-vm**: 4 vCPUs (data processing)

### Memory Allocation
- **apps-vm**: 32GB RAM (LLM requirements)
- **media-vm**: 16GB RAM (caching)
- **obs-vm**: 16GB RAM (query performance)

### Storage Allocation
- **apps-vm**: 500GB SSD (databases)
- **media-vm**: 8TB HDD (media files)
- **obs-vm**: 1TB SSD (metrics/logs)

## High Availability Considerations

### Service Redundancy
- Critical services have backup instances
- Watchtower ensures automatic updates
- Health checks trigger automatic restarts

### Data Persistence
- All data stored on redundant storage
- Regular snapshots at VM level
- Application-level backups for databases

### Network Redundancy
- Dual OPNsense with CARP failover
- Multiple DNS resolvers
- Redundant reverse proxy paths

## Scaling Strategy

### Horizontal Scaling
- Add more containers for stateless services
- Use Docker Swarm for orchestration (future)
- Load balance across multiple instances

### Vertical Scaling
- Increase VM resources as needed
- Migrate VMs to more powerful hosts
- Optimize container resource limits

### Service Migration Plan
When px-cpu is added:
1. **Phase 1**: Migrate obs-vm (least critical)
2. **Phase 2**: Migrate media-vm (moderate impact)
3. **Phase 3**: Keep apps-vm on px-nas (storage proximity)

## Monitoring and Alerting

### Metrics Collection
- **Node Exporter**: Host metrics from Proxmox
- **cAdvisor**: Container metrics
- **Custom exporters**: Application-specific metrics

### Log Aggregation
- **Promtail**: Collects logs from all containers
- **Loki**: Centralized log storage
- **Grafana**: Log visualization and alerting

### Health Monitoring
- **Uptime Kuma**: Service availability
- **Healthchecks**: Cron job monitoring
- **Deunhealth**: Container health status

### Alert Routing
- Critical alerts: Immediate notification
- Warning alerts: Aggregated hourly
- Info alerts: Daily summary

## Backup Strategy

### VM Level
- Weekly snapshots of all VMs
- Stored on separate storage pool
- 4 weeks retention

### Application Level
- Database dumps: Daily
- Configuration exports: On change
- Media metadata: Weekly

### Offsite Backup
- Critical data to cloud storage
- Encrypted before upload
- 3-2-1 backup rule applied

## Security Considerations

### Network Segmentation
- Services isolated in LAB VLAN
- No direct internet exposure
- Firewall rules restrict inter-service communication

### Access Control
- SSO through Authentik (planned)
- Service-specific authentication
- API keys for automation

### Container Security
- Regular image updates via Watchtower
- Non-root containers where possible
- Resource limits enforced

## Related Documentation
- [[Network Architecture Complete Overview]]
- [[Container Standardization Patterns]]
- [[High Availability Configuration]]
- [[Monitoring and Observability Setup]]

Tags: #services #docker #architecture #distribution #homelab #containers