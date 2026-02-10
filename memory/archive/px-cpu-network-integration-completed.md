---
title: px-cpu Network Integration Completed
type: note
permalink: decisions/px-cpu-network-integration-completed
---

# px-cpu Network Integration Completed

## Success Summary
**Date**: 2025-09-20  
**Status**: ✅ COMPLETED  
**Outcome**: px-cpu successfully integrated into homelab network with standardized configuration

## Final Network Configuration

### px-cpu Interface Mapping
- `enp89s0` → bond0 → vmbr2 → MGMT/SYNC (connected to Zyxel port 5)
- `enp87s0` → vmbr1 → WAN (disconnected, ready for future use)
- `enp2s0f0np0` → vmbr0 → VLAN Trunk (SFP+ 10Gb, connected to Zyxel port 10)
- `enp2s0f1np1` → vmbr3 → Unused SFP+ (available for future expansion)

### Bridge Configuration
```
vmbr0: VLAN trunk bridge (SFP+ 10Gb) - matches px-net/px-nas
vmbr1: WAN bridge (ready for future WAN connection)
vmbr2: MGMT/SYNC bridge with bond0
vmbr3: Unused SFP+ bridge (future expansion)
vmbr2.101: Management IP 10.10.101.11/24
```

### Network Connectivity
- **Management IP**: 10.10.101.11 (on VLAN 101)
- **Gateway**: 10.10.101.1
- **SSH Access**: Working ✅
- **Connectivity to px-net**: Working ✅ (10.10.101.12)
- **Connectivity to px-nas**: Working ✅ (10.10.101.13)

## Template Configuration Success

### Standardization Achieved
- **Same bridge numbering** as px-net/px-nas
- **Same VLAN configuration** pattern
- **Same bond setup** (ready for LACP)
- **Same IP addressing** scheme

### Physical Connections
- **Port 5**: MGMT connection (2.5Gb ethernet)
- **Port 10**: VLAN trunk (10Gb SFP+)
- **Both ports configured** on Zyxel switch

## Configuration Files

### Final /etc/network/interfaces
```bash
auto lo
iface lo inet loopback

# Physical interfaces
auto enp87s0
iface enp87s0 inet manual

auto enp89s0
iface enp89s0 inet manual

auto enp2s0f0np0
iface enp2s0f0np0 inet manual

auto enp2s0f1np1
iface enp2s0f1np1 inet manual

iface wlp90s0 inet manual

# Bond0 for MGMT
auto bond0
iface bond0 inet manual
    bond-slaves enp89s0
    bond-miimon 100
    bond-mode 802.3ad
    bond-xmit-hash-policy layer2+3

# Bridge configurations
auto vmbr0
iface vmbr0 inet manual
    bridge-ports enp2s0f0np0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094

auto vmbr1
iface vmbr1 inet manual
    bridge-ports enp87s0
    bridge-stp off
    bridge-fd 0

auto vmbr2
iface vmbr2 inet manual
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094

auto vmbr3
iface vmbr3 inet manual
    bridge-ports enp2s0f1np1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094

# Management IP
auto vmbr2.101
iface vmbr2.101 inet static
    address 10.10.101.11/24
    gateway 10.10.101.1
    dns-nameservers 10.10.101.1

source /etc/network/interfaces.d/*
```

## Next Steps Enabled

### Ready for VM Deployment
- All VLANs properly configured
- Bridge structure ready for VMs
- Network performance optimized

### Ready for Service Migration
- obs-vm (monitoring) - lowest risk
- media-vm (if storage proximity beneficial)
- apps-vm (if compute power needed)

### Ready for Clustering (Optional)
- Network configuration standardized
- Management interfaces consistent
- Future clustering preparation complete

## Lessons Learned

### Template-First Approach Success
- Using fresh px-cpu as template worked perfectly
- KVM access eliminated risk during network changes
- Configuration matches proven px-net/px-nas pattern

### Interface Naming Consistency
- Each Proxmox node has different interface names
- Physical port mapping documented for each node
- Bond configuration ensures consistency regardless

### Zyxel Switch Integration
- Port 5 configured for px-cpu MGMT
- Port 10 configured for px-cpu VLAN trunk
- No disruption to existing px-net/px-nas connectivity

## Related Documentation
- [[Network Architecture Complete Overview]]
- [[VLAN Design and Routing Configuration]]
- [[Service Distribution Architecture]]

Tags: #px-cpu #network #integration #completed #proxmox #template