---
title: Network Architecture Complete Overview
type: note
permalink: architecture/network-architecture-complete-overview
---

# Network Architecture Complete Overview

## Infrastructure Summary

This homelab network consists of:
- **2 Proxmox nodes** (px-net, px-nas) running standalone (not clustered)
- **3 VMs** distributed across nodes (apps-vm, media-vm, obs-vm)
- **1 Gateway VPS** for external access
- **High-speed core network** with 10Gbps SFP+ backbone
- **VLAN-segmented** architecture for security and organization
- **High availability** OPNsense with CARP failover

## Hardware Specifications

### WAN Connection
- 1 Gbps symmetric fiber from Hyproptic
- Static IP address
- RJ45 wall socket connection

### Network Hardware

#### Zyxel XMG-1920 (Main Switch)
- 8x 2.5Gbps ports with PoE out
- 2x 10Gbps SFP+ ports
- Full managed switch capabilities

#### Ubiquiti Flex Mini (HA Switch)
- 5-port switch with PoE in
- Port assignments:
  - Port 1: PoE in/MGMT (VLAN 101)
  - Port 2: WAN
  - Port 3: px-net (enp2s0)
  - Port 4: px-nas (enp88s0)

### Server Hardware

#### px-net (Firewall Appliance)
- **CPU**: Intel N355 (8 cores)
- **RAM**: 32 GB DDR4
- **Network**: 2x 2.5Gbps ethernet + 2x 10Gbps SFP+
- **Storage**: 500GB boot NVMe + 1TB services NVMe
- **Role**: Primary OPNsense, network services

#### px-nas (NAS Mini-PC)
- **CPU**: Intel i5-12600H (16 cores, 12th gen)
- **RAM**: 96 GB DDR5
- **Network**: 2x 2.5Gbps ethernet + 2x 10Gbps SFP+
- **Storage**: 1TB boot NVMe + 2x 16TB HDD (RAID1) + 2x 8TB HDD (RAID1)
- **Role**: Storage, secondary OPNsense, backup services

#### px-cpu (Planned)
- **CPU**: Intel i9 13th gen (24 cores)
- **RAM**: 96 GB DDR5
- **Role**: Compute-intensive workloads

## VLAN Architecture

### Production VLANs
- **VLAN 1**: LAN (default, unused)
- **VLAN 10**: LAB - Homelab services network
- **VLAN 40**: USER - User devices network
- **VLAN 60**: IOT - IoT devices network

### Infrastructure VLANs
- **VLAN 101**: MGMT - Management interfaces
- **VLAN 102**: CARP - OPNsense high availability sync
- **VLAN 666**: WAN - External access (isolated to Flex Mini)

## Network Architecture Layers

### Layer 1: Physical Connectivity
- 10Gbps SFP+ connections for inter-VM traffic
- 2.5Gbps connections for management and WAN
- LACP bonding configured (future expansion ready)

### Layer 2: VLAN Segmentation
- Proper isolation between service, user, and IoT networks
- Management network separated from production
- WAN VLAN isolated to specific ports

### Layer 3: Routing & Security
- **Primary OPNsense**: px-net (10.10.101.12)
- **Secondary OPNsense**: px-nas (10.10.101.13)
- **CARP VIP**: Automatic failover between instances
- Firewall rules enforcing strict VLAN isolation

### Layer 4: Services Distribution

#### Apps-VM
- AI services and tools
- Databases
- Development tools
- Network: 10.10.10.11

#### Media-VM
- Media services
- *arr stack (Sonarr, Radarr, etc.)
- Jellyfin, Plex
- Network: 10.10.10.12

#### Obs-VM
- Monitoring (Prometheus, Grafana)
- Logging (Loki, Dozzle)
- Observability tools
- Network: 10.10.10.13

## Access Patterns

### Internal Access
- **Direct Access**: `*.lan` domains (apps.lan, media.lan, obs.lan)
- **Proxied Access**: `*.lab.nobasura.org` via Caddy reverse proxy
- All internal services accessible from USER VLAN

### External Access
- **Gateway VPS**: Public IP with CrowdSec protection
- **WireGuard Tunnel**: Encrypted connection to homelab
- **Traefik Proxy**: Reverse proxy with Pangolin SSO
- **Public Domains**: `*.nobasura.org`

## High Availability Design

### Network Level HA
- Dual OPNsense instances with CARP protocol
- Automatic failover within seconds
- Synchronized configuration between instances
- Dedicated CARP VLAN for heartbeat

### Service Level HA
- Watchtower for automatic container updates
- Uptime Kuma for health monitoring
- Services distributed across multiple VMs
- Backup services on px-nas

## Security Architecture

### Network Segmentation
- VLANs isolate different device/service types
- Strict firewall rules control inter-VLAN traffic
- Management network completely separated
- Default deny policy with explicit allows
- Cross-VLAN service discovery enabled (mDNS repeater for Sonos/Chromecast)

### External Protection
- **CrowdSec**: Threat intelligence and blocking on gateway
- **Traefik + Pangolin**: Authentication middleware
- **WireGuard**: Encrypted tunnel for all external access
- **No Direct Exposure**: All homelab services behind gateway

### Internal Security
- Separate VLANs for different trust levels
- Management interfaces on dedicated network
- Service-to-service communication controlled
- Regular security updates via Watchtower

## IP Addressing Scheme

### VLAN 10 (LAB)
- Network: 10.10.10.0/24
- Gateway: 10.10.10.1
- Apps-VM: 10.10.10.11
- Media-VM: 10.10.10.12
- Obs-VM: 10.10.10.13

### VLAN 40 (USER)
- Network: 10.10.40.0/24
- Gateway: 10.10.40.1

### VLAN 60 (IOT)
- Network: 10.10.60.0/24
- Gateway: 10.10.60.1

### VLAN 101 (MGMT)
- Network: 10.10.101.0/24
- Gateway: 10.10.101.1
- px-net: 10.10.101.10
- px-nas: 10.10.101.11
- OPN1: 10.10.101.12
- OPN2: 10.10.101.13

### VLAN 102 (CARP)
- Network: 10.10.102.0/24
- Used for CARP heartbeat only

## Related Documentation

### Core Architecture
- [[VLAN Design and Routing Configuration]]
- [[Service Distribution Architecture]]
- [[High Availability Configuration]]
- [[Physical Network Topology]]

### Infrastructure Components
- [[Zyxel Switch Configuration]] - Port assignments, VLAN config, IGMP snooping
- [[OPNsense Services Configuration]] - mDNS repeater, firewall rules, DNS/DHCP
- [[ADR-002: Sonos Cross-VLAN Discovery Solution]] - Cross-VLAN multicast implementation

### Educational Resources
- [[Multicast and IGMP Snooping Explained]] - Deep dive into multicast networking

Tags: #network #architecture #infrastructure #homelab #proxmox #opnsense