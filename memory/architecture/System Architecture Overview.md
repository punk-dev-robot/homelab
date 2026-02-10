---
title: System Architecture Overview
type: note
permalink: architecture/system-architecture-overview
tags:
- '["architecture"'
- '"system-design"'
- '"infrastructure"'
- '"multi-tier"]'
---

# System Architecture Overview

## Architecture Summary
- [architecture] Multi-tier homelab infrastructure with external gateway #multi-tier
- [purpose] Self-hosted services with secure external access and internal management #self-hosted
- [scale] 59+ containers across 3 VMs with centralized authentication #container-scale

## Infrastructure Tiers

### Gateway VPS (External Infrastructure)
- [component] External access proxy and authentication gateway #gateway
- [location] Cloud VPS with public IP address #cloud-hosted
- [os] Ubuntu Server with CrowdSec protection #ubuntu
- [protection] Multi-layer security with real-time IP blocking #security
- [access] .nobasura.org domains via Traefik reverse proxy #external-access

**Key Services**:
- [service] Traefik - External routing and SSL termination #traefik
- [service] Pangolin - Single Sign-On authentication #sso
- [service] CrowdSec - Multi-layer threat protection #security

### Homelab VMs (Internal Infrastructure)  
- [component] Service hosting and container orchestration #internal-infrastructure
- [location] Proxmox-hosted VMs on local network #local-network
- [os] Arch Linux for all VMs #arch-linux
- [organization] Specialized by function: apps, media, observability #functional-separation

**VM Specialization**:
- [vm] apps-vm (10.100.10.x) - AI services, tools, databases #apps
- [vm] media-vm (10.100.20.x) - Media services, *arr stack #media  
- [vm] obs-vm (10.100.30.x) - Monitoring, logging, observability #observability

**Access Methods**:
- [access] Direct: .lan addresses (apps.lan, media.lan, obs.lan) #direct-access
- [access] Proxied: .lab.nobasura.org via OpnSense/Unbound + Caddy #proxied-access

### Proxmox (Hypervisor Level)
- [component] VM orchestration and infrastructure management #hypervisor
- [status] Work in progress - not production ready #wip
- [features] VM snapshots, resource allocation, cluster management #vm-management

## Network Architecture

### DNS Resolution Strategy
```
External Access Flow:
Internet → Cloudflare DNS → gateway-vps → Traefik → Pangolin → VMs

Internal Access Flow:  
.lan domains → OpnSense/Unbound → Direct VM access
.lab.nobasura.org → OpnSense/Unbound → Caddy proxy → VMs
```

### Service Discovery Pattern
- [discovery] External: Traefik dynamic configuration #traefik-discovery
- [discovery] Internal: Caddy proxy with static upstreams #caddy-proxy
- [discovery] Container: Docker internal DNS #docker-dns
- [discovery] Monitoring: Service health checks via testing framework #health-monitoring

## Container Architecture

### Service Inheritance Pattern
- [pattern] All services extend standardized base configurations #inheritance
- [standardization] 66/69 services (95.7%) use common.yml inheritance #compliance
- [benefit] Zero redundant configurations across infrastructure #efficiency

```yaml
# Standard service pattern
services:
  service-name:
    extends:
      file: ../common.yml
      service: base  # or socket-base for Docker management
    # Only service-specific configuration here
```

### Base Service Templates
- [template] base - Standard application services #base-template
- [template] socket-base - Services requiring Docker socket access #socket-template
- [provides] Restart policies, environment variables, security, timezone #standard-config

### Stack Organization Pattern
```
files/{vm-name}/
├── ai/           # AI services and tools  
├── dbs/          # Database services
├── lab/          # Dashboard and utilities
├── media/        # Media management and streaming
├── oam/          # Operations, Administration, Monitoring
├── servarr/      # Media automation (*arr stack)
└── common.yml    # Shared service templates
```

## Authentication & Authorization Architecture

