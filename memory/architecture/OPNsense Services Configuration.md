---
title: OPNsense Services Configuration
type: note
permalink: architecture/opnsense-services-configuration
---

# OPNsense Services Configuration

## Overview

This document details the configuration of key OPNsense services for cross-VLAN communication, multicast support, and high availability.

**Primary OPNsense**: px-net (10.10.101.12) - opnsense1  
**Secondary OPNsense**: px-nas (10.10.101.13) - opnsense2  
**Management**: Web interface via CARP VIP 10.10.101.1

## mDNS Repeater Configuration

### Overview
mDNS Repeater enables service discovery across VLANs by relaying multicast DNS packets (224.0.0.251:5353) between isolated broadcast domains.

**Service**: `/usr/local/bin/mdns-repeater`  
**Status**: Enabled ✓  
**CARP Failover**: Enabled (runs on MASTER node only) ✓

### Configuration

**Interfaces**:
- `vlan0.40` (USER VLAN)
- `vlan0.60` (IOT VLAN)

**Settings**:
```
Service: Enabled
Interface Selection: vlan0.40, vlan0.60
Enable CARP Failover: Yes
```

### How It Works

1. **Listens** on both configured interfaces (vlan0.40 and vlan0.60)
2. **Receives** mDNS packet on one interface
3. **Copies** packet and retransmits to all other configured interfaces
4. **Bidirectional**: Works in both directions (USER→IOT and IOT→USER)

### Process Verification

Check mDNS repeater is running:
```bash
ps aux | grep mdns
# Expected output:
# root  52914  0.0  0.0  13660  2192  -  Ss  18:49  0:00.00 /usr/local/bin/mdns-repeater -p /var/run/mdns
```

Check listening sockets:
```bash
sockstat -4 | grep 5353
# Expected output:
# root  mdns-repea  52914  3  udp4  *:5353               *:*
# root  mdns-repea  52914  4  udp4  10.10.60.2:5353      *:*
# root  mdns-repea  52914  6  udp4  10.10.40.2:5353      *:*
```

### Use Cases

**Enabled For**:
- Sonos speaker discovery (Spotify Connect works perfectly)
- Chromecast discovery
- AirPlay device discovery
- Any Bonjour/mDNS service across VLANs

**Known Limitations**:
- Source IP rewrite: Responses show OPNsense interface IP instead of actual device IP
- Some strict apps (Sonos app) reject responses due to source mismatch
- Workaround: Use protocols like Spotify Connect that are less strict on validation

### Failover Behavior

**CARP Failover Enabled**:
- Service runs ONLY on MASTER node (opnsense1 normally)
- When failover occurs, service automatically starts on new MASTER
- No manual intervention required
- Tested and verified: **Works correctly** ✓

**Verification After Failover**:
```bash
# Check which node is MASTER
ifconfig | grep carp
# Expected on MASTER:
# carp: MASTER vhid 4 advbase 1 advskew 0

# Verify mDNS repeater running on MASTER only
ps aux | grep mdns
```

## IGMP Proxy Configuration

### Overview
IGMP Proxy provides multicast routing between network segments with upstream/downstream relationships.

**Service**: `/usr/local/sbin/igmpproxy`  
**Status**: Disabled (not needed for simple service discovery)  
**Config File**: `/usr/local/etc/igmpproxy.conf`

### Why Disabled

**Reasons**:
1. Sonos uses peer-to-peer multicast (no clear upstream/downstream)
2. mDNS uses link-local range (224.0.0.251) not routed by IGMP proxy
3. mDNS Repeater is simpler and more appropriate for discovery use case
4. Adds unnecessary complexity without benefit

### When to Enable

**Use IGMP Proxy For**:
- IPTV service from ISP (upstream: WAN, downstream: LAN VLANs)
- Video streaming servers with defined source VLAN
- Multicast data feeds (stock tickers, live data)
- Any scenario with clear upstream source and downstream subscribers

**Configuration Template** (if needed):
```
# Upstream interface (source of multicast)
phyint vtnet1 upstream ratelimit 0 threshold 1

# Downstream interfaces (subscribers)
phyint vlan0.10 downstream ratelimit 0 threshold 1
phyint vlan0.40 downstream ratelimit 0 threshold 1
phyint vlan0.60 downstream ratelimit 0 threshold 1
```

