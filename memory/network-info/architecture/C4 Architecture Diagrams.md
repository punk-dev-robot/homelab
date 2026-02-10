---
title: C4 Architecture Diagrams
type: note
permalink: network-info/architecture/c4-architecture-diagrams
---

# C4 Architecture Diagrams

## Level 1: System Context Diagram

```mermaid
graph TB
    subgraph "External Users"
        User[Users<br/>Web/Mobile]
        Admin[Administrator<br/>Remote Access]
    end
    
    subgraph "Homelab System"
        HL[Homelab Infrastructure<br/>Self-hosted services]
    end
    
    subgraph "External Services"
        ISP[ISP<br/>Hyproptic<br/>1Gbps Static IP]
        VPS[Gateway VPS<br/>Auth & Proxy<br/>141.147.93.212]
        CF[Cloudflare<br/>DNS]
        OP[1Password<br/>Secrets]
    end
    
    User -->|HTTPS| VPS
    Admin -->|WireGuard| VPS
    VPS -->|WireGuard Tunnel| HL
    HL -->|Internet| ISP
    VPS -->|DNS| CF
    HL -->|Secrets| OP
    
    style HL fill:#1168bd,color:#fff
    style VPS fill:#2ecc71,color:#fff
```

## Level 2: Container Diagram (High-Level Components)

```mermaid
graph TB
    subgraph "External Layer"
        VPS[Gateway VPS<br/>Ubuntu 22.04]
        subgraph "VPS Services"
            Traefik[Traefik<br/>Reverse Proxy]
            Pangolin[Pangolin<br/>SSO/Auth]
            CS[CrowdSec<br/>Security]
            Auth[Authentik<br/>Identity Provider]
        end
    end
    
    subgraph "Network Infrastructure"
        Router[OPNsense<br/>Primary/Secondary<br/>CARP HA]
        Switch[Zyxel XMG-1920<br/>8x2.5G + 2x10G SFP+]
        FlexMini[Ubiquiti Flex Mini<br/>WAN Distribution]
    end
    
    subgraph "Proxmox Infrastructure"
        subgraph "px-net (10.10.101.12)"
            OPN1[OPNsense Primary<br/>VM]
        end
        
        subgraph "px-nas (10.10.101.13)"
            OPN2[OPNsense Secondary<br/>VM]
            TrueNAS[TrueNAS<br/>Storage VM]
        end
        
        subgraph "Virtual Machines"
            Apps[apps-vm<br/>10.100.10.x<br/>AI, DBs, Tools]
            Media[media-vm<br/>10.100.20.x<br/>Media Services]
            Obs[obs-vm<br/>10.100.30.x<br/>Monitoring]
        end
    end
    
    VPS -.->|WireGuard| Router
    Router -->|VLAN Trunk| Switch
    Switch -->|10Gbps SFP+| px-net
    Switch -->|10Gbps SFP+| px-nas
    FlexMini -->|WAN| Router
    
    style VPS fill:#2ecc71,color:#fff
    style Router fill:#e74c3c,color:#fff
    style Apps fill:#3498db,color:#fff
    style Media fill:#9b59b6,color:#fff
    style Obs fill:#f39c12,color:#fff
```

## Level 3: Component Diagram (Service Distribution)

