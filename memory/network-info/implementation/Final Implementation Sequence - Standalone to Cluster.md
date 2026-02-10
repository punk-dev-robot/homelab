---
title: Final Implementation Sequence - Standalone to Cluster
type: note
permalink: network-info/implementation/final-implementation-sequence-standalone-to-cluster
---

# Final Implementation Sequence - Standalone to Cluster

## Overview
Start with standalone px-cpu, verify all networking, then create 2-node cluster BEFORE any service migrations. This ensures cluster infrastructure is solid before moving critical workloads.

## Phase 1: px-cpu Standalone Setup (Day 1)

### Step 1.1: Base Installation
```bash
# Install Proxmox VE on px-cpu
- Hostname: px-cpu
- IP: 10.10.101.14/24
- Gateway: 10.10.101.1
- DNS: 10.10.101.1
```

### Step 1.2: Basic Network Configuration
```bash
# Initial setup - MGMT only
auto eth1
iface eth1 inet manual

auto vmbr101
iface vmbr101 inet static
    address 10.10.101.14/24
    gateway 10.10.101.1
    bridge-ports eth1
    bridge-stp off
    bridge-fd 0
```

### Step 1.3: Verify Basic Connectivity
```bash
# From px-cpu:
ping 10.10.101.1    # Gateway
ping 10.10.101.12   # px-net  
ping 10.10.101.13   # px-nas
ping 8.8.8.8        # Internet via px-net
```

## Phase 2: Complete Network Configuration (Day 1-2)

### Step 2.1: Identify All Interfaces
```bash
# Document actual interface names
ip link show
lspci | grep -i ethernet
lshw -class network -businfo
```

### Step 2.2: Configure All Networks
Apply full configuration from "px-cpu Detailed Network Configuration" document:
- All bridges (vmbr0, vmbr1, vmbr2, vmbr3)
- VLAN awareness
- TSO disabled
- Bond preparation

### Step 2.3: Connect SFP+ and Test
```bash
# Connect SFP+ to Zyxel port 10
# Verify 10Gb link:
ethtool enp3s0f0  # Or actual interface name
ip link show

# Test VLAN connectivity:
# Create test VM with IPs on different VLANs
# Verify can ping devices on each VLAN
```

## Phase 3: px-net Network Reconfiguration (Day 2)

### Step 3.1: Pre-Change Testing
```bash
# Force CARP to px-nas (make it MASTER)
ssh px-net "qm exec 100 -- sysctl net.inet.carp.demotion=100"

# Verify px-nas is handling all traffic
# From client: continuous ping to 8.8.8.8
```

### Step 3.2: Execute Network Change (5-10 min)
```bash
# With px-nas as MASTER, safe to modify px-net:
1. Install SFP+ to RJ45 module
2. Shutdown OPNsense: qm shutdown 100
3. Move cable from port 10 to port 6
4. Start OPNsense: qm start 100
5. Verify comes up as BACKUP
```

### Step 3.3: Test and Stabilize
```bash
# Let run as BACKUP for 30 minutes
# Monitor logs for issues
# Test failover back to px-net
# Re-enable normal CARP operation
```

## Phase 4: Create 2-Node Cluster (Day 2-3)

### Step 4.1: Add Cluster Network VLAN
```bash
# On all three nodes, add VLAN 103:

# px-nas:
auto vmbr2.103
iface vmbr2.103 inet static
    address 10.10.103.13/24

# px-cpu:
auto vmbr2.103
iface vmbr2.103 inet static
    address 10.10.103.14/24

# px-net (for QDevice):
auto vmbr2.103
iface vmbr2.103 inet static
    address 10.10.103.12/24
```

### Step 4.2: Form Cluster
```bash
# On px-nas (first node):
pvecm create compute-cluster \
  --ring0_addr 10.10.103.13 \
  --bindnet0_addr 10.10.103.0/24

# Verify:
pvecm status

# On px-cpu (join cluster):
pvecm join 10.10.103.13 \
  --ring0_addr 10.10.103.14

# Verify both nodes:
pvecm nodes
```

### Step 4.3: Setup QDevice on px-net
```bash
# On px-net:
apt update
apt install corosync-qnetd
systemctl enable --now corosync-qnetd

# On px-nas (setup QDevice):
pvecm qdevice setup 10.10.103.12

# Verify quorum:
pvecm status
# Should show 3 votes (2 nodes + 1 qdevice)
```

### Step 4.4: Test Cluster Operations
```bash
# Create test VM on px-nas
qm create 999 --name test-migrate --memory 512

# Live migrate to px-cpu
qm migrate 999 px-cpu --online

# Migrate back
qm migrate 999 px-nas --online

# Delete test VM
qm destroy 999
```

## Phase 5: Migrate OPNsense Secondary (Day 3)

### Step 5.1: Create OPNsense VM on px-cpu
Now that cluster is working, create secondary OPNsense on px-cpu following "OPNsense Secondary and CARP Migration Details" document.

### Step 5.2: Shutdown Old Secondary
```bash
# On px-nas:
qm shutdown 101  # Old OPNsense secondary
```

### Step 5.3: Configure New Secondary
- Restore configuration
- Update CARP sync peer IPs
- Test failover

## Phase 6: Service Migration Planning (Day 4+)

With cluster operational and OPNsense HA working:
1. Plan which services move to px-cpu
2. Use cluster live migration where possible
3. Schedule migrations during maintenance windows

## Timeline Summary

```
Day 1: 
  Morning: px-cpu Proxmox installation
  Afternoon: Full network configuration
  Evening: Testing all connectivity

Day 2:
  Morning: CARP testing and px-net network change
  Afternoon: Cluster VLAN setup
  Evening: Form 2-node cluster

Day 3:
  Morning: QDevice setup and cluster testing  
  Afternoon: OPNsense secondary migration
  Evening: Full HA testing

Day 4+:
  Service migration planning and execution
```

## Success Criteria Before Each Phase

### Before Network Change:
- [ ] px-cpu fully connected and tested
- [ ] CARP failover tested successfully
- [ ] Switch port 6 configured and tested

### Before Clustering:
- [ ] px-net network change successful
- [ ] All nodes on same Proxmox version
- [ ] Cluster VLAN connectivity verified

### Before OPNsense Migration:
- [ ] Cluster fully operational
- [ ] Live migration tested
- [ ] QDevice providing quorum

### Before Service Migration:
- [ ] OPNsense HA fully functional
- [ ] Cluster stable for 24 hours
- [ ] Backup strategy defined

## Emergency Rollback Options

At each phase, we can rollback:
1. **Network change**: Move cable back, restore SFP+
2. **Cluster**: `pvecm expected 1` to break cluster
3. **OPNsense**: Start old VM on px-nas
4. **Services**: Migrate back or restore from backup