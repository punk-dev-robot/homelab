---
title: Zyxel Switch Configuration
type: note
permalink: architecture/zyxel-switch-configuration
---

# Zyxel XMG-1920 Switch Configuration

## Switch Overview

**Model**: Zyxel XMG-1920  
**Firmware**: Latest  
**Management IP**: 10.10.101.4 (VLAN 101)  
**Role**: Core network switch with VLAN segmentation and multicast support

## Port Configuration

### Port Assignments

| Port | Active | Name | Speed/Duplex | Flow Control | 802.1p Priority | Media Type |
|------|--------|------|--------------|--------------|-----------------|------------|
| * | No | (unnamed) | Auto | No | 0 | SFP+ |
| 1 | Yes | unifi flex mini mgmt (wan) | Auto | No | 0 | - |
| 2 | Yes | arch | Auto | No | 0 | - |
| 3 | Yes | kbs1 | Auto | No | 0 | - |
| 4 | Yes | TMP jet | Auto | No | 0 | - |
| 5 | Yes | mgmt trunk from px-nas | Auto | No | 0 | - |
| 6 | Yes | mgmt trunk from px-cpu | Auto | No | 0 | - |
| 7 | Yes | wifi | Auto | No | 0 | - |
| 8 | Yes | px-net vlans | Auto | No | 0 | - |
| 9 | Yes | px-nas vlans | Auto | No | 0 | SFP+ |
| 10 | Yes | px-cpu vlans | Auto | No | 0 | SFP+ |

### Port Details

#### Port 1 - Unifi Flex Mini (WAN Management)
- **Connection**: Ubiquiti Flex Mini HA switch
- **VLAN**: 101 (MGMT) untagged
- **Purpose**: Management access to HA switch
- **Speed**: 2.5Gbps

#### Port 2 - Arch (User Device)
- **Connection**: User workstation
- **VLAN**: 40 (USER) untagged
- **Purpose**: Admin/developer workstation access
- **Speed**: 2.5Gbps

#### Port 3 - KBS1 (Keyboard/KVM)
- **Connection**: KVM switch or management device
- **VLAN**: 101 (MGMT) untagged
- **Purpose**: Direct management access
- **Speed**: 2.5Gbps

#### Port 4 - TMP Jet (JetKVM)
- **Connection**: JetKVM management device
- **VLAN**: 101 (MGMT) untagged
- **Purpose**: Remote management and console access
- **Speed**: 2.5Gbps

#### Port 5 - px-nas Management Trunk
- **Connection**: px-nas enp91s0 (2.5Gbps)
- **VLAN**: 101 (MGMT) PVID, plus CARP (102)
- **Purpose**: Management and CARP sync for secondary OPNsense
- **Speed**: 2.5Gbps

#### Port 6 - px-cpu Management Trunk
- **Connection**: px-cpu management interface (future)
- **VLAN**: 101 (MGMT) PVID, plus all VLANs for future expansion
- **Purpose**: Management trunk for compute node
- **Speed**: 2.5Gbps
- **Status**: Reserved for future use

#### Port 7 - WiFi Access Point
- **Connection**: Wireless access point
- **VLAN**: 101 (MGMT) PVID, all VLANs tagged (10, 40, 60, 101, 102, 666)
- **Purpose**: Wireless access to all network segments
- **Speed**: 2.5Gbps

#### Port 8 - px-net Main Trunk
- **Connection**: px-net management interface enp3s0 (2.5Gbps)
- **VLAN**: 101 (MGMT) PVID, plus all VLANs
- **Purpose**: Management trunk for primary OPNsense host
- **Speed**: 2.5Gbps

#### Port 9 - px-nas SFP+ Trunk (LAN)
- **Connection**: px-nas enp3s0f0np0 (SFP+)
- **VLAN**: All VLANs tagged (10, 40, 60, 101, 102)
- **Purpose**: High-speed trunk for secondary OPNsense VM traffic
- **Speed**: 10Gbps
- **Media**: SFP+

#### Port 10 - px-net SFP+ Trunk (LAN)
- **Connection**: px-net enp1s0f0 (SFP+)
- **VLAN**: All VLANs tagged (10, 40, 60, 101, 102)
- **Purpose**: High-speed trunk for primary OPNsense VM traffic
- **Speed**: 10Gbps
- **Media**: SFP+

