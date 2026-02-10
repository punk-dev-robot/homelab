---
title: Container Service Architecture
type: note
permalink: architecture/container-service-architecture
tags:
- '["container-architecture"'
- '"service-categorization"'
- '"inheritance-patterns"'
- '"port-management"]'
---

# Container Service Architecture

## Architecture Summary  
- [overview] Categorization of all 59+ homelab services by inheritance patterns #service-categorization
- [standardization] 95.7% compliance with common.yml inheritance model #high-compliance
- [organization] Services organized by socket access requirements and deployment patterns #organized-architecture

## Service Inheritance Architecture

### Base Service Extension (`extends: base`)
- [purpose] Standard application services without Docker socket access requirements #standard-applications
- [count] 48 services across all VMs #base-service-count
- [inheritance] Provides restart policies, environment variables, security, timezone sync #inherited-config

**Standard Configuration Provided**:
- [config] `restart: unless-stopped` for automatic recovery #restart-policy
- [config] Standard environment variables: `PUID`, `PGID`, `TZ`, `UMASK`, `LOG_LEVEL` #env-variables
- [config] Security: `no-new-privileges:true` for container security #security-config
- [config] Timezone sync: `/etc/localtime:/etc/localtime:ro` #timezone-sync

### Socket-Base Service Extension (`extends: socket-base`)
- [purpose] Services requiring Docker socket access via socket-proxy #docker-management
- [count] 18 services for container management functions #socket-service-count
- [inheritance] All base features plus Docker socket proxy connection #enhanced-config

**Additional Configuration Provided**:
- [config] Docker socket proxy connection: `DOCKER_HOST=tcp://socket-proxy:2375` #docker-proxy
- [config] Network access to socket-proxy service #proxy-network
- [config] Automatic dependency on socket-proxy service #dependency-management

## Service Distribution by VM

### Apps-VM Services (13 services)
- [category] AI Services: `litellm`, `litellm_db`, `litellm_prometheus`, `open_webui` #ai-services
- [category] Development Tools: `atuin`, `atuin_db`, `firecrawl`, `it-tools` #dev-tools
- [category] Database: `neo4j` for graph database functionality #database
- [category] Lab Management: `homepage` with direct Docker socket access #lab-management

### Media-VM Services (23 services)
- [category] Jellyfin Stack: `jellyfin`, `jellyseerr`, `jellystat`, `jellystat-db`, `jolly`, `stash` #jellyfin-stack
- [category] Servarr Stack: `bazarr`, `deluge`, `flaresolverr`, `lidarr`, `nzbget`, `prowlarr`, `radarr`, `readarr`, `recyclarr`, `sabnzbd`, `sonarr`, `whisparr` #servarr-stack
- [category] Network: `gluetun` for VPN connectivity, `notifiarr` for notifications #network-services

### Obs-VM Services (23 services)
- [category] Monitoring: `prometheus`, `node-exporter`, `cadvisor`, `pbs-exporter`, `pihole-exporter` #monitoring-services
- [category] Visualization: `grafana` for dashboards and analytics #visualization
- [category] Logging: `loki`, `promtail` for log aggregation #logging-services
- [category] Applications: `beszel`, `gotify`, `uptime-kuma` for operational tools #operational-apps
- [category] Advanced Logging: `graylog`, `graylog-mongodb`, `graylog-datanode` #enterprise-logging

## Socket-Base Service Categories

### Container Management Services (All VMs)
- [service] Watchtower: Automated container updates (apps-vm, media-vm, obs-vm) #automated-updates
- [service] Deunhealth: Health monitoring and restart (apps-vm, media-vm, obs-vm) #health-monitoring  
- [service] Docker-GC: Container cleanup (apps-vm, media-vm, obs-vm) #container-cleanup

### Monitoring and Management
- [service] Dozzle: Container log viewing (obs-vm) #log-viewing
- [service] Dozzle-Agent: Log collection (apps-vm) #log-collection
- [service] Portainer: Container management (obs-vm) #container-management
- [service] Portainer-Agent: Management agents (apps-vm, media-vm) #management-agents

## Special Cases (Cannot Use Inheritance)

### Direct Docker Socket Access Required
- [special-case] Services that mount docker.sock directly #direct-socket-access
- [count] 3 services with specific requirements #special-case-count

**1. Socket-Proxy (All VMs)**
- [reason] Provides the proxy service itself #proxy-provider
- [requirement] Direct mount `/var/run/docker.sock:/var/run/docker.sock:ro` #direct-mount
- [role] Foundation service for socket-base inheritance #foundation-service

**2. Homepage (Apps-VM)**  
- [reason] Requires full Docker API access for dashboard container discovery #full-api-access
- [requirement] Direct socket mount for container enumeration #container-discovery
- [inheritance] Extends `base` for other standardization benefits #partial-inheritance

**3. OpenHands (Apps-VM) - Currently Commented Out**
- [reason] Manages development containers requiring full Docker API #dev-container-management
- [requirement] Direct socket mount for container lifecycle management #lifecycle-management
- [status] Reserved port 3003, ready for future activation #reserved-service

