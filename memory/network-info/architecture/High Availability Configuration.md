---
title: High Availability Configuration
type: note
permalink: network-info/architecture/high-availability-configuration
---

# High Availability Configuration

## Overview

The homelab implements high availability at multiple layers:
- **Network Level**: Dual OPNsense routers with CARP failover
- **Service Level**: Container health monitoring and auto-restart
- **Storage Level**: ZFS mirror on TrueNAS
- **Future**: Proxmox clustering and service orchestration

## OPNsense CARP Configuration

### Architecture
```mermaid
graph TB
    subgraph "High Availability Routing"
        VIP[CARP VIPs<br/>10.10.x.1]
        
        subgraph "px-net"
            OPN1[OPNsense Primary<br/>10.10.101.12<br/>Priority: 1]
        end
        
        subgraph "px-nas"
            OPN2[OPNsense Secondary<br/>10.10.101.13<br/>Priority: 2]
        end
        
        SYNC[CARP Sync<br/>VLAN 102]
    end
    
    subgraph "Clients"
        VM[VMs]
        USER[User Devices]
        IOT[IoT Devices]
    end
    
    VM -->|Gateway| VIP
    USER -->|Gateway| VIP
    IOT -->|Gateway| VIP
    
    OPN1 <-->|State Sync| SYNC
    OPN2 <-->|State Sync| SYNC
    
    VIP -.->|Active| OPN1
    VIP -.->|Standby| OPN2
    
    style OPN1 fill:#2ecc71,color:#fff
    style OPN2 fill:#3498db,color:#fff
    style VIP fill:#e74c3c,color:#fff
```

### CARP Virtual IPs

| VLAN | Virtual IP | Description | VHID |
|------|------------|-------------|------|
| 10 | 10.10.10.1 | LAB Gateway | 10 |
| 40 | 10.10.40.1 | USER Gateway | 40 |
| 60 | 10.10.60.1 | IOT Gateway | 60 |
| 101 | 10.10.101.1 | MGMT Gateway | 101 |

### Failover Configuration

```yaml
Primary (px-net):
  Base Priority: 1
  Preemption: Enabled
  Advertising Frequency: 1 second
  
Secondary (px-nas):
  Base Priority: 2
  Preemption: Enabled
  Advertising Frequency: 1 second

Failover Time: < 3 seconds
Failback: Automatic when primary recovers
```

### State Synchronization

**Synchronized Components**:
- Firewall rules
- NAT configuration
- DHCP leases
- IPsec tunnels
- User certificates
- Aliases and tables

**Sync Interface**: VLAN 102 (dedicated)
**Sync Protocol**: pfsync over dedicated VLAN
**Security**: Encrypted with shared key

## WAN Failover Design

### Dual WAN Connectivity
```mermaid
graph LR
    ISP[ISP Router<br/>1Gbps Static IP]
    
    subgraph "Ubiquiti Flex Mini"
        P1[Port 1: PoE/MGMT]
        P2[Port 2: WAN In]
        P3[Port 3: px-net]
        P4[Port 4: px-nas]
    end
    
    subgraph "Failover Path"
        WAN1[px-net WAN<br/>Primary]
        WAN2[px-nas WAN<br/>Secondary]
    end
    
    ISP -->|RJ45| P2
    P2 -->|Untagged| P3
    P2 -->|Untagged| P4
    P3 -->|enp2s0| WAN1
    P4 -->|enp88s0| WAN2
    
    style WAN1 fill:#2ecc71,color:#fff
    style WAN2 fill:#3498db,color:#fff
```

**Failover Behavior**:
- Both OPNsense instances have independent WAN connections
- Active instance handles all WAN traffic
- On failover, secondary takes over with same public IP
- Gateway monitoring triggers failover on WAN failure

## Service High Availability

### Container Management
```yaml
Restart Policies:
  - unless-stopped: Default for all services
  - always: Critical services (Traefik, Pangolin)
  
Health Checks:
  - Interval: 30s
  - Timeout: 10s
  - Retries: 3
  - Start Period: 40s
```

### Monitoring Stack
- **Uptime Kuma**: Service availability monitoring
- **Deunhealth**: Docker health status aggregation
- **Gotify**: Alert notifications
- **Grafana**: Dashboards and alerting

### Automated Recovery
```mermaid
graph LR
    subgraph "Health Monitoring"
        HC[Health Check<br/>Every 30s]
        WT[Watchtower<br/>Updates]
        DH[Deunhealth<br/>Status]
    end
    
    subgraph "Actions"
        RS[Restart<br/>Service]
        NT[Notify<br/>Admin]
        FL[Failover<br/>to Backup]
    end
    
    HC -->|Failed| RS
    HC -->|Critical| NT
    WT -->|Updated| RS
    DH -->|Degraded| NT
    
    style HC fill:#3498db,color:#fff
    style RS fill:#e74c3c,color:#fff
    style NT fill:#f39c12,color:#fff
```

## Storage High Availability

### TrueNAS Configuration
- **Pool**: 2x 16TB HDDs in ZFS mirror
- **Redundancy**: Single disk failure tolerance
- **Scrub Schedule**: Weekly
- **Snapshots**: Hourly (24), Daily (7), Weekly (4)
- **Replication**: Planned to backup location

### VM Storage
- **Local-ZFS**: On each Proxmox host
- **Shared Storage**: NFS from TrueNAS
- **Backup**: Proxmox Backup Server (planned)

## Future HA Enhancements

### Proxmox Clustering (Planned)
```mermaid
graph TB
    subgraph "3-Node Proxmox Cluster"
        PX1[px-net<br/>Quorum Node]
        PX2[px-nas<br/>Quorum Node]
        PX3[px-cpu<br/>Quorum Node]
    end
    
    subgraph "Shared Resources"
        CEPH[Ceph Storage<br/>Distributed]
        HA[HA Manager<br/>VM Migration]
    end
    
    PX1 <--> PX2
    PX2 <--> PX3
    PX1 <--> PX3
    
    PX1 --> CEPH
    PX2 --> CEPH
    PX3 --> CEPH
    
    style PX3 fill:#e74c3c,color:#fff,stroke-dasharray: 5 5
```

### Service Orchestration (Planned)
- **Nomad**: Distributed scheduler
- **Consul**: Service discovery
- **Vault**: Secret management
- **Benefits**:
  - Automatic service placement
  - Rolling updates
  - Self-healing
  - Resource optimization

## Monitoring and Alerting

### Key Metrics
- CARP status changes
- WAN connectivity
- Service health status
- Disk usage and health
- CPU/Memory utilization

### Alert Channels
- Gotify push notifications
- Email via Resend API
- Grafana dashboard alerts
- Uptime Kuma status page

## Recovery Procedures

### OPNsense Failover Test
```bash
# Manual failover test
1. SSH to primary OPNsense
2. Maintenance mode: ifconfig carpX down
3. Verify secondary takes over
4. Restore: ifconfig carpX up

# Monitor during failover
tail -f /var/log/system.log | grep carp
```

### Service Recovery Priority
1. **Critical**: Routing, DNS, DHCP
2. **High**: Authentication, reverse proxy
3. **Medium**: Application services
4. **Low**: Monitoring, logging

## Best Practices

1. **Regular Testing**: Monthly failover tests
2. **Documentation**: Runbooks for common failures
3. **Monitoring**: Proactive alerting before failures
4. **Maintenance Windows**: Planned with notifications
5. **Backup Verification**: Regular restore tests
6. **Change Management**: Test in dev before production