## VLAN Configuration

### VLAN Status Summary

| Index | VID | Name | Tagged Ports | Untagged Ports | Elapsed Time | Status |
|-------|-----|------|--------------|----------------|--------------|--------|
| 1 | 1 | LAN | - | - | 23:29:26 | Static |
| 2 | 10 | LAB | 7-10 | 3 | 12:49:10 | Static |
| 3 | 40 | USER | 7-10 | 2 | 23:29:26 | Static |
| 4 | 60 | IOT | 7-10 | - | 23:29:26 | Static |
| 5 | 101 | MGMT | 5-7 | 1,4 | 11:59:46 | Static |
| 6 | 102 | CARP | 5-6 | - | 12:52:00 | Static |
| 7 | 666 | WAN | - | - | 23:29:26 | Static |

### VLAN Detailed Configuration

#### VLAN 1 - LAN (Default/Unused)
- **Purpose**: Default VLAN (unused per best practice)
- **Status**: Static but no active ports
- **Security**: Blocked on all production ports

#### VLAN 10 - LAB (Homelab Services)
- **Tagged Ports**: 7-10 (WiFi AP, px-net vlans trunk, px-nas SFP+, px-cpu SFP+)
- **Untagged Ports**: 3 (kbs1 - for direct lab access)
- **Purpose**: All homelab VMs and services
- **Network**: 10.10.10.0/24

#### VLAN 40 - USER (User Devices)
- **Tagged Ports**: 7-10 (WiFi AP and trunk ports)
- **Untagged Ports**: 2 (arch workstation)
- **Purpose**: End-user devices (laptops, phones, workstations)
- **Network**: 10.10.40.0/24
- **Multicast**: mDNS enabled for Sonos/Chromecast discovery

#### VLAN 60 - IOT (Internet of Things)
- **Tagged Ports**: 7-10 (WiFi AP and trunk ports)
- **Untagged Ports**: None (all wireless or DHCP)
- **Purpose**: IoT devices (Sonos speakers, smart home devices)
- **Network**: 10.10.60.0/24
- **Security**: Isolated from USER and LAB VLANs
- **Multicast**: mDNS enabled for device discovery

#### VLAN 101 - MGMT (Management)
- **Tagged Ports**: 5-7 (management trunks, WiFi)
- **Untagged Ports**: 1, 4 (Flex Mini, JetKVM)
- **Purpose**: Infrastructure management interfaces
- **Network**: 10.10.101.0/24
- **Security**: Administrative access only

#### VLAN 102 - CARP (High Availability Sync)
- **Tagged Ports**: 5-6 (px-nas and px-cpu management trunks)
- **Untagged Ports**: None
- **Purpose**: OPNsense CARP heartbeat and state synchronization
- **Network**: 10.10.102.0/24
- **Security**: Isolated, no routing to other VLANs

#### VLAN 666 - WAN (External Access)
- **Tagged Ports**: None on main switch
- **Status**: Available on Flex Mini only
- **Purpose**: WAN traffic isolation
- **Security**: Blocked on main switch for security

## IGMP Snooping Configuration

### Global IGMP Snooping Settings

**IPv4 Multicast → IGMP Snooping:**
- **Status**: Enabled ✓
- **Host-Based Timeout**: 260 seconds
- **Purpose**: Optimize multicast traffic forwarding

### IGMP Snooping Status

