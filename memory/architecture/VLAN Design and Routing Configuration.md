---
title: VLAN Design and Routing Configuration
type: note
permalink: architecture/vlan-design-and-routing-configuration
---

# VLAN Design and Routing Configuration

## VLAN Architecture Overview

The network uses 802.1Q VLAN tagging to segment traffic for security, performance, and management purposes. All VLANs are trunked through the main Zyxel switch with VLAN-aware bridges on Proxmox hosts.

## VLAN Definitions and IP Addressing

### Production VLANs

#### VLAN 10 - LAB (Homelab Services)
- **Purpose**: All homelab services and VMs
- **IP Range**: 10.10.10.0/24
- **Gateway**: 10.10.10.1 (OPNsense CARP VIP)
- **Services**: All Docker containers and VMs
- **VM Assignments**:
  - Apps-VM: 10.10.10.11
  - Media-VM: 10.10.10.12
  - Obs-VM: 10.10.10.13
- **Switch Ports**: Fixed on ports 8-10, forbidden on 1-7

#### VLAN 40 - USER (User Devices)
- **Purpose**: End-user devices (laptops, desktops, phones)
- **IP Range**: 10.10.40.0/24
- **Gateway**: 10.10.40.1 (OPNsense CARP VIP)
- **DHCP**: 10.10.40.100-200
- **Switch Ports**: Fixed on ports 2,8-10, forbidden on 1,3-7

#### VLAN 60 - IOT (Internet of Things)
- **Purpose**: IoT devices requiring network isolation
- **IP Range**: 10.10.60.0/24
- **Gateway**: 10.10.60.1 (OPNsense CARP VIP)
- **DHCP**: 10.10.60.100-200
- **Security**: Completely isolated from other VLANs
- **Switch Ports**: Fixed on ports 8-10, forbidden on 1-7

### Infrastructure VLANs

#### VLAN 101 - MGMT (Management)
- **Purpose**: Infrastructure management interfaces
- **IP Range**: 10.10.101.0/24
- **Gateway**: 10.10.101.1 (OPNsense CARP VIP)
- **Static Assignments**:
  - px-net Proxmox: 10.10.101.10
  - px-nas Proxmox: 10.10.101.11
  - OPN1 (primary): 10.10.101.12
  - OPN2 (secondary): 10.10.101.13
  - Zyxel switch: 10.10.101.4
- **Switch Ports**: Fixed on ports 1-8, untagged on 1-2,5-6,9-10

#### VLAN 102 - CARP (High Availability)
- **Purpose**: CARP synchronization between OPNsense instances
- **IP Range**: 10.10.102.0/24
- **Usage**: Heartbeat and state synchronization only
- **Security**: Isolated, no routing to other VLANs
- **Switch Ports**: Fixed on ports 3-4,8

#### VLAN 666 - WAN (External Access)
- **Purpose**: WAN traffic isolation
- **Status**: Available on Flex Mini only
- **Security**: Blocked on main switch for security
- **Usage**: ISP connection distribution to OPNsense instances

#### VLAN 1 - LAN (Default)
- **Purpose**: Default VLAN (unused as per best practice)
- **Status**: Should remain unused
- **Access**: Blocked on all production ports

## Routing Architecture

### OPNsense High Availability Configuration

#### Primary Router (px-net)
```
- WAN: vtnet1 (via vmbr1 → enp2s0 → Flex Mini)
- LAN Trunk: vtnet0 (via vmbr0 → enp1s0f0 SFP+)
- MGMT: vlan02.101
- SYNC: vlan02.102
- IP: 10.10.101.12
```

#### Secondary Router (px-nas)
```
- WAN: vtnet1 (via vmbr1 → enp88s0 → Flex Mini)
- LAN Trunk: vtnet0 (via vmbr0 → enp3s0f0np0 SFP+)
- MGMT: vlan02.101
- SYNC: vlan02.102
- IP: 10.10.101.13
```

#### CARP Virtual IPs
- VLAN 10: 10.10.10.1
- VLAN 40: 10.10.40.1
- VLAN 60: 10.10.60.1
- VLAN 101: 10.10.101.1

## Inter-VLAN Routing Rules

### Allowed Routes
1. **MGMT (101)** → All VLANs: Full administrative access
2. **USER (40)** → LAB (10): Access to homelab services
3. **LAB (10)** → Internet: Outbound access for services
4. **USER (40)** → Internet: General internet access
5. **IOT (60)** → Internet: Limited internet access only

### Blocked Routes
1. **IOT (60)** → **USER (40)**: IOT cannot initiate connections to USER
2. **IOT (60)** → **LAB (10)**: No access to services
3. **CARP (102)** ↔ All VLANs: Sync traffic only
4. **LAB (10)** → **USER (40)**: No initiated connections

### Special Cross-VLAN Routes (Multicast Discovery)

#### USER (40) → IOT (60) - Service Discovery
**Purpose**: Enable cross-VLAN discovery of IoT devices (Sonos, Chromecast) from user devices

**Allowed Traffic**:
1. **mDNS Discovery**: USER → multicast (224.0.0.0/4) port 5353 UDP
   - Enables service discovery via mDNS repeater
   - Works with Spotify Connect, Chromecast
   - Source IP rewritten by mDNS repeater (known limitation)