```mermaid
graph TB
    subgraph "apps-vm Services"
        subgraph "AI Stack"
            LiteLLM[LiteLLM<br/>AI Proxy]
            OpenWebUI[Open WebUI<br/>Chat Interface]
            OpenHands[OpenHands<br/>AI Dev Assistant]
        end
        
        subgraph "Databases"
            Neo4j[Neo4j<br/>Graph DB]
            Postgres1[PostgreSQL<br/>Multiple DBs]
        end
        
        subgraph "Tools"
            Atuin[Atuin<br/>Shell History]
            Firecrawl[Firecrawl<br/>Web Scraper]
            Karakeep[Karakeep<br/>Knowledge Base]
            ITTools[IT-Tools<br/>Utilities]
            Enclosed[Enclosed<br/>File Sharing]
        end
    end
    
    subgraph "media-vm Services"
        subgraph "Media Frontend"
            Jellyfin[Jellyfin<br/>Media Server]
            Jellyseerr[Jellyseerr<br/>Request Manager]
            Jellystat[Jellystat<br/>Statistics]
        end
        
        subgraph "Servarr Stack"
            Radarr[Radarr<br/>Movies]
            Sonarr[Sonarr<br/>TV Shows]
            Lidarr[Lidarr<br/>Music]
            Prowlarr[Prowlarr<br/>Indexer]
            Bazarr[Bazarr<br/>Subtitles]
        end
        
        subgraph "Download"
            Deluge[Deluge<br/>Torrent]
            SABnzbd[SABnzbd<br/>Usenet]
            Gluetun[Gluetun<br/>VPN]
        end
    end
    
    subgraph "obs-vm Services"
        subgraph "Monitoring Stack"
            Grafana[Grafana<br/>Dashboards]
            Prometheus[Prometheus<br/>Metrics]
            Loki[Loki<br/>Logs]
            InfluxDB[InfluxDB<br/>Time Series]
        end
        
        subgraph "Management"
            Portainer[Portainer<br/>Container Mgmt]
            Dozzle[Dozzle<br/>Log Viewer]
            UptimeKuma[Uptime Kuma<br/>Monitoring]
            Beszel[Beszel<br/>System Stats]
        end
        
        subgraph "Logging"
            Graylog[Graylog<br/>Log Analysis]
            MongoDB[MongoDB<br/>Graylog DB]
        end
    end
    
    style LiteLLM fill:#3498db,color:#fff
    style Jellyfin fill:#9b59b6,color:#fff
    style Grafana fill:#f39c12,color:#fff
```

## Level 4: Deployment Diagram (Physical Network)

```mermaid
graph TB
    subgraph "Internet"
        ISP[Hyproptic<br/>1Gbps Fiber<br/>Static IP]
        GVPS[Gateway VPS<br/>141.147.93.212<br/>Ubuntu 22.04]
    end
    
    subgraph "Network Cabinet"
        subgraph "Switches"
            ZYX[Zyxel XMG-1920<br/>Main Switch]
            FLEX[Ubiquiti Flex Mini<br/>WAN Distribution]
        end
        
        subgraph "px-net Server"
            CPU1[Intel N355<br/>8 cores]
            RAM1[32GB DDR4]
            NIC1A[enp1s0f0<br/>10G SFP+]
            NIC1B[enp1s0f1<br/>10G SFP+]
            NIC1C[enp2s0<br/>2.5G]
            NIC1D[enp3s0<br/>2.5G]
        end
        
        subgraph "px-nas Server"
            CPU2[Intel i5-12600H<br/>16 cores]
            RAM2[96GB DDR5]
            NIC2A[enp3s0f0np0<br/>10G SFP+]
            NIC2B[enp3s0f1np1<br/>10G SFP+]
            NIC2C[enp88s0<br/>2.5G]
            NIC2D[enp91s0<br/>2.5G]
            HBA[LSI 2008<br/>SAS Controller]
            DISK[2x 16TB HDD<br/>ZFS Mirror]
        end
    end
    
    ISP -->|RJ45| FLEX
    FLEX -->|Port 2| NIC1C
    FLEX -->|Port 4| NIC2C
    
    NIC1A -->|SFP+ Cable| ZYX_P10[Port 10]
    NIC2A -->|SFP+ Cable| ZYX_P9[Port 9]
    NIC1D -->|Port 3 LACP| ZYX
    NIC2D -->|Port 4 LACP| ZYX
    
    GVPS -.->|WireGuard<br/>Tunnel| NIC1C
    
    HBA -->|SAS Cables| DISK
    
    style ZYX fill:#1168bd,color:#fff
    style GVPS fill:#2ecc71,color:#fff
```

## Diagram Key

### Colors
- 🟦 Blue: Core infrastructure components
- 🟩 Green: External/gateway services  
- 🟥 Red: Critical network infrastructure
- 🟪 Purple: Media services
- 🟨 Orange: Monitoring/observability

### Line Types
- Solid lines: Physical connections
- Dashed lines: Logical connections (tunnels, etc.)
- Arrows indicate data flow direction

### Component Types
- Rectangles: Physical devices or VMs
- Rounded rectangles: Services/applications
- Subgraphs: Logical groupings