### Single Sign-On (SSO) Pattern
- [sso] Pangolin SSO provides centralized authentication #pangolin-sso
- [simplification] Replaced complex Authelia with streamlined solution #simplification
- [integration] 1Password for credential management #credential-management
- [authorization] Role-based permissions via Pangolin #rbac

### Dual Access Strategy
- [strategy] Priority-based routing for different access methods #dual-access
- [api] High priority: API/mobile bypass with authentication headers #api-access
- [web] Lower priority: Web authentication via SSO #web-access

```yaml
# Priority-based routing configuration
http:
  routers:
    # High priority: API/mobile bypass
    service-mobile-bypass:
      rule: "Host(`service.domain.org`) && Header(`traefik-auth-bypass-key`, `${KEY}`)"
      priority: 300
      service: "service-direct@file"
    
    # Lower priority: Web authentication  
    service-auth:
      rule: "Host(`service.domain.org`)"
      priority: 100
      middlewares: ["auth@file"]
      service: "service@http"
```

## Security Architecture

### Multi-Layer Protection
```
Internet → CrowdSec (VPS) → Traefik → Pangolin Auth → Application
          ├── Firewall Bouncer (iptables)
          ├── Traefik Plugin (HTTP)  
          └── Real-time IP blocking
```

### Secret Management Pattern
- [secrets] 1Password integration via Ansible lookup #secret-management
- [template] Secure template processing with no_log protection #secure-templating
- [principle] Zero secrets in version control #secret-security

```yaml
# 1Password integration pattern
secret_value: "{{ lookup('community.general.onepassword', 'SECRET_NAME', vault='Homelab') }}"

# Secure template processing
- name: "Process secure configuration"
  template:
    src: config.yml.j2
    dest: "{{ config_path }}/config.yml"
    mode: '0600'
  no_log: true
```

## Testing Architecture

### Infrastructure Test Separation
- [testing] Gateway VPS testing (external infrastructure) #gateway-testing
- [testing] Homelab VM testing (internal infrastructure) #homelab-testing
- [philosophy] Architecture-first validation - tests define expected behavior #testing-philosophy

```bash
# Separated testing approach
ansible-playbook test_gateway_vps.yml    # External infrastructure
ansible-playbook test_homelab_vms.yml    # Internal infrastructure (🚧 WIP)
```

### Test Validation Principles
- [principle] Tests validate expected behavior, not accommodate bugs #test-integrity
- [example] Expected status codes: 200 (direct), 307 (login redirect) #expected-behavior
- [simulation] Browser simulation for realistic testing #realistic-testing

## Deployment Architecture

### Infrastructure as Code (IaC)
- [iac] Ansible playbooks and roles for all configuration #ansible
- [secrets] 1Password integration for secure credential management #secrets
- [testing] Mandatory pre-commit validation #pre-commit-testing
- [deployment] Idempotent operations with rollback capability #idempotent
- [versioning] Git-based version control for all infrastructure #git-versioned

### Container Update Strategy  
- [automation] Watchtower for regular container updates #automated-updates
- [monitoring] Health checks and rollback capability #health-monitoring
- [persistence] Data separation from containers #data-persistence
- [networking] Isolated container networking #network-isolation

## Performance Architecture

### Latency Optimization
- [performance] Sub-5ms tunnel latency via Pangolin #low-latency
- [caching] Strategic cache placement for performance #caching
- [resources] Proper memory/CPU limits for containers #resource-limits
- [monitoring] Real-time performance metrics #performance-monitoring

### Scalability Patterns
- [horizontal] Multiple VMs for service distribution #horizontal-scaling
- [vertical] Proxmox resource allocation #vertical-scaling  
- [load-balancing] Traefik and Caddy routing #load-balancing
- [storage] Distributed volume management #storage-management

## Relations
- implements [[Container Standardization Patterns]]
- enforces [[Critical Infrastructure Rules]]
- documented_in [[Operations Guide]]
- supports [[Dual Access Strategy]]