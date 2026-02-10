---
title: Service Distribution
type: note
permalink: network-info/architecture/service-distribution
---

# Service Distribution

## Current Service Allocation

The homelab services are distributed across three VMs based on function and resource requirements. Each VM runs multiple Docker stacks managed through Ansible.

## Service Distribution by VM

### apps-vm (10.100.10.x)
**Purpose**: AI services, databases, and productivity tools  
**Resources**: Optimized for CPU and memory-intensive workloads

```mermaid
graph TB
    subgraph "apps-vm Stacks"
        subgraph "AI Stack"
            LiteLLM[LiteLLM<br/>AI Model Proxy<br/>:4000]
            OpenWebUI[Open WebUI<br/>Chat Interface<br/>:3000]
            OpenHands[OpenHands<br/>AI Dev Assistant<br/>:3001]
        end
        
        subgraph "Database Stack"
            Neo4j[Neo4j<br/>Graph Database<br/>:7474/7687]
            PostgresAI[PostgreSQL<br/>AI Services DB<br/>:5432]
        end
        
        subgraph "Tools Stack"
            Atuin[Atuin<br/>Shell History Sync<br/>:8888]
            Firecrawl[Firecrawl<br/>Web Scraping API<br/>:3002]
            Karakeep[Karakeep<br/>Knowledge Base<br/>:3000]
            ITTools[IT-Tools<br/>Dev Utilities<br/>:8080]
            Enclosed[Enclosed<br/>File Sharing<br/>:8787]
        end
        
        subgraph "OAM Stack"
            WatchtowerA[Watchtower<br/>Auto Updates]
            DeunhealthA[Deunhealth<br/>Health Monitor]
            DockerGCA[Docker-GC<br/>Cleanup]
            DozzleAgentA[Dozzle Agent<br/>Log Forward]
            PortainerAgentA[Portainer Agent]
        end
    end
```

### media-vm (10.100.20.x)
**Purpose**: Media management and streaming services  
**Resources**: Optimized for storage I/O and transcoding

```mermaid
graph TB
    subgraph "media-vm Stacks"
        subgraph "Media Frontend"
            Jellyfin[Jellyfin<br/>Media Server<br/>:8096]
            Jellyseerr[Jellyseerr<br/>Request Mgmt<br/>:5055]
            Jellystat[Jellystat<br/>Statistics<br/>:3004]
            Stash[Stash<br/>Organizer<br/>:9999]
        end
        
        subgraph "Servarr Stack"
            Radarr[Radarr<br/>Movies<br/>:7878]
            Sonarr[Sonarr<br/>TV Shows<br/>:8989]
            Lidarr[Lidarr<br/>Music<br/>:8686]
            Readarr[Readarr<br/>Books<br/>:8787]
            Whisparr[Whisparr<br/>Adult<br/>:6969]
            Prowlarr[Prowlarr<br/>Indexers<br/>:9696]
            Bazarr[Bazarr<br/>Subtitles<br/>:6767]
        end
        
        subgraph "Download Stack"
            Deluge[Deluge<br/>Torrents<br/>:8112]
            SABnzbd[SABnzbd<br/>Usenet<br/>:8080]
            NZBGet[NZBGet<br/>Usenet Alt<br/>:6789]
            Gluetun[Gluetun<br/>VPN Gateway]
            FlareSolverr[FlareSolverr<br/>Captcha<br/>:8191]
        end
    end
```

### obs-vm (10.100.30.x)
**Purpose**: Monitoring, logging, and observability  
**Resources**: Optimized for data ingestion and querying

```mermaid
graph TB
    subgraph "obs-vm Stacks"
        subgraph "Monitoring Stack"
            Grafana[Grafana<br/>Dashboards<br/>:3000]
            Prometheus[Prometheus<br/>Metrics<br/>:9090]
            Loki[Loki<br/>Log Store<br/>:3100]
            Promtail[Promtail<br/>Log Shipper]
        end
        
        subgraph "Management Stack"
            Portainer[Portainer<br/>Container UI<br/>:9000]
            Dozzle[Dozzle<br/>Log Viewer<br/>:8080]
            UptimeKuma[Uptime Kuma<br/>Monitoring<br/>:3001]
            Beszel[Beszel<br/>System Stats<br/>:8090]
            Gotify[Gotify<br/>Notifications<br/>:80]
        end
        
        subgraph "Logging Stack"
            Graylog[Graylog<br/>Log Analysis<br/>:9000]
            MongoDB[MongoDB<br/>Graylog DB<br/>:27017]
            OpenSearch[OpenSearch<br/>Log Index]
        end
        
        subgraph "TICK Stack"
            InfluxDB[InfluxDB 2<br/>Time Series<br/>:8086]
        end
    end
```

