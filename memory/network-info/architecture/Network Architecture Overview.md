---
title: Network Architecture Overview
type: note
permalink: network-info/architecture/network-architecture-overview
---

# Network Architecture Overview

## Infrastructure Summary

This homelab network consists of:
- **2 Proxmox nodes** (px-net, px-nas) running standalone (not clustered)
- **3 VMs** distributed across nodes (apps-vm, media-vm, obs-vm)
- **1 Gateway VPS** for external access
- **High-speed core network** with 10Gbps SFP+ backbone
- **VLAN-segmented** architecture for security and organization
- **High availability** OPNsense with CARP failover

## Physical Network Topology

### Core Infrastructure
- **Internet**: 1 Gbps symmetric fiber from Hyproptic (static IP)
- **Main Switch**: Zyxel XMG-1920 (8x 2.5Gbps + 2x 10Gbps SFP+)
- **HA Switch**: Ubiquiti Flex Mini (5-port, PoE powered)

### Server Hardware
- **px-net**: Intel N355 (8 cores), 32GB RAM, 2x2.5Gbps + 2x10Gbps SFP+
- **px-nas**: Intel i5-12600H (16 cores), 96GB RAM, 2x2.5Gbps + 2x10Gbps SFP+
- **px-cpu** (planned): Intel i9 13th gen (24 cores), 96GB RAM

## Network Architecture Layers

### Layer 1: Physical Connectivity
- 10Gbps SFP+ connections for inter-VM traffic
- 2.5Gbps connections for management and WAN
- LACP bonding configured (future expansion ready)

### Layer 2: VLAN Segmentation
- **VLAN 10 (LAB)**: Homelab services
- **VLAN 40 (USER)**: User devices
- **VLAN 60 (IOT)**: IoT devices
- **VLAN 101 (MGMT)**: Management interfaces
- **VLAN 102 (CARP)**: High availability sync
- **VLAN 666 (WAN)**: External access (isolated)

### Layer 3: Routing & Security
- Primary OPNsense on px-net (10.10.101.12)
- Secondary OPNsense on px-nas (10.10.101.13)
- CARP VIP for automatic failover
- Firewall rules enforcing VLAN isolation

### Layer 4: Services
- **Apps-VM**: AI services, databases, tools
- **Media-VM**: Media services, *arr stack
- **Obs-VM**: Monitoring, logging, observability
- **Gateway VPS**: External access, authentication

## Access Patterns

### Internal Access
- Direct: `*.lan` domains (apps.lan, media.lan, obs.lan)
- Proxied: `*.lab.nobasura.org` via Caddy reverse proxy

### External Access
- Gateway VPS with public IP
- WireGuard tunnel to homelab
- Traefik reverse proxy with Pangolin SSO
- `*.nobasura.org` domains

## High Availability Design

### Network Level
- Dual OPNsense instances with CARP
- Automatic failover on primary failure
- Synchronized configuration

### Service Level
- Watchtower for automatic container updates
- Health monitoring via Uptime Kuma
- Distributed services across multiple VMs

## Security Architecture

### Network Segmentation
- VLANs isolate different device/service types
- Firewall rules control inter-VLAN traffic
- Management network separated from services

### External Protection
- CrowdSec on gateway VPS
- Traefik with authentication middleware
- WireGuard encrypted tunnels
- No direct exposure of homelab services

## Navigation

- [C4 Architecture Diagrams](./c4-diagrams.md)
- [VLAN Design & Routing](./vlan-design.md)
- [High Availability Configuration](./high-availability.md)
- [Service Distribution](./service-distribution.md)
- [Physical Network Topology](./physical-topology.md)