### Common Pitfalls

- Setting both querier on switch and IGMP proxy can cause conflicts
- Incorrect upstream/downstream designation breaks multicast completely
- Too complex for simple service discovery needs

## UDP Broadcast Relay Configuration

### Overview
UDP Broadcast Relay forwards UDP broadcast packets (255.255.255.255) for specific ports between VLANs.

**Service**: `udp_broadcast_relay` (various implementations)  
**Status**: Disabled ⚠️  
**Reason**: Causes packet loops on trunk topology

### Why Disabled

**Critical Issue**: Network outage caused by broadcast storm
- Single trunk port carries all VLANs to/from OPNsense
- Relay receives broadcast on VLAN A → sends broadcast on VLAN B
- Switch floods broadcast back to trunk (includes VLAN B)
- Relay sees VLAN B broadcast → relays back to VLAN A
- **Result**: Infinite loop, complete network saturation

**Tested Ports** (all caused loops):
- Port 5353 (mDNS) - better handled by mDNS repeater
- Port 1900 (SSDP) - not critical for Sonos

### When It Might Work

**Safe Topologies**:
- Separate physical links per VLAN (not shared trunk)
- One-way broadcast forwarding only
- Careful firewall rules to prevent return broadcasts

**Not Recommended For**:
- Shared trunk topologies (your setup)
- When multicast alternatives exist
- Complex networks with loop risk

## DHCP Relay Configuration

### Overview
DHCP Relay forwards DHCP broadcast requests to a centralized DHCP server on a different VLAN.

**Service**: `dhcrelay` (available but not used)  
**Status**: Not Used  
**Reason**: Separate DHCP server per VLAN preferred

### Current DHCP Architecture

**Per-VLAN DHCP Servers** (on OPNsense):
- **VLAN 40 (USER)**: 10.10.40.100-200
- **VLAN 60 (IOT)**: 10.10.60.100-200

**Why Separate DHCP**:
- Better security isolation
- Different lease times per network
- Separate DNS and gateway options
- IOT devices don't need to know about USER DHCP server

### When DHCP Relay Makes Sense

**Use Cases**:
- Centralized IP address management (enterprise)
- Single DHCP server for entire network
- Consistent configuration across all VLANs
- Reduced DHCP server maintenance

## DNS Configuration

### Unbound DNS Resolver

**Service**: Unbound  
**Status**: Enabled ✓  
**Listen Port**: 53 (NOT 5353 - no conflict with mDNS)  
**Listen Interfaces**: All VLANs

**Configuration**:
```
Listen Port: 53
Network Interfaces: All (10.10.10.1, 10.10.40.1, 10.10.60.1, 10.10.101.1)
DNSSEC: Enabled
DNS Rebinding: Protected with exceptions for .lan and .lab domains
```

**Domain Resolution**:
- `.lan` domains → A records pointing to VM IPs
- `.lab.nobasura.org` → CNAME to .lan domains
- External domains → Forwarded to upstream resolvers (Quad9, Cloudflare)

### No Conflict with mDNS

**Port 53 vs 5353**:
- Unbound DNS: Port 53 (standard DNS)
- mDNS Repeater: Port 5353 (multicast DNS)
- No overlap or conflict

## Firewall Rules for Cross-VLAN Multicast

### VLAN 40 (USER) → VLAN 60 (IOT) Rules

**Rule 1: mDNS Discovery**
```
Action: Pass
Interface: USER
Protocol: UDP
Source: USER net (10.10.40.0/24)
Destination: 224.0.0.0/4 (all multicast)
Destination Port: 5353
Description: Allow mDNS discovery to IOT VLAN
```

**Rule 2: Spotify Connect**
```
Action: Pass
Interface: USER
Protocol: TCP
Source: USER net (10.10.40.0/24)
Destination: IOT net (10.10.60.0/24)
Destination Port: 1400
Description: Allow Spotify Connect to Sonos speakers
```

**Existing Rule: IGMP**
```
Action: Pass
Interface: USER
Protocol: IGMP
Source: USER net
Destination: any
Description: Allow IGMP membership reports
```

### VLAN 60 (IOT) Rules

