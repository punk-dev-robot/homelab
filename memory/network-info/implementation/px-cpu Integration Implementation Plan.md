---
title: px-cpu Integration Implementation Plan
type: note
permalink: network-info/implementation/px-cpu-integration-implementation-plan
---

# px-cpu Integration Implementation Plan

## Overview
This plan details the step-by-step process to integrate px-cpu into the homelab infrastructure while maintaining zero downtime for internet access and critical services.

## Network Topology Changes

### Final Physical Connections
```
Zyxel XMG-1920 Switch:
┌─────────────────────────────────────────────────────────┐
│ Port │ Device    │ Interface    │ Purpose      │ Speed   │
├─────────────────────────────────────────────────────────┤
│  1   │ Flex Mini │ Port 1       │ PoE/MGMT     │ 2.5Gb   │
│  2   │ -         │ -            │ MGMT access  │ 2.5Gb   │
│  3   │ px-net    │ enp3s0       │ MGMT (LACP)  │ 2.5Gb   │
│  4   │ px-nas    │ enp91s0      │ MGMT (LACP)  │ 2.5Gb   │
│  5   │ px-cpu    │ eth1         │ MGMT         │ 2.5Gb   │
│  6   │ px-net    │ enp1s0f0*    │ VLAN trunk   │ 2.5Gb   │
│  7   │ QNAP      │ -            │ Storage      │ 2.5Gb   │
│  8   │ WiFi AP   │ -            │ Trunk        │ 2.5Gb   │
│  9   │ px-nas    │ enp3s0f0np0  │ VLAN trunk   │ 10Gb    │
│  10  │ px-cpu    │ SFP+         │ VLAN trunk   │ 10Gb    │
└─────────────────────────────────────────────────────────┘
* via SFP+ to RJ45 module
```

## Prerequisites Checklist

### Hardware Required
- [ ] SFP+ to RJ45 module (2.5Gb capable) for px-net
- [ ] SFP+ optical module for px-cpu 
- [ ] SFP+ DAC cable or fiber for px-cpu to Zyxel port 10
- [ ] Ethernet cable for px-cpu eth1 to Zyxel port 5
- [ ] Ethernet cable for px-net SFP+/RJ45 to Zyxel port 6

### Software Required
- [ ] Proxmox VE ISO (same version as px-net/px-nas)
- [ ] OPNsense configuration backup from px-nas
- [ ] Network configuration templates

### Pre-Implementation Tasks
- [ ] Verify current Proxmox versions match
- [ ] Document current VMID assignments
- [ ] Backup all critical configurations
- [ ] Schedule maintenance windows

## Implementation Phases

### Phase 1: px-cpu Base Installation (No Downtime)

#### Step 1.1: Install Proxmox VE
```bash
# Installation parameters:
Hostname: px-cpu
IP Address: 10.10.101.14
Netmask: 255.255.255.0
Gateway: 10.10.101.1
DNS: 10.10.101.1
```

#### Step 1.2: Initial Network Configuration
Create `/etc/network/interfaces`:
```bash
auto lo
iface lo inet loopback

# Physical interfaces
auto eth1
iface eth1 inet manual

auto eth2  
iface eth2 inet manual

# SFP+ interfaces (naming TBD after boot)
auto enpXs0f0
iface enpXs0f0 inet manual

auto enpXs0f1
iface enpXs0f1 inet manual

# Management network
auto vmbr101
iface vmbr101 inet static
    address 10.10.101.14/24
    gateway 10.10.101.1
    bridge-ports eth1
    bridge-stp off
    bridge-fd 0

# VLAN trunk bridge (SFP+)
auto vmbr0
iface vmbr0 inet manual
    bridge-ports enpXs0f0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094
```

#### Step 1.3: Connect px-cpu to Network
1. Connect eth1 to Zyxel port 5
2. Connect SFP+ to Zyxel port 10
3. Verify connectivity: `ping 10.10.101.1`

### Phase 2: Zyxel Switch Configuration (5 min downtime for px-net)