**Current State:**
- **Query**: Enabled
- **Querier**: Enabled (backup querier if OPNsense doesn't send queries)
- **Report Proxy**: Enabled
- **Host Timeout**: 260 seconds
- **802.1p Priority**: No-Change
- **Unknown Multicast Frame**: Drop (prevents flooding of unknown groups)
- **Reserved Multicast Group**: Flooding ✓ (CRITICAL for mDNS 224.0.0.251)

### IGMP Snooping Per-Port Configuration

| Port | Normal Leave | Fast Leave | IGMP Querier Mode |
|------|--------------|------------|-------------------|
| 1 | ● (enabled) | ○ (disabled) | Auto |
| 2 | ● (enabled) | ○ (disabled) | Auto |
| 3 | ● (enabled) | ○ (disabled) | Auto |
| 4 | ● (enabled) | ○ (disabled) | Auto |
| 5 | ● (enabled) | ○ (disabled) | Auto |
| 6 | ● (enabled) | ○ (disabled) | Auto |
| 7 | ● (enabled) | ○ (disabled) | Auto |
| 8 | ● (enabled) | ○ (disabled) | Auto |
| 9 | ● (enabled) | ○ (disabled) | Auto |
| 10 | ● (enabled) | ○ (disabled) | Auto |

**Configuration Notes:**
- **Normal Leave**: Enabled on all ports (standard IGMP leave processing)
- **Fast Leave**: Disabled (allows querier to verify no other subscribers before removing from group)
- **IGMP Querier Mode**: Auto on all ports (learns from network)

### Critical IGMP Settings for Multicast Discovery

**Reserved Multicast Group: Flooding** ✓
- **Why Required**: mDNS uses 224.0.0.251 (reserved multicast range 224.0.0.0-224.0.0.255)
- **Impact if Dropped**: Complete loss of service discovery (Sonos, Chromecast, Bonjour)
- **Overhead**: Minimal (only link-local multicast traffic)
- **Decision**: Accept flooding for reserved range to enable zero-config protocols

**Unknown Multicast Frame: Drop**
- **Why Used**: Prevents flooding of multicast groups not subscribed via IGMP
- **Impact**: Optimizes bandwidth by only forwarding subscribed multicast
- **Works With**: Reserved multicast flooding (different setting)

## Spanning Tree Configuration

**Status**: Disabled globally
**Reason**: Simple star topology with no redundant links, no risk of loops
**Alternative Protection**: Careful VLAN design and port configuration prevents loops

## Link Aggregation (LACP)

**Current Status**: No active LACP bonds
**Prepared For**: Future expansion with multiple links
**Potential Bonds**:
- px-net management ports could be bonded
- px-nas management ports could be bonded

## Quality of Service (QoS)

**Current Status**: Default priority (0) on all ports
**802.1p Priority**: No-Change for multicast traffic
**Future Consideration**: Priority for voice/video traffic if needed

## Security Features

### Port Security
- **Default VLAN**: VLAN 1 unused (best practice)
- **Native VLAN**: Proper PVID assignment per port
- **VLAN Pruning**: Only necessary VLANs on each port
- **Unused Ports**: Disabled or monitored

### Multicast Security
- **IGMP Snooping**: Prevents multicast flooding to uninterested ports
- **Unknown Multicast**: Dropped (prevents unnecessary forwarding)
- **Reserved Multicast**: Flooded only for discovery protocols (acceptable risk)

### Management Access
- **Management VLAN**: Dedicated VLAN 101
- **SSH Access**: Key-based authentication recommended
- **HTTPS Management**: Web interface on 10.10.101.4
- **SNMP**: Disabled or restricted if enabled

## Performance Monitoring

### Key Metrics to Monitor
- Port utilization and errors
- IGMP snooping group membership
- Multicast traffic rates
- Port speed and duplex negotiation
- VLAN trunk saturation

### Troubleshooting Commands

Via switch CLI or web interface:
```
show vlan all                    # View all VLAN configurations
show igmp snooping status        # Check IGMP snooping state
show igmp snooping groups        # View multicast group memberships
show port statistics             # Check port traffic
show port status                 # Verify link status
```

## Backup and Change Management

### Configuration Backup
- **Frequency**: Before major changes and monthly
- **Location**: Stored in homelab documentation
- **Format**: Full switch configuration file
- **Restoration**: Keep backup accessible for quick recovery

### Change Log
- **Current Config Date**: 2025-10-24 (Sonos cross-VLAN completed)
- **Last Major Change**: IGMP snooping configuration for multicast discovery
- **Documentation**: ADR created for Sonos cross-VLAN solution

## Related Documentation
- [[VLAN Design and Routing Configuration]]
- [[Network Architecture Complete Overview]]
- [[OPNsense Services Configuration]]
- [[ADR: Sonos Cross-VLAN Discovery Solution]]
- [[Multicast and IGMP Snooping Explained]] (educational guide)

## Tags
#switch #zyxel #vlan #igmp-snooping #multicast #network-infrastructure