**No Additional Rules Required**:
- Stateful firewall automatically allows return traffic
- IOT devices cannot initiate connections to USER VLAN
- Security maintained: IOT → USER blocked by default

### Firewall Rule Notes

**Minimal Configuration**:
- Only 2 new rules needed on USER VLAN
- Zero new rules on IOT VLAN (stateful returns)
- No bidirectional rules (security preserved)

**Security Considerations**:
- Multicast rule allows discovery but not data transfer
- Spotify Connect only allows TCP to port 1400 (specific service)
- IOT isolation maintained (cannot initiate to USER)

## Service Monitoring and Troubleshooting

### Check Service Status

**mDNS Repeater**:
```bash
# Process check
ps aux | grep mdns-repeater

# Socket check
sockstat -4 | grep 5353

# System log
grep mdns /var/log/system.log
```

**IGMP Status**:
```bash
# IGMP groups (even with proxy disabled)
netstat -g

# IGMP messages
tcpdump -i vlan0.40 -n igmp
```

**Unbound DNS**:
```bash
# Process check
ps aux | grep unbound

# Query test
dig @10.10.40.1 apps.lan

# Statistics
unbound-control stats_noreset
```

### Troubleshooting Cross-VLAN Multicast

**Packet Capture for mDNS**:
```bash
# On USER VLAN (should see queries and responses)
tcpdump -i vlan0.40 -n port 5353

# On IOT VLAN (should see forwarded queries and original responses)
tcpdump -i vlan0.60 -n port 5353
```

**Expected Traffic Flow**:
```
USER VLAN:
  Phone sends: 10.10.40.111:5353 → 224.0.0.251:5353 (query)
  Phone receives: 10.10.40.2:5353 → 224.0.0.251:5353 (response with rewritten source)

IOT VLAN:
  Receives forwarded: 10.10.60.2:5353 → 224.0.0.251:5353 (query)
  Sonos responds: 10.10.60.42:5353 → 10.10.60.2:5353 (unicast response to repeater)
```

**Common Issues**:
1. mDNS repeater not running → check CARP status
2. No responses → check firewall rules allow multicast
3. Responses arrive but app doesn't see → source IP validation issue
4. Network loop → UDP broadcast relay enabled (disable it!)

### CARP Failover Testing

**Test Procedure**:
1. Verify current MASTER: `ifconfig | grep carp`
2. Check services running on MASTER
3. Trigger failover (or reboot MASTER node)
4. Verify new MASTER takes over
5. Check services start on new MASTER
6. Test Spotify Connect still works

**Verified Working** ✓:
- mDNS repeater starts on new MASTER
- Spotify Connect discovery continues working
- No manual intervention required

## Service Dependencies

### Switch Configuration Dependencies
- IGMP snooping must be enabled
- Reserved multicast must be set to "Flooding"
- Unknown multicast should be "Drop"

### Firewall Rule Dependencies
- mDNS repeater requires USER→multicast:5353 allowed
- Spotify Connect requires USER→IOT:1400 allowed
- IGMP should be allowed for group membership

### High Availability Dependencies
- CARP must be functioning correctly
- VLAN 102 must be working for sync
- Services marked for CARP failover start automatically

## Performance Considerations

### mDNS Repeater Overhead
- **CPU**: Negligible (simple packet copy)
- **Memory**: ~2-3 MB RSS
- **Network**: Minimal (only mDNS discovery packets)
- **Latency**: <1ms added latency

### IGMP Snooping Benefits
- Reduces multicast traffic to only interested ports
- Saves bandwidth on trunk links
- No noticeable performance impact
- Switch handles optimization in hardware

### Multicast Flooding Impact
- Reserved multicast flooding necessary for mDNS
- Slight overhead acceptable (only 224.0.0.0/24 range)
- No noticeable impact on network performance
- Discovery protocols are low-bandwidth

## Related Documentation
- [[Zyxel Switch Configuration]]
- [[VLAN Design and Routing Configuration]]
- [[Network Architecture Complete Overview]]
- [[ADR: Sonos Cross-VLAN Discovery Solution]]
- [[Multicast and IGMP Snooping Explained]]

## Tags
#opnsense #services #mdns #multicast #firewall #high-availability