#### Step 2.1: Configure Port 6 for px-net VLAN Trunk
```
interface port-channel 6
  name "px-net vlan trunk"
  pvid 101
  frame-type tagged
  vlan-trunking
exit
```

#### Step 2.2: Update VLAN Assignments
```
vlan 10
  fixed 6,8-10
exit

vlan 40  
  fixed 2,6,8-10
exit

vlan 60
  fixed 6,8-10
exit

vlan 101
  fixed 1-8
exit

vlan 102
  fixed 3-6,8
exit
```

### Phase 3: px-net Network Reconfiguration (5-10 min downtime)

#### Step 3.1: Preparation on px-net
1. SSH to px-net
2. Backup current network config: `cp /etc/network/interfaces /etc/network/interfaces.backup`
3. Install SFP+ to RJ45 module in enp1s0f0

#### Step 3.2: Execute Network Change
```bash
# Quick execution to minimize downtime
1. Shutdown OPNsense VM: qm shutdown 100
2. Move cable from Zyxel port 10 to port 6
3. Start OPNsense VM: qm start 100
4. Verify connectivity
```

### Phase 4: Proxmox Cluster Configuration

#### Option A: 2-Node Cluster (Recommended)
```bash
# On px-nas:
pvecm create homelab-compute

# On px-cpu:
pvecm join 10.10.101.13

# On px-net (QDevice for quorum):
apt install corosync-qdevice
# Configure as arbitrator
```

#### Option B: 3-Node Cluster
```bash
# On px-net:
pvecm create homelab-cluster

# On px-nas:
pvecm join 10.10.101.12

# On px-cpu:
pvecm join 10.10.101.12
```

### Phase 5: OPNsense Secondary Migration

#### Step 5.1: Prepare New OPNsense VM on px-cpu
```bash
# Create VM with same specifications
qm create 101 --name opn2 --memory 4096 --cores 4 --numa 0 --sockets 1
qm set 101 --virtio0 local-zfs:32 --boot c --bootdisk virtio0
qm set 101 --net0 virtio,bridge=vmbr0 --net1 virtio,bridge=vmbr1 --net2 virtio,bridge=vmbr2
```

#### Step 5.2: Migration Process
1. Backup config from px-nas OPNsense
2. Shutdown secondary on px-nas: `qm shutdown 101`
3. Restore config to px-cpu OPNsense
4. Start new secondary: `qm start 101`
5. Verify CARP synchronization

#### Step 5.3: Test Failover
```bash
# On primary OPNsense:
ifconfig carpX down  # Force failover
# Verify secondary takes over
ifconfig carpX up    # Restore primary
```

## Rollback Procedures

### Network Change Rollback (px-net)
```bash
1. qm shutdown 100
2. Move cable back to port 10
3. Replace RJ45 module with optical SFP+
4. qm start 100
```

### Cluster Rollback
```bash
# Remove node from cluster
pvecm delnode px-cpu
```

## Verification Tests

### After Each Phase
- [ ] All nodes pingable on management network
- [ ] Proxmox web UI accessible on all nodes
- [ ] Internet connectivity maintained
- [ ] OPNsense CARP status healthy
- [ ] No service interruptions reported

### Final System Tests
- [ ] CARP failover works both directions
- [ ] VMs can migrate between clustered nodes
- [ ] 10Gb connectivity verified between px-nas and px-cpu
- [ ] All existing services remain accessible

## Maintenance Windows Required

1. **Phase 2-3**: 10-15 minutes total
   - Switch reconfiguration: 5 min
   - px-net network change: 5-10 min
   
2. **Phase 5**: 10-15 minutes
   - OPNsense migration and testing

## Next Steps After Integration

1. **Service Migration Planning**
   - Identify services to move from apps-vm to px-cpu
   - Plan migration schedule
   
2. **Performance Optimization**
   - Tune network settings for 10Gb
   - Optimize VM placement
   
3. **High Availability Enhancement**
   - Configure automated failover policies
   - Implement monitoring and alerting