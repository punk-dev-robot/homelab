# Homelab Infrastructure

A comprehensive overview of all virtual machines and containerized services running across the homelab environment.

## 🏗️ Proxmox Infrastructure

Network and storage foundation layer running on Proxmox VE hypervisor cluster.

### Network Services

- **[OPNsense](https://github.com/opnsense/core)** - Open-source FreeBSD-based firewall and routing platform with HA failover support. Provides network security, VPN, and traffic shaping for the entire homelab.
- **[TrueNAS](https://github.com/truenas/middleware)** - Enterprise-grade ZFS-based network-attached storage (NAS) solution. Manages storage pools, datasets, and NFS shares for all VMs and services.
- **[Proxmox Backup Server](https://github.com/proxmox/proxmox-backup)** - Deduplicating backup solution designed for Proxmox VE environments. Provides automated VM backups with efficient storage and restore capabilities.

## 🌐 Gateway VPS (External Access)

Public-facing reverse proxy and authentication gateway running on Oracle Cloud VPS.

- **[Traefik](https://github.com/traefik/traefik)** - Modern cloud-native reverse proxy and load balancer with automatic HTTPS. Routes external traffic to internal services with dynamic configuration.
- **[Pangolin](https://github.com/RobinThrift/Pangolin)** - Lightweight API gateway and request router. Provides additional routing logic and API management for external access.
- **[Gerbil](https://github.com/RobinThrift/Gerbil)** - WireGuard VPN tunnel manager for secure gateway-to-homelab connectivity. Maintains encrypted tunnel between VPS and internal network.
- **[CrowdSec](https://github.com/crowdsecurity/crowdsec)** - Collaborative intrusion prevention system with community-driven threat intelligence. Blocks malicious IPs and protects all externally exposed services.
- **[Authentik](https://github.com/goauthentik/authentik)** - Modern SSO and identity provider supporting OAuth2, SAML, and LDAP. Centralizes authentication for all exposed services with multi-factor support.
- **[Beszel Agent](https://github.com/henrygd/beszel)** - Lightweight server monitoring agent. Collects system metrics and sends them to the central Beszel instance.
- **[Dozzle](https://github.com/amir20/dozzle)** - Real-time Docker container log viewer with a clean web interface. Provides centralized log access for all gateway containers.

## 🤖 Apps VM (apps.lan)

AI services, utilities, and automation tools.

### OAM Stack (Operations/Automation/Monitoring)

_This standardized stack also runs on Media VM and Obs VM_

- **[Watchtower](https://github.com/containrrr/watchtower)** - Automated Docker container update service. Monitors for new images and updates running containers with configurable schedules.
- **[Docker-GC](https://github.com/spotify/docker-gc)** - Garbage collection for Docker images, containers, and volumes. Automatically cleans up unused resources to save disk space.
- **[Portainer Agent](https://github.com/portainer/agent)** - Lightweight agent for Portainer remote management. Enables centralized Docker management from Portainer UI.
- **[Deunhealth](https://github.com/qdm12/deunhealth)** - Health check orchestrator for Docker containers. Monitors container health and can trigger automated recovery actions.
- **[Dozzle Agent](https://github.com/amir20/dozzle)** - Log streaming agent for centralized log viewing. Streams container logs to the central Dozzle instance.
- **[Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy)** - Security proxy for Docker socket access. Restricts Docker API access with fine-grained permissions for better security.

### AI Stack

- **[LiteLLM](https://github.com/BerriAI/litellm)** - Universal LLM proxy supporting OpenAI, Anthropic, Azure, and 100+ providers. Provides unified API interface and request routing with load balancing.
- **[OpenWebUI](https://github.com/open-webui/open-webui)** - Feature-rich web interface for local and cloud LLMs. Offers ChatGPT-like experience with support for multiple models and RAG capabilities.

### Tools

- **[Firecrawl](https://github.com/mendableai/firecrawl)** - API for web scraping and crawling optimized for LLM data extraction. Converts websites to clean markdown or structured data.
- **[Atuin](https://github.com/atuinsh/atuin)** - Shell history sync and search tool with encrypted cloud backup. Replaces standard shell history with searchable, synchronized command database.
- **[IT-Tools](https://github.com/CorentinTh/it-tools)** - Collection of web-based utilities for developers and IT professionals. Includes encoders, generators, converters, and other handy tools in one place.
- **[Enclosed](https://github.com/CorentinTh/enclosed)** - Secure, client-side file encryption and sharing tool. Encrypts files in the browser before upload for privacy-focused file sharing.
- **[Karakeep](https://github.com/karakeep/karakeep)** - Personal knowledge management and note-taking application. Organizes notes with markdown support and full-text search.

### Databases

- **[Neo4j](https://github.com/neo4j/neo4j)** - Graph database optimized for connected data and relationships. Used for knowledge graphs and relationship-heavy data modeling.

### Lab

- **[Homepage](https://github.com/gethomepage/homepage)** - Customizable application dashboard with service status widgets. Serves as the central hub for accessing all homelab services.

## 📺 Media VM (media.lan)

Media streaming and automated content management.
_Uses same OAM stack as Apps VM_

### Servarr Ecosystem

- **[Gluetun](https://github.com/qdm12/gluetun)** - VPN client container supporting multiple providers with killswitch. Routes torrent traffic through VPN for privacy and security.
- **[Deluge](https://github.com/deluge-torrent/deluge)** - Lightweight BitTorrent client with web interface and plugin support. Handles torrent downloads managed by the Arr apps.
- **[Prowlarr](https://github.com/Prowlarr/Prowlarr)** - Indexer manager and proxy for Usenet and torrent trackers. Centralizes indexer configuration for all Arr applications.
- **[Radarr](https://github.com/Radarr/Radarr)** - Movie collection manager with automated downloading and organization. Monitors for releases, sends to download clients, and renames/organizes files.
- **[Sonarr](https://github.com/Sonarr/Sonarr)** - TV series collection manager with episode tracking and automation. Monitors show schedules, downloads episodes, and maintains organized library.
- **[Lidarr](https://github.com/Lidarr/Lidarr)** - Music collection manager for automated album downloads. Monitors artists, downloads releases, and organizes music library.
- **[Bazarr](https://github.com/morpheus65535/bazarr)** - Subtitle automation companion for Radarr and Sonarr. Downloads and synchronizes subtitles in multiple languages for your media.
- **[Recyclarr](https://github.com/recyclarr/recyclarr)** - Configuration sync tool for Arr applications using TRaSH Guides. Automates quality profiles and custom format setup across all Arr apps.
- **[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr)** - Proxy server to bypass Cloudflare and DDoS-GUARD protection. Enables access to protected indexers and trackers.
- **[NZBGet](https://github.com/nzbget/nzbget)** - Efficient Usenet binary downloader with minimal resource usage. Handles NZB downloads with automated post-processing.
- **[SABnzbd](https://github.com/sabnzbd/sabnzbd)** - Alternative Usenet downloader with extensive automation features. Provides more configuration options and plugin support than NZBGet.
- **[Notifiarr](https://github.com/Notifiarr/notifiarr)** - Unified notification client for Arr applications and Plex. Sends rich notifications to Discord, Telegram, and other platforms.

### Media Streaming

- **[Jellyfin](https://github.com/jellyfin/jellyfin)** - Open-source media server for streaming movies, TV shows, and music. Provides clients for all platforms without subscription fees or tracking.
- **[Jellyseerr](https://github.com/Fallenbagel/jellyseerr)** - Request management system for Jellyfin media libraries. Allows users to request content which automatically triggers Arr apps.
- **[Jellystat](https://github.com/CyferShepard/Jellystat)** - Statistics and analytics platform for Jellyfin servers. Tracks viewing history, user activity, and library statistics.
- **[Janitorr](https://github.com/Schaka/Janitorr)** - Automated media library cleanup tool. Removes watched content based on configurable rules to manage disk space.

## 📊 Observability VM (obs.lan)

Monitoring, logging, and operational visibility.
_Uses same OAM stack as Apps VM_

### Monitoring Stack

- **[Grafana](https://github.com/grafana/grafana)** - Analytics and monitoring visualization platform. Creates dashboards from multiple data sources including Prometheus, Loki, and InfluxDB.
- **[Prometheus](https://github.com/prometheus/prometheus)** - Time-series database and monitoring system with powerful query language. Scrapes metrics from services and stores them for analysis and alerting.
- **[Loki](https://github.com/grafana/loki)** - Log aggregation system designed to work with Grafana. Indexes metadata instead of full-text for efficient log storage and querying.
- **[InfluxDB](https://github.com/influxdata/influxdb)** - Time-series database optimized for high write loads. Stores metrics from IoT devices, monitoring agents, and application telemetry.

### Logging

- **[Graylog](https://github.com/Graylog2/graylog2-server)** - Centralized log management platform with full-text search. Collects, indexes, and analyzes logs from all infrastructure components.

### Operations

- **[Beszel](https://github.com/henrygd/beszel)** - Lightweight server monitoring dashboard with agent-based collection. Tracks CPU, memory, disk, and network metrics across all hosts.
- **[Dozzle](https://github.com/amir20/dozzle)** - Real-time Docker log viewer with multi-host support. Provides centralized access to container logs without heavy logging infrastructure.
- **[Gotify](https://github.com/gotify/server)** - Self-hosted push notification server with Android app. Receives alerts from monitoring systems and sends push notifications to mobile devices.
- **[Portainer](https://github.com/portainer/portainer)** - Web-based Docker management UI for containers and stacks. Manages Docker resources across multiple hosts from a single interface.
- **[Uptime Kuma](https://github.com/louislam/uptime-kuma)** - Self-hosted uptime monitoring and status page platform. Monitors service availability and sends alerts on downtime.

---

**Total Infrastructure**: 3 Proxmox VMs + 7 Gateway containers + 49 Docker services across 3 homelab VMs
