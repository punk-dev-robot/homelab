---
title: Risk Mitigation and Pre-Flight Testing Plan
type: note
permalink: network-info/implementation/risk-mitigation-and-pre-flight-testing-plan
---

# Risk Mitigation and Pre-Flight Testing Plan

## Critical Pre-Implementation Testing

### 1. CARP Health Verification (1 Week Before)

```bash
# Test 1: Current State Verification
# On both OPNsense instances via console/SSH:
- Check CARP status in web UI
- Verify all CARP VIPs are assigned
- Check sync status between nodes
- Review logs for any CARP flapping

# Test 2: Controlled Failover Test
# Schedule 15-minute maintenance window for testing:

1. Monitor from client machine:
   while true; do ping -c 1 8.8.8.8; sleep 1; done

2. On px-net OPNsense (current MASTER):
   # Demote to BACKUP
   sysctl net.inet.carp.demotion=100
   
3. Verify px-nas becomes MASTER:
   - Check all VIPs move
   - Monitor client ping (should see <3 seconds interruption)
   - Test critical services (DNS, DHCP)

4. Restore px-net to MASTER:
   sysctl net.inet.carp.demotion=0
   
5. Document failover time and any issues
```

### 2. SFP+ Module Testing (Before Implementation Day)

```bash
# Test the SFP+ to RJ45 module:
1. Install in unused port (enp1s0f1 on px-net)
2. Connect to laptop with iperf3
3. Verify 2.5Gb capability:
   iperf3 -s  # on laptop
   iperf3 -c laptop_ip -t 30  # on px-net
4. Check for any errors:
   ethtool enp1s0f1
   dmesg | tail -50
```

### 3. Switch Port 6 Pre-Configuration

```bash
# Configure port 6 identically to port 10:
# Can be done days in advance with no impact

interface port-channel 6
  name "px-net vlan trunk"
  pvid 101
  frame-type tagged
  vlan-trunking
  speed-duplex 2500-full
exit

# Test with laptop:
1. Configure laptop with VLAN 101 IP (10.10.101.200/24)
2. Connect to port 6
3. Verify can ping 10.10.101.1
4. Verify VLAN tagging works
```

## Detailed Risk Matrix

| Risk | Probability | Impact | Mitigation | Rollback |
|------|------------|---------|------------|-----------|
| SFP+ module incompatible | Low | High | Pre-test module | Use original optical |
| Cable failure | Low | High | Test cable, have spare | Swap cable |
| Port 6 config wrong | Low | High | Pre-configure and test | Move back to port 10 |
| Interface name changes | Medium | Medium | Have console ready | Manual reconfigure |
| CARP fails during change | Low | Low | Do when px-nas is MASTER | Already failed over |
| Bridge config error | Low | High | Copy exact config | Restore from backup |
| DNS/DHCP interruption | Low | Medium | Test during low usage | Quick rollback |

## Implementation Day Checklist

### Equipment Ready
- [ ] SFP+ to RJ45 module (tested)
- [ ] CAT6 cable (tested)
- [ ] Console cable for px-net
- [ ] Laptop for emergency access
- [ ] Backup of all configs on USB

### Pre-Staging (Day Before)
- [ ] Port 6 configured and tested
- [ ] CARP failover tested and working
- [ ] px-cpu Proxmox installed
- [ ] px-cpu basic networking confirmed
- [ ] All configs backed up

### Communication Plan
- [ ] Maintenance window announced
- [ ] Contact info for key people
- [ ] Rollback decision criteria defined

## Safe Implementation Sequence

### Phase A: px-cpu Setup (Zero Downtime)
1. Install Proxmox with basic config
2. Connect MGMT only (port 5)
3. Verify access and stability
4. Pre-stage network config file
5. Connect SFP+ to port 10 (but don't configure bridges yet)

### Phase B: Controlled Testing
1. Create test VM on px-cpu
2. Configure single test bridge
3. Verify VLAN connectivity
4. Delete test setup

### Phase C: px-net Failover (Safest Approach)
```bash
# New approach - keep px-nas as MASTER during change:

1. Morning of change:
   - Force px-nas to MASTER
   - Disable preemption on px-net
   - Verify all traffic through px-nas

2. Make px-net change:
   - Now px-net is BACKUP (no impact if it goes down)
   - Make network changes
   - Verify it comes back as BACKUP
   
3. Test carefully:
   - Let it run as BACKUP for 1 hour
   - Monitor for any issues
   - Then test failover to px-net
   
4. If all good:
   - Re-enable preemption
   - Normal CARP operation resumes
```

## Console Access Preparation

### px-net Serial Console Setup
```bash
# In case network access is lost:
1. Connect serial cable before changes
2. Test console access:
   screen /dev/ttyUSB0 115200
   
3. Have these commands ready:
   # Quick interface reset:
   ifconfig vmbr0 down
   ifconfig vmbr0 up
   
   # Restart networking:
   systemctl restart networking
   
   # Emergency SSH enable:
   ip addr add 10.10.101.12/24 dev enp3s0
```

## Go/No-Go Decision Points

### Before Starting
- [ ] CARP failover tested successfully in both directions
- [ ] Port 6 confirmed working with test device
- [ ] px-cpu responding on management network
- [ ] All backups completed and verified
- [ ] Rollback plan understood by all involved

### After Each Step
- [ ] Expected result achieved
- [ ] No unexpected errors in logs
- [ ] Services remain available
- [ ] Rollback still possible

## Emergency Contacts and Procedures

### If Internet Goes Down
1. Check if local services still work
2. Console into px-nas OPNsense
3. Verify it's MASTER for all CARPs
4. Check WAN interface status
5. Rollback px-net if needed

### If CARP Fails
1. Manually assign VIPs on working node
2. Disable CARP temporarily
3. Investigate after service restored

### If Complete Failure
1. Move cable back to port 10
2. Replace optical SFP+ module
3. Restart OPNsense VM
4. Should restore in <5 minutes