---
title: 'ADR-002: Sonos Cross-VLAN Discovery Solution'
type: note
permalink: decisions/adr-002-sonos-cross-vlan-discovery-solution
---

# ADR-002: Sonos Cross-VLAN Discovery Solution

**Status**: Accepted  
**Date**: 2025-10-24  
**Decision Makers**: Infrastructure Team  
**Related**: [[OPNsense Services Configuration]], [[Zyxel Switch Configuration]], [[Multicast and IGMP Snooping Explained]]

## Context

Sonos speakers are located on IOT VLAN (60) for security isolation, while user devices (phones, laptops) are on USER VLAN (40). Users need to discover and control Sonos speakers from their devices without compromising network security.

### Requirements
1. Discover Sonos speakers from USER VLAN devices
2. Control Sonos speakers (Spotify Connect preferred)
3. Maintain IOT → USER security isolation
4. Support CARP high availability failover
5. Minimal configuration complexity
6. No network disruption or packet loops

### Network Topology
- **USER VLAN (40)**: 10.10.40.0/24 - User devices
- **IOT VLAN (60)**: 10.10.60.0/24 - Sonos speakers (10.10.60.41-43)
- **OPNsense HA**: Two instances with CARP failover
- **Switch**: Zyxel XMG-1920 with single trunk to OPNsense

### Technical Challenges
1. **Multicast Link-Local**: mDNS uses 224.0.0.251 (never routed by design)
2. **VLAN Isolation**: Broadcast/multicast domains separated
3. **Source IP Validation**: Modern apps validate mDNS response source IPs
4. **Trunk Topology**: Single trunk carries all VLANs (risk of loops)

## Decision

**Implement mDNS Repeater on OPNsense with minimal firewall rules**

### Solution Components

#### 1. OPNsense mDNS Repeater
- **Service**: `/usr/local/bin/mdns-repeater`
- **Interfaces**: vlan0.40 (USER), vlan0.60 (IOT)
- **CARP Failover**: Enabled (runs on MASTER only)
- **Behavior**: Copies mDNS packets between configured interfaces bidirectionally

#### 2. Firewall Rules (USER VLAN)
```
Rule 1: Pass UDP from USER net to 224.0.0.0/4 port 5353 (mDNS discovery)
Rule 2: Pass TCP from USER net to IOT net port 1400 (Spotify Connect)
Rule 3: Pass IGMP from USER net to any (multicast group management)
```

#### 3. Firewall Rules (IOT VLAN)
```
No additional rules required (stateful return traffic allowed)
```

#### 4. Switch IGMP Snooping
- **IGMP Snooping**: Enabled
- **IGMP Querier**: Enabled (backup)
- **Unknown Multicast**: Drop
- **Reserved Multicast**: **Flooding** (CRITICAL for mDNS)

### How It Works

```
1. Phone (10.10.40.111) sends mDNS query to 224.0.0.251:5353
2. Switch floods to all USER VLAN ports (reserved multicast = flooding)
3. OPNsense vlan0.40 receives query
4. Firewall allows USER → multicast:5353
5. mDNS repeater copies packet to vlan0.60
6. Switch floods to all IOT VLAN ports
7. Sonos speakers (10.10.60.42) receive query and respond
8. mDNS repeater forwards response back to vlan0.40 (source IP rewritten to 10.10.40.2)
9. Spotify app accepts discovery and makes direct TCP connection to 10.10.60.42:1400
10. Firewall allows USER → IOT:1400 (Spotify Connect)
```

## Alternatives Considered

### Alternative 1: UDP Broadcast Relay
**Rejected** - Caused complete network outage

**Attempted Configuration**:
- UDP broadcast relay for ports 5353 (mDNS) and 1900 (SSDP)
- Forward broadcasts between USER and IOT VLANs

**Why It Failed**:
- Single trunk port carries all VLANs
- Relay creates bidirectional broadcast forwarding
- Broadcast on VLAN A → relayed to VLAN B → flooded back to trunk → received on VLAN B → relayed to VLAN A
- **Result**: Infinite loop, complete network saturation within seconds
- **Impact**: Lost internet access across entire network

**Lesson**: UDP broadcast relay incompatible with shared trunk topologies

### Alternative 2: IGMP Proxy
**Rejected** - Too complex and inappropriate for use case

**Why Not Used**:
- IGMP proxy designed for upstream/downstream multicast routing (IPTV, video streaming)
- Sonos uses peer-to-peer multicast (no clear upstream/downstream)
- mDNS uses link-local range (224.0.0.251) not routed by IGMP proxy
- Adds unnecessary complexity

**When It Makes Sense**: IPTV with ISP multicast source

### Alternative 3: Move Sonos to USER VLAN
**Rejected** - Defeats security isolation purpose