2. **Spotify Connect**: USER → IOT port 1400 TCP
   - Direct control of Sonos speakers
   - Verified working with Spotify app

3. **IGMP**: USER → any (IGMP protocol)
   - Multicast group membership management
   - Required for IGMP snooping

**Return Traffic**: Stateful firewall automatically allows IOT → USER responses

**Security Notes**:
- IOT devices still cannot initiate connections to USER VLAN
- Only specific discovery and control protocols allowed
- Firewall maintains security isolation while enabling functionality

## Switch Port Configuration

### Zyxel XMG-1920 Port Assignments

| Port | Description | Mode | VLANs | LACP | Notes |
|------|-------------|------|-------|------|-------|
| 1 | Unifi Flex Mini MGMT | Trunk | 101 (PVID) | No | HA switch connection |
| 2 | MGMT Port | Access | 40 (untagged) | No | Admin laptop |
| 3 | px-net MGMT (enp3s0) | Trunk | 101 (PVID), All | T3 | 2.5Gbps |
| 4 | px-nas MGMT (enp91s0) | Trunk | 101 (PVID), All | T4 | 2.5Gbps |
| 5 | px-cpu MGMT (future) | Trunk | 101 (PVID), All | No | Reserved |
| 6 | KBS/JetKVM/Floating | Access | 101 | No | Management tools |
| 7 | QNAP Aggregation | Access | 101 | No | NAS access |
| 8 | WiFi AP | Trunk | 101 (PVID), All | No | All VLANs |
| 9 | px-nas SFP+ | Trunk | 101 (PVID), All | No | 10Gbps |
| 10 | px-net SFP+ | Trunk | 101 (PVID), All | No | 10Gbps |

### Ubiquiti Flex Mini Port Assignments

| Port | Description | VLANs | Purpose |
|------|-------------|-------|---------|
| 1 | PoE In/MGMT | 101 | Power and management |
| 2 | WAN (ISP) | Native | Internet uplink |
| 3 | px-net WAN | Native | Primary OPNsense |
| 4 | px-nas WAN | Native | Secondary OPNsense |
| 5 | Unused | - | Available |

## Proxmox Network Configuration

### VLAN-Aware Bridges

#### vmbr0 - Main VM Traffic Bridge
- **Physical Interface**: SFP+ (10Gbps)
- **VLAN Aware**: Yes
- **VLAN IDs**: 2-4094
- **TSO**: Disabled (compatibility)
- **Purpose**: All VM network traffic

#### vmbr1 - WAN Bridge
- **Physical Interface**: 2.5Gbps ethernet
- **VLAN Aware**: No
- **Purpose**: Direct WAN passthrough to OPNsense

#### vmbr2 - Management/Sync Bridge
- **Physical Interface**: LACP bond
- **VLAN Aware**: Yes
- **VLAN IDs**: 2-4094
- **Tagged VLANs**: 101 (MGMT), 102 (CARP)
- **Purpose**: Management and HA synchronization

## DNS and DHCP Configuration

### DNS Resolution Strategy
- **Internal Resolver**: OPNsense Unbound
- **Domain Structure**:
  - `.lan`: Direct A records to VM IPs
  - `.lab.nobasura.org`: CNAME to .lan domains
  - External: Forwarded to upstream resolvers

### DHCP Configuration
- **VLAN 40 Scope**: 10.10.40.100-200
- **VLAN 60 Scope**: 10.10.60.100-200
- **Reservations**: MAC-based for known devices
- **Options Provided**:
  - DNS servers
  - NTP servers
  - Domain search paths
  - Gateway

## Security Best Practices

### Network Segmentation
1. **Default VLAN Avoidance**: VLAN 1 completely unused
2. **Management Isolation**: Dedicated MGMT VLAN with restricted access
3. **IoT Segregation**: Complete isolation with internet-only access
4. **Service Separation**: LAB VLAN for all homelab services

### Trunk Security
1. **Trunk Minimization**: Only where necessary
2. **VLAN Pruning**: Forbidden VLANs on access ports
3. **Native VLAN**: Proper PVID assignment
4. **Port Security**: Unused ports disabled

### Firewall Policies
1. **Default Deny**: All inter-VLAN traffic blocked by default
2. **Explicit Allow**: Only necessary routes permitted
3. **Stateful Rules**: Return traffic properly handled
4. **Logging**: All denied traffic logged for analysis

## Monitoring and Troubleshooting

### Key Metrics
- CARP status and failover events
- Inter-VLAN traffic flows
- DHCP lease utilization
- DNS query performance

### Common Issues and Solutions
1. **VLAN Tagging**: Verify trunk configuration on switches and Proxmox
2. **CARP Failover**: Check VLAN 102 connectivity and sync settings
3. **DNS Resolution**: Verify Unbound configuration and forwarders
4. **DHCP**: Check scope exhaustion and reservations

## Related Documentation
- [[Network Architecture Complete Overview]]
- [[High Availability Configuration]]
- [[Service Distribution]]
- [[Physical Network Topology]]

Tags: #vlan #routing #networking #security #homelab #opnsense