---
title: px-cpu Integration Implementation Plan
type: note
permalink: guides/px-cpu-integration-implementation-plan
---

# px-cpu Integration Implementation Plan

## Overview
This plan details the step-by-step process to integrate px-cpu (Intel i9 13th gen, 24 cores, 96GB RAM) into the homelab infrastructure while maintaining minimal downtime for internet access and critical services.

## Network Topology Changes

### Final Physical Connections
```
Zyxel XMG-1920 Switch Port Assignments:
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
* via SFP+ to RJ45 module (2.5Gb)
```

## Prerequisites Checklist

### Hardware Required
- [ ] SFP+ to RJ45 module (2.5Gb capable) for px-net
- [ ] SFP+ optical module for px-cpu
- [ ] SFP+ DAC cable or fiber for px-cpu to Zyxel port 10
- [ ] Ethernet cable for px-cpu eth1 to Zyxel port 5
- [ ] Ethernet cable for px-net SFP+/RJ45 to Zyxel port 6

### Software Required
- [ ] Proxmox VE ISO (matching version with px-net/px-nas)
- [ ] OPNsense configuration backup from px-nas
- [ ] Network configuration templates
- [ ] VM migration scripts

### Pre-Implementation Tasks
- [ ] Verify current Proxmox versions match
- [ ] Document current VMID assignments
- [ ] Backup all critical configurations
- [ ] Schedule maintenance windows
- [ ] Test SFP+ to RJ45 module functionality

## Implementation Phases

### Phase 1: px-cpu Base Installation (Zero Downtime)

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
    post-up ethtool -K vmbr0 tso off gso off
```

#### Step 1.3: Connect px-cpu to Network
1. Connect eth1 to Zyxel port 5
2. Connect SFP+ to Zyxel port 10
3. Verify connectivity: `ping 10.10.101.1`
4. Access Proxmox UI: `https://10.10.101.14:8006`

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
  forbidden 1-5,7
exit

vlan 40  
  fixed 2,6,8-10
  forbidden 1,3-5,7
exit

vlan 60
  fixed 6,8-10
  forbidden 1-5,7
exit

vlan 101
  fixed 1-10
  untagged 1-2,5-6,9-10
exit

vlan 102
  fixed 3-6,8
exit
```

#### Step 2.3: Save Configuration
```
write memory
```

### Phase 3: px-net Network Reconfiguration (5-10 min downtime)

#### Step 3.1: Install SFP+ to RJ45 Module
1. Power down px-net gracefully
2. Install SFP+ to RJ45 module in enp1s0f0
3. Connect to Zyxel port 6 with ethernet cable
4. Power on px-net

#### Step 3.2: Update px-net Network Configuration
Edit `/etc/network/interfaces`:
```bash
# Change vmbr0 from SFP+ (10Gb) to SFP+/RJ45 (2.5Gb)
auto vmbr0
iface vmbr0 inet manual
    bridge-ports enp1s0f0  # Now using SFP+ with RJ45 module
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094
    post-up ethtool -K vmbr0 tso off gso off
    # Note: Speed reduced from 10Gb to 2.5Gb
```

#### Step 3.3: Restart Networking
```bash
systemctl restart networking
# Verify: ip a | grep vmbr0
```

### Phase 4: OPNsense Migration (30 min downtime)

#### Step 4.1: Export OPN2 from px-nas
1. Shut down OPN2 VM on px-nas
2. Export VM configuration and disk:
```bash
# On px-nas
qm shutdown 102
vzdump 102 --storage local --compress gzip
```

#### Step 4.2: Import OPN2 to px-cpu
```bash
# Copy backup to px-cpu
scp /var/lib/vz/dump/vzdump-qemu-102-*.vma.gz root@10.10.101.14:/var/lib/vz/dump/

# On px-cpu
qmrestore /var/lib/vz/dump/vzdump-qemu-102-*.vma.gz 102
```

#### Step 4.3: Update OPN2 Network Configuration
```bash
# Modify VM config to use px-cpu bridges
qm set 102 -net0 virtio,bridge=vmbr0,tag=10
qm set 102 -net1 virtio,bridge=vmbr1
```

#### Step 4.4: Start OPN2 on px-cpu
```bash
qm start 102
# Verify CARP status in OPNsense UI
```

### Phase 5: VM Migration (Per VM: 10-30 min downtime)

#### Step 5.1: Migration Order
1. obs-vm (least critical)
2. media-vm (moderate impact)
3. apps-vm (if performance benefits justify)

#### Step 5.2: Live Migration Process
```bash
# For each VM on px-nas to migrate:
qm migrate <VMID> px-cpu --online --with-local-disks
```

#### Step 5.3: Post-Migration Verification
- Check VM network connectivity
- Verify service accessibility
- Monitor performance metrics

### Phase 6: Proxmox Clustering (Optional - 1 hour downtime)

#### Step 6.1: Create Cluster on px-net
```bash
pvecm create homelab-cluster
```

#### Step 6.2: Join px-nas to Cluster
```bash
# On px-nas
pvecm add 10.10.101.12
```

#### Step 6.3: Join px-cpu to Cluster
```bash
# On px-cpu
pvecm add 10.10.101.12
```

#### Step 6.4: Configure Cluster Network
- Set up Corosync rings
- Configure migration network
- Set up HA resources

## Rollback Procedures

### Phase 3 Rollback (px-net)
1. Power down px-net
2. Remove SFP+ to RJ45 module
3. Reconnect original SFP+ cable to port 10
4. Power on and verify

### Phase 4 Rollback (OPNsense)
1. Shut down OPN2 on px-cpu
2. Start OPN2 on px-nas
3. Verify CARP failback

### Phase 5 Rollback (VM Migration)
1. Shut down VM on px-cpu
2. Migrate back to original host
3. Verify services

## Testing Procedures

### Network Connectivity Tests
```bash
# From px-cpu
ping 10.10.101.1    # Gateway
ping 10.10.101.12   # px-net
ping 10.10.101.13   # px-nas
ping 10.10.10.11    # apps-vm
ping 8.8.8.8        # Internet
```

### Service Availability Tests
- Access each VM's web interface
- Test inter-VM communication
- Verify external access through gateway
- Test CARP failover

### Performance Tests
- iperf3 between nodes
- Storage throughput tests
- VM migration speed tests

## Success Criteria

1. All three Proxmox nodes accessible
2. Internet connectivity maintained
3. CARP failover functional
4. All VMs accessible
5. Inter-VM communication at expected speeds
6. No packet loss during normal operations

## Risk Mitigation

### Critical Risks
1. **SFP+ Module Incompatibility**
   - Mitigation: Test module before implementation
   - Fallback: Use original configuration

2. **Network Loop Creation**
   - Mitigation: Verify STP disabled on all bridges
   - Fallback: Disconnect redundant links

3. **VMID Conflicts**
   - Mitigation: Document all VMIDs before starting
   - Fallback: Renumber VMs as needed

### Contingency Plans
- Keep original network cables accessible
- Document all configuration changes
- Take screenshots of working configurations
- Have console access ready (KVM/IPMI)

## Post-Implementation Tasks

1. Update documentation
2. Configure monitoring for px-cpu
3. Set up backup schedules
4. Performance baseline testing
5. Update network diagrams
6. Configure alerting rules

## Related Documentation
- [[Network Architecture Complete Overview]]
- [[VLAN Design and Routing Configuration]]
- [[High Availability Configuration]]
- [[Proxmox Clustering Network Design]]

Tags: #implementation #px-cpu #proxmox #networking #migration #planning