## Common Services (All VMs)

Each VM runs a standard OAM (Operations, Administration, Maintenance) stack:

| Service | Purpose | Notes |
|---------|---------|-------|
| Watchtower | Automatic container updates | Scheduled updates |
| Deunhealth | Health status aggregation | Reports to Uptime Kuma |
| Docker-GC | Container/image cleanup | Prevents disk fill |
| Socket-Proxy | Secure Docker API access | For management tools |
| Dozzle Agent | Centralized log viewing | Forwards to obs-vm |
| Portainer Agent | Remote container management | Managed from obs-vm |

## Service Dependencies

```mermaid
graph LR
    subgraph "External Dependencies"
        Gateway[Gateway VPS<br/>Pangolin + Traefik]
        Storage[TrueNAS<br/>Media Storage]
        Secrets[1Password<br/>Credentials]
    end
    
    subgraph "Service Dependencies"
        Apps[apps-vm]
        Media[media-vm]
        Obs[obs-vm]
    end
    
    Gateway -->|Auth/Proxy| Apps
    Gateway -->|Auth/Proxy| Media
    Gateway -->|Auth/Proxy| Obs
    
    Storage -->|NFS/SMB| Media
    Storage -->|Backups| Apps
    Storage -->|Metrics| Obs
    
    Secrets -->|API| Apps
    Secrets -->|API| Media
    Secrets -->|API| Obs
    
    Apps -->|Metrics| Obs
    Media -->|Metrics| Obs
    Media -->|AI Processing| Apps
```

## Resource Allocation Guidelines

### CPU Allocation
- **apps-vm**: High CPU for AI workloads
- **media-vm**: Moderate CPU for transcoding
- **obs-vm**: Moderate CPU for data processing

### Memory Allocation
- **apps-vm**: High memory for databases and AI models
- **media-vm**: Moderate memory for caching
- **obs-vm**: High memory for log retention

### Storage Allocation
- **apps-vm**: SSD for databases, moderate capacity
- **media-vm**: Large capacity, NFS mounts
- **obs-vm**: SSD for metrics, high IOPS

## Network Traffic Patterns

### Internal Traffic
```yaml
High Bandwidth:
  - media-vm ←→ TrueNAS (media files)
  - obs-vm ← all VMs (metrics/logs)
  
Moderate Bandwidth:
  - apps-vm ←→ Gateway (API traffic)
  - media-vm → apps-vm (AI processing)
  
Low Bandwidth:
  - Management traffic (SSH, Portainer)
  - Health checks and monitoring
```

### External Traffic
```yaml
Inbound (via Gateway VPS):
  - HTTPS to all services
  - API calls to AI services
  
Outbound:
  - Package updates
  - Docker image pulls
  - Media metadata fetching
  - AI model API calls
```

## Service Discovery and Routing

### Internal DNS (.lan)
- apps.lan → 10.100.10.x
- media.lan → 10.100.20.x
- obs.lan → 10.100.30.x

### Reverse Proxy (.lab.nobasura.org)
- Internal access via Caddy
- Service-specific subdomains
- SSL termination

### External Access (.nobasura.org)
- Via Gateway VPS
- Pangolin SSO authentication
- Traefik reverse proxy

## Future Service Distribution (with px-cpu)

### Proposed Redistribution
```yaml
px-cpu (Primary Compute):
  - All AI services (from apps-vm)
  - All databases (from apps-vm)
  - All tools (from apps-vm)
  - Critical monitoring (Prometheus, Grafana)
  - High availability services

apps-vm (Deprecated/Repurposed):
  - Development/testing environment
  - Non-critical experiments

px-nas (Storage Focus):
  - All media services (keep as-is)
  - TrueNAS VM
  - Backup services

obs-vm (Monitoring Focus):
  - Logging and analysis (keep as-is)
  - Non-critical monitoring
  - Historical data storage
```

### Benefits of Redistribution
1. **Performance**: AI/DB on most powerful hardware
2. **Reliability**: Critical services on HA-capable host
3. **Efficiency**: Better resource utilization
4. **Flexibility**: Easier maintenance and updates
5. **Scalability**: Room for growth on px-cpu