**Why Not Preferred**:
- Loses IOT isolation benefits
- Other IoT devices would also need to move
- Increases attack surface
- Solution should enable cross-VLAN functionality, not remove isolation

### Alternative 4: Separate Physical Links Per VLAN
**Rejected** - Hardware limitation

**Why Not Feasible**:
- Would require multiple network interfaces per VLAN
- Significantly increases hardware complexity
- Current 10Gbps SFP+ trunk sufficient for performance
- Not worth hardware investment for this use case

## Consequences

### Positive Outcomes ✅

1. **Spotify Connect Works Perfectly**
   - Full speaker discovery from USER VLAN
   - Control playback on any Sonos speaker
   - Group speakers together
   - Verified working on phone and laptop

2. **Minimal Configuration**
   - Only 2 new firewall rules on USER VLAN
   - Zero new rules on IOT VLAN (stateful returns)
   - Simple mDNS repeater configuration
   - No switch configuration complexity

3. **Security Maintained**
   - IOT cannot initiate connections to USER VLAN
   - Only specific discovery and control ports allowed
   - Firewall logs all cross-VLAN traffic
   - Default deny policy preserved

4. **High Availability Verified**
   - mDNS repeater works with CARP failover
   - Service starts automatically on new MASTER
   - Spotify Connect continues working during failover
   - Zero manual intervention required

5. **Performance**
   - No noticeable latency
   - CPU overhead negligible
   - Network bandwidth impact minimal
   - No packet loss or errors

6. **Educational Value**
   - Team learned multicast networking deeply
   - Documented troubleshooting process
   - Created educational guide for future reference
   - Understanding of IGMP snooping internals

### Known Limitations ⚠️

1. **Sonos App Discovery Fails**
   - **Cause**: Source IP validation - mDNS repeater rewrites source to OPNsense interface IP (10.10.40.2) instead of actual speaker IP (10.10.60.42)
   - **Impact**: Modern Sonos app rejects responses due to mismatch
   - **Workaround**: Use Spotify Connect (works perfectly) or switch phone to IOT WiFi for Sonos app configuration
   - **Acceptable**: Spotify provides full control, Sonos app only needed for initial setup

2. **YouTube Casting Not Tested**
   - **Status**: Unknown if YouTube casting works cross-VLAN
   - **Mitigation**: Can cast to Fire TV connected to same network if needed
   - **Decision**: Not critical enough to investigate further

3. **Reserved Multicast Flooding**
   - **Trade-off**: Switch floods reserved multicast (224.0.0.0-224.0.0.255) to all ports
   - **Impact**: Slight bandwidth overhead for discovery protocols
   - **Justification**: Necessary for zero-config protocols (mDNS, LLMNR) to function
   - **Acceptable**: Minimal overhead, discovery traffic is infrequent and low-bandwidth

### Negative Consequences Avoided ❌

1. **Network Loops** - Avoided by disabling UDP broadcast relay
2. **Configuration Complexity** - Avoided by not using IGMP proxy
3. **Security Degradation** - Avoided by maintaining IOT isolation
4. **HA Complications** - Avoided by using CARP-aware services

## Implementation Timeline

### Phase 1: Initial Attempt (Failed)
- **Date**: 2025-10-24 (early)
- **Action**: Configured mDNS repeater with wrong interfaces (LAB, USER instead of IOT, USER)
- **Result**: "No products found" error in Sonos app
- **Learning**: Interface selection critical for repeater functionality

### Phase 2: UDP Broadcast Relay (Failed)
- **Date**: 2025-10-24 (mid)
- **Action**: Attempted UDP broadcast relay for ports 5353 and 1900
- **Result**: Complete network outage - lost internet across entire network
- **Learning**: UDP broadcast relay incompatible with trunk topology - creates unavoidable loops

### Phase 3: Reserved Multicast Setting (Failed)
- **Date**: 2025-10-24 (mid)
- **Action**: Changed switch "Reserved Multicast Group" from "Flooding" to "Drop"
- **Result**: Complete connectivity loss - websites won't open, ping fails
- **Learning**: Reserved multicast flooding REQUIRED for mDNS (224.0.0.251) to function

### Phase 4: Scientific Debugging (Breakthrough)
- **Date**: 2025-10-24 (late)
- **Action**: Used tcpdump to analyze packet flow on both VLANs
- **Finding**: mDNS repeater working perfectly - packets flow correctly
- **Discovery**: Sonos app rejects responses due to source IP mismatch (OPNsense IP vs speaker IP)
- **Learning**: Network working correctly, app-level validation causing discovery failure

