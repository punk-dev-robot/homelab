---
title: Network Documentation Summary and Review
type: note
permalink: network-info/architecture/network-documentation-summary-and-review
---

# Network Documentation Summary and Review

## Documentation Created

I've created comprehensive network architecture documentation covering all aspects of your homelab infrastructure. Here's what has been documented:

### 1. Network Architecture Overview
- Complete infrastructure summary
- Physical topology overview  
- Network layers (Physical, VLAN, Routing, Services)
- Access patterns (internal/external)
- Security architecture
- Navigation links to detailed sections

### 2. C4 Architecture Diagrams
- **Level 1**: System Context - Shows external users, homelab system, and external services
- **Level 2**: Container Diagram - High-level components including VPS, network infrastructure, and VMs
- **Level 3**: Component Diagram - Detailed service breakdown by VM
- **Level 4**: Deployment Diagram - Physical network connections and hardware

All diagrams are in Mermaid format for easy visualization and updates.

### 3. VLAN Design and Routing
- Detailed VLAN definitions (1, 10, 40, 60, 101, 102, 666)
- IP ranges and purposes for each VLAN
- Inter-VLAN routing rules and firewall policies
- Switch port configurations for both Zyxel and Flex Mini
- Proxmox VLAN-aware bridge configurations
- DNS and DHCP setup details

### 4. High Availability Configuration
- OPNsense CARP configuration with virtual IPs
- Failover mechanisms and timing
- State synchronization between instances
- WAN failover design
- Service-level HA (container restart policies)
- Storage HA with ZFS mirrors
- Future plans for Proxmox clustering and Nomad orchestration

### 5. Service Distribution
- Current allocation across apps-vm, media-vm, and obs-vm
- Detailed service lists with ports for each stack
- Resource allocation guidelines
- Network traffic patterns
- Service discovery and routing methods
- Proposed redistribution plan for px-cpu integration

### 6. Physical Network Topology
- Rack layout ASCII diagram
- Complete cable matrix with connection details
- Port speed reference for all devices
- Power distribution and budget
- Environmental considerations
- Future expansion planning
- Maintenance access requirements

## Key Findings and Observations

### Strengths
1. **Well-designed VLAN segmentation** for security and organization
2. **High-speed backbone** with 10Gbps SFP+ connections
3. **Robust HA setup** with CARP failover
4. **Clear service separation** by function
5. **Future-ready** with pre-provisioned px-cpu port

### Current Limitations
1. **Single points of failure**:
   - ISP connection (no multi-WAN)
   - Main switch (no redundancy)
   - Storage concentrated on px-nas

2. **Resource concentration**:
   - Apps-vm running many critical services
   - No current service orchestration

### Opportunities with px-cpu
1. **True 3-node HA** for critical services
2. **Better resource distribution** based on workload types
3. **Potential for Proxmox clustering**
4. **Foundation for Nomad orchestration**

## Recommendations for px-cpu Integration

### Naming Suggestion
Based on its intended role as the primary compute and HA node, I recommend:
- **px-core** - Emphasizes its central role in the infrastructure
- Alternative: **px-prime** - Indicates primary compute resource

### Network Integration Plan
1. Connect to pre-provisioned Zyxel port 5
2. Use same pattern as px-nas:
   - eth1 for MGMT (2.5G)
   - Future: TB4 to 10GbE adapter for high-speed VLAN trunk
3. Configure all necessary VLANs
4. Add as tertiary OPNsense node

### Service Migration Priority
1. **Phase 1**: AI and database services (high CPU/memory needs)
2. **Phase 2**: Tools and development services
3. **Phase 3**: Critical monitoring (Prometheus, Grafana)
4. **Phase 4**: Implement service orchestration

## Questions for Clarification

Before proceeding to Phase 2 (detailed px-cpu integration planning):

1. **Naming preference**: Do you prefer px-core, px-prime, or would you like other suggestions?

2. **Timeline**: When do you plan to integrate px-cpu into the network?

3. **Thunderbolt networking**: Are you interested in exploring TB4 to 10GbE adapters for px-cpu and px-nas to create a high-speed interconnect?

4. **Orchestration preference**: You mentioned Nomad - would you like the integration plan to include Nomad setup from the start?

5. **Storage strategy**: Should px-cpu have local storage only, or would you want to explore distributed storage options?

## Next Steps

With this documentation complete, we can:
1. Review and refine any sections you'd like adjusted
2. Export the documentation to files if desired
3. Move to Phase 2 for detailed px-cpu integration planning
4. Create specific runbooks for common operations

What would you like to review or discuss about the documentation?