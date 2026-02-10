---
title: Linux Bonding MAC Address Management and fail_over_mac Option
type: note
permalink: research/linux-bonding-mac-address-management-and-fail-over-mac-option
---

# Linux Bonding MAC Address Management and fail_over_mac Option

## Executive Summary

**The Problem**: You cannot have bond0 with an independent MAC while slave interfaces keep their original permanent MACs in active-backup mode with default settings.

**The Solution**: Use `FailOverMACPolicy=active` (fail_over_mac=1) in systemd-networkd, which allows slaves to keep their permanent MACs while the bond dynamically adopts the active slave's MAC.

## Current Situation

Based on current configuration analysis:

```
Configuration:
- bond0.netdev: MACAddress=ea:dc:4f:6b:66:02 (manually set)
- fail_over_mac: none (default mode 0)

Permanent MACs:
- lan0:  6c:1f:f7:21:c3:48
- wlan0: 7c:e7:12:81:27:e3

Current Runtime MACs:
- lan0:  7c:e7:12:81:27:e3 (overridden!)
- wlan0: 7c:e7:12:81:27:e3
- bond0: 7c:e7:12:81:27:e3
```

**Problem**: All three interfaces share wlan0's MAC because `fail_over_mac=none` (default) forces all slaves to adopt the bond's MAC address. The manually configured MAC (ea:dc:4f:6b:66:02) in the .netdev file is being ignored because systemd-networkd's behavior conflicts with the bonding driver's default MAC handling.

## Understanding fail_over_mac Option

The `fail_over_mac` kernel bonding parameter controls MAC address management in active-backup mode. It has three modes:

### Mode 0: none (DEFAULT - Current Behavior)

**Behavior**:
- Bond's MAC is set at creation (either manually or from first slave)
- ALL slave interfaces are forced to use the bond's MAC address
- MAC remains constant even during failover

**Configuration**:
```ini
[Bond]
FailOverMACPolicy=none
```

**Result**: What you're experiencing now - all interfaces share the same MAC.

### Mode 1: active (RECOMMENDED SOLUTION)

**Behavior**:
- Bond's MAC dynamically changes to match the currently active slave
- Slaves KEEP their original permanent MAC addresses
- When failover occurs, bond adopts the new active slave's MAC
- Gratuitous ARP sent on failover to notify network of MAC change

**Configuration**:
```ini
[Bond]
FailOverMACPolicy=active
```

**Result**: 
- lan0 keeps: 6c:1f:f7:21:c3:48 (permanent)
- wlan0 keeps: 7c:e7:12:81:27:e3 (permanent)
- bond0 uses: 6c:1f:f7:21:c3:48 when lan0 is active
- bond0 uses: 7c:e7:12:81:27:e3 when wlan0 is active

**Advantages**:
- Slaves retain original MACs (solves your problem!)
- Works with devices that can't change MAC
- Avoids confusion for devices with firmware MAC restrictions

**Disadvantages**:
- Bond MAC changes during failover
- Requires gratuitous ARP (can be unreliable if packets lost)
- Network must support MAC address changes

### Mode 2: follow

**Behavior**:
- Bond's MAC selected normally (typically first slave's MAC)
- Only the ACTIVE slave is set to bond's MAC
- Backup slaves keep their original MACs
- During failover: new active slave gets bond's MAC, old active slave gets new slave's original MAC

**Configuration**:
```ini
[Bond]
FailOverMACPolicy=follow
```

**Result**:
- If lan0 is active:
  - lan0: uses bond's MAC
  - wlan0: keeps 7c:e7:12:81:27:e3
  - bond0: uses bond's MAC
- On failover to wlan0:
  - lan0: gets wlan0's original MAC (7c:e7:12:81:27:e3)
  - wlan0: uses bond's MAC
  - bond0: keeps bond's MAC

**Use case**: Multiport devices that have performance issues when multiple ports share the same MAC.

## Why Slaves Currently Share Bond's MAC

With `fail_over_mac=none` (default), the Linux bonding driver enforces this behavior by design:

1. Bond interface is created with a MAC (either manually set or inherited from first slave)
2. When slaves are enslaved, bonding driver overwrites their MAC to match bond's MAC
3. This ensures consistent MAC addressing across the bond
4. Prevents network confusion since only one interface is active at a time

From kernel documentation:
> "bonding will set all slaves of an active-backup bond to the same MAC address at enslavement time"

## systemd-networkd Configuration

### Current Configuration
File: `/etc/systemd/network/30-bond0.netdev`
```ini
[NetDev]
Name=bond0
Kind=bond
MACAddressPolicy=none
MACAddress=ea:dc:4f:6b:66:02  # This is being overridden

[Bond]
Mode=active-backup
PrimaryReselectPolicy=always
MIIMonitorSec=1s
# Missing: FailOverMACPolicy
```

### Recommended Configuration (Option 1: Dynamic Bond MAC)

If you want slaves to keep their permanent MACs and bond to follow the active slave:

```ini
[NetDev]
Name=bond0
Kind=bond
# Remove MACAddress - let bond adopt active slave's MAC

[Bond]
Mode=active-backup
PrimaryReselectPolicy=always
MIIMonitorSec=1s
FailOverMACPolicy=active  # KEY CHANGE
```

**Result**:
- lan0: 6c:1f:f7:21:c3:48 (always)
- wlan0: 7c:e7:12:81:27:e3 (always)
- bond0: 6c:1f:f7:21:c3:48 (when lan0 active) or 7c:e7:12:81:27:e3 (when wlan0 active)

### Alternative Configuration (Option 2: Fixed Bond MAC with Follow)

If you want bond to have a fixed MAC but only active slave matches it:

```ini
[NetDev]
Name=bond0
Kind=bond
MACAddress=ea:dc:4f:6b:66:02  # Keep your custom MAC

[Bond]
Mode=active-backup
PrimaryReselectPolicy=always
MIIMonitorSec=1s
FailOverMACPolicy=follow  # Different approach
```

**Result**:
- bond0: ea:dc:4f:6b:66:02 (always)
- lan0: ea:dc:4f:6b:66:02 (when active) or 7c:e7:12:81:27:e3 (when backup)
- wlan0: ea:dc:4f:6b:66:02 (when active) or 7c:e7:12:81:27:e3 (when backup)

**Note**: This still changes slave MACs, just less frequently.

## Answer to Your Specific Question

> Can bond have independent MAC in active-backup mode?

**No, not in the way you want.** Here's why:

1. **With fail_over_mac=none (default)**: Bond can have independent MAC, but ALL slaves are forced to use it
2. **With fail_over_mac=active**: Slaves keep their MACs, but bond CANNOT have independent MAC - it must use active slave's MAC
3. **With fail_over_mac=follow**: Bond can have independent MAC, but ACTIVE slave is forced to use it (backup slaves keep theirs)

**The fundamental limitation**: In active-backup bonding, the bond interface and the currently active slave interface must share the same MAC address for proper network operation. This is by design - the bond IS the active slave from a network perspective.

## Why This Limitation Exists

Active-backup bonding works by having one slave "represent" the bond at any given time. The network sees traffic from the bond's MAC, which must be the active slave's MAC for the networking stack to function correctly:

1. **Incoming packets**: Arrive addressed to the bond's MAC, must be receivable by active slave
2. **Outgoing packets**: Sent from active slave, must have bond's source MAC
3. **ARP/NDP**: Network learns bond's MAC from active slave's traffic

If bond had a truly independent MAC separate from all slaves, the active slave couldn't receive packets addressed to the bond, breaking connectivity.

## Recommended Solution

For your use case (slaves keeping permanent MACs), use **FailOverMACPolicy=active**:

### Advantages
✅ Slaves keep their permanent MAC addresses (solves your requirement)
✅ Simple configuration
✅ Works with MAC-restricted hardware
✅ No manual MAC management needed

### Disadvantages
❌ Bond MAC changes during failover (not truly independent)
❌ Relies on gratuitous ARP for network notification
❌ May cause brief connectivity disruption during failover

### Configuration Change Required

```ini
# /etc/systemd/network/30-bond0.netdev
[NetDev]
Name=bond0
Kind=bond
# Remove: MACAddress=ea:dc:4f:6b:66:02
# Remove: MACAddressPolicy=none

[Bond]
Mode=active-backup
PrimaryReselectPolicy=always
MIIMonitorSec=1s
FailOverMACPolicy=active  # Add this
```

### Verification After Change

```bash
# Restart networking
sudo networkctl reload
sudo networkctl reconfigure bond0

# Check fail_over_mac setting
cat /sys/class/net/bond0/bonding/fail_over_mac
# Should show: active 1

# Verify MAC addresses
ethtool -P lan0  # Should show: 6c:1f:f7:21:c3:48
ethtool -P wlan0 # Should show: 7c:e7:12:81:27:e3
ip link show lan0 wlan0 bond0 | grep "link/ether"
# lan0 should show: 6c:1f:f7:21:c3:48
# wlan0 should show: 7c:e7:12:81:27:e3
# bond0 should show: 6c:1f:f7:21:c3:48 (matches active slave lan0)
```

## References

- **Kernel Documentation**: https://www.kernel.org/doc/Documentation/networking/bonding.txt
- **systemd.netdev man page**: `man systemd.netdev` (search for FailOverMACPolicy)
- **GitHub Issue**: https://github.com/systemd/systemd/issues/3375 (networkd bond MAC behavior)
- **Stack Overflow**: https://askubuntu.com/questions/1546344/ (bonding options in systemd-networkd)

## Related Memory Links

- [[architecture/network-architecture-overview]] - Overall network design
- [[patterns/systemd-networkd-patterns]] - systemd-networkd configuration patterns
- [[decisions/adr-network-bonding-decision]] - Why we use bonding

## Tags

#networking #bonding #systemd-networkd #mac-address #active-backup #fail-over-mac #linux-kernel
