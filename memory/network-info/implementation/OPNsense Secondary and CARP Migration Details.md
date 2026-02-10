---
title: OPNsense Secondary and CARP Migration Details
type: note
permalink: network-info/implementation/opnsense-secondary-and-carp-migration-details
---

# OPNsense Secondary and CARP Migration Details

## Overview
Moving the secondary OPNsense from px-nas to px-cpu requires careful handling of CARP interfaces and synchronization settings to maintain high availability.

## Current CARP Configuration

### On px-net (Primary - MASTER)
- CARP VIP 10.10.10.1 (VLAN 10) - VHID 10
- CARP VIP 10.10.40.1 (VLAN 40) - VHID 40  
- CARP VIP 10.10.60.1 (VLAN 60) - VHID 60
- CARP VIP 10.10.101.1 (VLAN 101) - VHID 101
- Synchronization: Via VLAN 102 to px-nas

### On px-nas (Secondary - BACKUP)
- Same CARP VIPs configured
- Base priority: 2 (lower than px-net)
- Synchronization: Via VLAN 102 from px-net

## Migration Process

### Phase 1: Prepare px-cpu OPNsense VM

```bash
# Create VM with EXACT same specs as px-nas instance
qm create 101 --name opnsense-secondary \
  --memory 4096 --cores 4 --numa 0 --sockets 1 \
  --cpu host --ostype other

# Add storage (match size from px-nas)
qm set 101 --virtio0 local-zfs:32,cache=writeback,discard=on

# Add network interfaces IN EXACT ORDER
qm set 101 --net0 virtio,bridge=vmbr0,tag=0  # VLAN trunk
qm set 101 --net1 virtio,bridge=vmbr1        # WAN  
qm set 101 --net2 virtio,bridge=vmbr2,tag=0  # MGMT/SYNC

# Set boot order
qm set 101 --boot order=virtio0
```

### Phase 2: Export Configuration from px-nas

```bash
# On px-nas OPNsense (via web UI or console):
1. System -> Configuration -> Backups
2. Download configuration backup
3. Note down:
   - Interface assignments
   - CARP passwords (if set)
   - Sync interface IP (VLAN 102)
```

### Phase 3: Shutdown px-nas Secondary

```bash
# IMPORTANT: Verify px-net is MASTER first!
# On px-net OPNsense:
ifconfig | grep -A2 carp
# Should show MASTER for all CARP interfaces

# Safe to proceed - shutdown px-nas OPNsense:
qm shutdown 101  # on px-nas
```

### Phase 4: Configure px-cpu OPNsense

```bash
# Install OPNsense on px-cpu VM
qm start 101
# Follow installation, then:

1. Initial interface assignment:
   vtnet0 -> LAN (VLAN trunk)
   vtnet1 -> WAN
   vtnet2 -> SYNC

2. Set temporary LAN IP: 10.10.10.50/24

3. Access web UI and restore backup

4. Critical: Update sync interface IP
   - Old: 10.10.102.13 (px-nas)
   - New: 10.10.102.14 (px-cpu)
```

### Phase 5: Update CARP Configuration

#### On px-cpu OPNsense:
```
1. Interfaces -> Virtual IPs -> Settings
   - Verify all CARP VIPs present
   - Verify Base priority = 2
   - Verify VHID matches primary

2. System -> High Availability -> Settings
   - Synchronize Config to IP: 10.10.102.12 (px-net)
   - Sync interface: SYNC (vtnet2)
   
3. Firewall -> Rules -> SYNC
   - Allow all from 10.10.102.12 (px-net)
```

#### On px-net OPNsense (Primary):
```
1. System -> High Availability -> Settings
   - Change sync peer from 10.10.102.13 to 10.10.102.14
   
2. Firewall -> Rules -> SYNC  
   - Update rule to allow from 10.10.102.14 (px-cpu)
   - Remove old rule for .13
```

### Phase 6: Enable and Test CARP

```bash
# On px-cpu OPNsense:
1. Enable CARP interfaces
2. Check status - should show BACKUP
3. Monitor logs for sync messages

# Test failover:
# On px-net (primary):
sysctl net.inet.carp.demotion=100

# Verify px-cpu becomes MASTER
# Check all services accessible
# Restore px-net:
sysctl net.inet.carp.demotion=0
```

## IP Address Changes Summary

### Before Migration:
- px-net OPNsense: 10.10.102.12 (VLAN 102)
- px-nas OPNsense: 10.10.102.13 (VLAN 102)
- CARP sync: .12 ←→ .13

### After Migration:
- px-net OPNsense: 10.10.102.12 (VLAN 102) [NO CHANGE]
- px-cpu OPNsense: 10.10.102.14 (VLAN 102) [NEW]
- CARP sync: .12 ←→ .14

## Verification Checklist

- [ ] All CARP VIPs present on both nodes
- [ ] CARP status shows MASTER/BACKUP correctly
- [ ] Configuration sync working (.12 → .14)
- [ ] Failover works in both directions
- [ ] Firewall states synchronized
- [ ] DHCP leases synchronized
- [ ] No IP conflicts on VLAN 102

## Rollback Plan

If issues occur:
1. Shutdown px-cpu OPNsense
2. Start px-nas OPNsense (still has config)
3. Update px-net sync peer back to .13
4. Investigate issues offline

## Common Issues and Solutions

### CARP Not Syncing
- Check firewall rules on SYNC interface
- Verify VLAN 102 connectivity between nodes
- Check CARP passwords match

### Split Brain (Both MASTER)
- Check network connectivity on VLAN 102
- Verify VHID unique per CARP VIP
- Check for duplicate IP addresses

### Configuration Not Syncing
- Verify sync interface IPs correct
- Check firewall allows sync traffic
- Verify admin password same on both