### Phase 5: Spotify Connect Success (Final)
- **Date**: 2025-10-24 (evening)
- **Action**: Tested Spotify Connect as alternative to Sonos app
- **Result**: **Works perfectly!** - All speakers discovered and controllable
- **Acceptance**: Spotify Connect sufficient, Sonos app limitation acceptable

### Phase 6: High Availability Validation (Complete)
- **Date**: 2025-10-24 (night)
- **Action**: Booted secondary OPNsense (opnsense2) and tested CARP failover
- **Result**: mDNS repeater with CARP failover works correctly
- **Status**: **Solution complete and validated** ✅

## Validation and Testing

### Functional Testing
- ✅ Spotify Connect discovers all Sonos speakers
- ✅ Can control playback from phone (VLAN 40)
- ✅ Can control playback from laptop (VLAN 40)
- ✅ Can group speakers together
- ✅ Can switch between different speakers
- ✅ Audio quality unchanged
- ✅ No noticeable latency

### Network Testing
- ✅ tcpdump shows mDNS queries forwarded USER → IOT
- ✅ tcpdump shows Sonos responses forwarded IOT → USER
- ✅ Packet flow verified bidirectionally
- ✅ No packet loss or errors
- ✅ Firewall logs show allowed cross-VLAN traffic

### High Availability Testing
- ✅ Primary OPNsense (opnsense1) runs mDNS repeater
- ✅ Failover to secondary (opnsense2) successful
- ✅ mDNS repeater starts on new MASTER automatically
- ✅ Spotify Connect continues working after failover
- ✅ No manual intervention required

### Security Testing
- ✅ IOT VLAN cannot initiate connections to USER VLAN
- ✅ Only mDNS (5353) and Spotify (1400) allowed USER → IOT
- ✅ Firewall blocks other IOT → USER traffic
- ✅ Default deny policy maintained

### Edge Case Testing
- ✅ Works with multiple speakers simultaneously
- ✅ Works with speaker groups
- ✅ Survives speaker reboot
- ✅ Survives phone WiFi reconnection
- ✅ Survives CARP failover

## Maintenance and Operations

### Monitoring
- Monitor mDNS repeater process on MASTER node
- Check firewall logs for unusual cross-VLAN traffic
- Verify IGMP snooping statistics on switch
- Monitor CARP status for failover events

### Troubleshooting Runbook

**Symptom**: Spotify Connect stops working
```bash
1. Check which node is MASTER: ifconfig | grep carp
2. Verify mDNS repeater running: ps aux | grep mdns
3. Check firewall rules: Review USER VLAN rules for port 5353 and 1400
4. Test connectivity: ping from USER to IOT devices
5. Capture packets: tcpdump -i vlan0.40 -n port 5353
6. Check switch: Verify "Reserved Multicast: Flooding" still enabled
```

**Symptom**: Network outage after configuration change
```bash
1. Check if UDP broadcast relay accidentally enabled
2. Verify reserved multicast is "Flooding" not "Drop"
3. Review recent firewall rule changes
4. Check switch logs for errors
5. Restart affected services if needed
```

### Documentation Maintenance
- Keep firewall rules documented in this ADR
- Update switch configuration document when IGMP settings change
- Document any new limitations discovered
- Record failover test results

### Future Enhancements

**Guest Network Extension**:
- Add guest VLAN interface to mDNS repeater
- Add similar firewall rules for guest → IOT
- Test and document guest Spotify Connect access

**Other Discovery Protocols**:
- Consider enabling for Chromecast (also uses mDNS)
- Test AirPlay discovery (also mDNS-based)
- Document any additional protocols needed

## References

### Internal Documentation
- [[Multicast and IGMP Snooping Explained]] - Educational guide
- [[OPNsense Services Configuration]] - Service details
- [[Zyxel Switch Configuration]] - Switch settings
- [[VLAN Design and Routing Configuration]] - Network architecture

### External References
- RFC 6762: Multicast DNS specification
- Sonos Integration Guide: https://docs.sonos.com
- OPNsense Documentation: https://docs.opnsense.org
- IGMP Snooping Best Practices: Zyxel documentation

### Troubleshooting Session
Complete troubleshooting process documented in:
- Conversation logs with detailed tcpdump analysis
- Multiple failed attempts and lessons learned
- Scientific debugging methodology applied

## Decision Review

**Review Date**: 2025-10-24  
**Outcome**: **Solution accepted and deployed** ✅

**Success Criteria Met**:
- ✅ Spotify Connect works perfectly
- ✅ Security isolation maintained
- ✅ High availability validated
- ✅ Minimal configuration
- ✅ No network disruption
- ✅ Documented and reproducible

**Outstanding Items**: None

## Tags
#adr #decision-record #sonos #multicast #mdns #cross-vlan #spotify-connect #networking