### Gateway Services (Immutable Infrastructure)
- [classification] Treated as immutable production infrastructure #immutable-infrastructure
- [services] `pangolin`, `traefik`, `crowdsec`, `auth-bypass`, `middleware-manager` #gateway-services
- [policy] No standardization applied to maintain production stability #stability-priority

## Port Management Architecture

### Per-VM Port Allocation Strategy
- [strategy] VM-specific IP ranges prevent port conflicts #ip-segregation
- [allocation] Sequential port assignment within VMs #sequential-allocation

**Apps-VM Port Map (10.100.10.x)**:
- [port] 3000: OpenWebUI for AI interface #ai-interface
- [port] 3003: OpenHands (reserved, currently commented out) #dev-reserved
- [port] 4000: LiteLLM API gateway #ai-gateway
- [port] 5432: LiteLLM Database (PostgreSQL) #ai-database
- [port] 7474: Neo4j HTTP interface #graph-http
- [port] 7687: Neo4j Bolt protocol #graph-bolt
- [port] 8888: Atuin shell history #shell-history
- [port] 9090: LiteLLM Prometheus metrics #ai-metrics

**Media-VM Port Allocation**:
- [allocation] Sequential port allocation starting from 6767 #media-ports
- [networking] VPN services (gluetun) handle proxy routing for *arr services #vpn-routing

**Obs-VM Port Map (10.100.30.x)**:
- [port] 3000: Grafana dashboard #grafana-dashboard
- [port] 3001: Uptime Kuma monitoring #uptime-monitoring
- [port] 3100: Loki log aggregation #log-aggregation
- [port] 8080: Dozzle log viewer #log-viewer
- [port] 8090: Beszel system monitoring #system-monitoring
- [port] 9000: Graylog enterprise logging #enterprise-logging
- [port] 9090: Prometheus metrics #prometheus-metrics
- [port] 9617: PiHole Exporter metrics #pihole-metrics

### Conflict Resolution Strategy
- [principle] Within VM: Port conflicts resolved by assignment #within-vm-resolution
- [principle] Cross-VM: No conflicts due to different IP addresses #cross-vm-isolation
- [documentation] Reserved ports documented to prevent future conflicts #conflict-prevention

## Health Monitoring Integration

### Deunhealth Configuration
- [integration] Services with healthcheck configurations get automatic labels #health-integration
- [label] `deunhealth.restart.on.unhealthy=true` for health-monitored services #restart-labels
- [monitoring] Deunhealth monitors via socket-proxy and restarts unhealthy containers #automated-recovery

### Watchtower Integration
- [updates] Automatic container updates with exclusion controls #update-automation
- [exclusion] `com.centurylinklabs.watchtower.monitor-only` for critical services #update-exclusion
- [policy] Critical infrastructure excluded from automatic updates #critical-exclusion

## Network Architecture

### Standard Network Patterns
- [networking] Default: Most services use default Docker Compose networks #default-networking
- [networking] Socket Proxy: Management services connect via `socket_proxy` network #proxy-networking
- [networking] VPN: Media services route through `gluetun` service network #vpn-networking

### External Access Patterns
- [access] Internal HTTP: Direct access for admin interfaces (e.g., Neo4j) #internal-http
- [access] External HTTPS: All public services routed through Traefik on gateway-vps #external-https
- [access] Dual Access: Mobile/API bypass + web authentication routing #dual-access

## Validation and Success Metrics

### Achieved Standardization Results
- [achievement] 59 containers running across 3 VMs #total-containers
- [achievement] Zero restart loops after deployment #stable-deployment
- [achievement] Zero redundant restart policies in service definitions #clean-config
- [achievement] 100% standardization of eligible services #full-compliance
- [achievement] Automatic recovery via deunhealth monitoring #automated-recovery
- [achievement] Zero port conflicts within VMs #conflict-free

### Validation Commands
```bash
# Verify zero restart policies in service definitions
ansible-playbook -i inventory.yml validate_container_standardization.yml

# Check all containers running
ansible all -i inventory.yml -m shell -a "docker ps --filter 'status=running' | wc -l"

# Verify no restart loops
ansible all -i inventory.yml -m shell -a "docker ps -a --filter 'status=restarting'"

# Check deunhealth monitoring
ansible all -i inventory.yml -m shell -a "docker logs deunhealth --tail 5"
```

## Future Architecture Considerations

### Migration Readiness
- [preparation] Foundation established for Podman migration #podman-ready
- [preparation] Standard Docker Compose features used throughout #compose-standard
- [preparation] Easy removal path when migrating to orchestrators #orchestrator-ready

### Scalability Planning
- [planning] Architecture supports horizontal scaling across VMs #horizontal-ready
- [planning] Service categories enable organized growth #organized-growth
- [planning] Standardization simplifies operational complexity #operational-simplicity

## Relations
- implements [[System Architecture Overview]]
- enforces [[Critical Infrastructure Rules]]
- documented_in [[ADR-001: Container Availability Improvements]]
- uses [[Container Standardization Patterns]]