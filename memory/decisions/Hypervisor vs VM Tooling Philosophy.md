---
title: Hypervisor vs VM Tooling Philosophy
type: note
permalink: decisions/hypervisor-vs-vm-tooling-philosophy
---

# Hypervisor vs VM Tooling Philosophy

## Core Principle: Purpose-Built Systems

Each system layer should be optimized for its specific role and responsibilities.

## Hypervisor Layer (Proxmox)
**Philosophy**: Lean, stable, minimal attack surface

### Why Minimal?
- Proxmox GUI handles most management tasks
- Terminal access typically for emergencies only
- Real debugging happens in VMs/containers
- Fewer packages = fewer vulnerabilities and updates
- Better resource efficiency for VMs

### Essential Tools Only
- **System monitoring**: htop/bottom, iotop (when VM performance issues need host investigation)
- **Network debugging**: mtr, tcpdump (for VM connectivity issues)
- **Log analysis**: ripgrep (when something's broken and needs investigation)
- **API interaction**: jq (for Proxmox API calls if needed)
- **Storage monitoring**: ncdu, du equivalents (for VM disk performance problems)

### Optional Tools (Available but Not Installed)
- Modern CLI replacements (eza, bat, fd, etc.)
- Development tools
- Advanced monitoring dashboards
- Convenience tools better suited for development environments

## VM Layer (Apps/Services)
**Philosophy**: Full-featured, development-ready

### Why Full-Featured?
- Active development and debugging environment
- Container orchestration and management
- Application troubleshooting and optimization
- Regular interactive terminal usage

### Complete Toolset
- All modern CLI replacements
- Development tools and SDKs
- Advanced monitoring and profiling tools
- Container management tools (docker, lazydocker, etc.)
- Full shell enhancement suite

## Implementation Strategy

### Configuration Structure
```yaml
modern_tools:
  essential:    # Always installed
    - minimal hypervisor toolkit
  optional:     # Available but disabled by default
    - full modern toolkit
    - install: false  # Easy to enable when needed
```

### Benefits
1. **Maintainability**: Clear separation of concerns
2. **Security**: Minimal attack surface on critical infrastructure
3. **Performance**: Host resources dedicated to VMs
4. **Flexibility**: Can enable full toolkit when needed for deep debugging
5. **Consistency**: Same philosophy across all hypervisor nodes

## User Workflow Alignment

### Normal Operations
- **Hypervisor**: Proxmox GUI for VM management
- **Development**: Full toolkit in VMs/containers
- **Monitoring**: Grafana/observability stack in dedicated VMs

### Emergency Debugging
- **Available**: Essential tools pre-configured
- **Expandable**: Optional tools can be enabled rapidly
- **Familiar**: Tools match user's existing preferences and muscle memory

## Future Considerations

### Expansion Triggers
- Complex hypervisor issues requiring advanced debugging
- Infrastructure changes requiring more hands-on terminal work
- Team growth requiring more comprehensive tooling

### Migration Path
- Configuration already prepared for full toolkit
- Single variable flip to enable comprehensive tooling
- No architectural changes needed for expansion