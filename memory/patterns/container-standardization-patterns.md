# Container Standardization Patterns

## Service Inheritance Pattern
```yaml
# Standard service inheritance pattern
services:
  service-name:
    extends:
      file: ../common.yml
      service: base  # Provides: restart, PUID/PGID/TZ, /etc/localtime
    image: service:latest
    container_name: service-name
    # Only service-specific configuration here
```

## Port Management Rules
- Port conflicts only matter within same VM (different VMs = different IPs)
- **ALWAYS reuse service default port if available** (e.g., 8787:8787 for Enclosed)
- Use sequential port assignment only when default port conflicts (3000, 3001, 3002...)
- Document reserved ports: OpenHands→3003 (currently commented out)

## Docker Socket Access Categories
1. **Direct mount (3 services)**: `socket-proxy`, `homepage`, `openhands` (commented)
2. **Via socket-proxy (18 services)**: All management tools extend `socket-base`
3. **No socket access (48 services)**: Standard apps extend `base`

## Base Service Templates

### Standard Base (common.yml)
```yaml
base:
  restart: unless-stopped
  environment:
    - PUID=1000
    - PGID=1000
    - TZ=America/New_York
  volumes:
    - /etc/localtime:/etc/localtime:ro
  security_opt:
    - no-new-privileges:true
```

### Socket Base (for Docker management tools)
```yaml
socket-base:
  extends:
    service: base
  environment:
    - DOCKER_HOST=tcp://socket-proxy:2375
  depends_on:
    - socket-proxy
```

## Common Issues & Fixes

### Security_opt Duplication
**Problem**: Some services (gotify, uptime-kuma) had duplicate security options  
**Fix**: Remove security_opt from services extending base (already provided)

### Template Format Conflicts
**Problem**: Ansible/Docker format string conflicts in templates  
**Fix**: Escape Docker format strings or use environment variables

### Neo4j HTTPS Misconfiguration
**Problem**: Browser forces bolt+s:// with HTTPS enabled  
**Fix**: Disabled HTTPS in Neo4j, use HTTP internally + Traefik HTTPS externally

## Related Notes
- [Critical Infrastructure Rules](../core/critical-infrastructure-rules.md) - Must-follow infrastructure rules
- [Project Status](../core/project-status.md) - Current metrics and achievements
- [Dual Access Strategy](dual-access-strategy.md) - Auth patterns

## Tunnel Infrastructure Pattern (Newt Automation)

### Conditional Deployment with Safety Flags
**Pattern**: Use explicit safety flags for infrastructure-critical services
```yaml
- name: Deploying newt tunnel stack
  include_tasks: deploy_stack.yml
  when: docker_deploy and deploy_tunnels | default(false) and pangolin_newt_enabled | default(false)
  vars:
    cur_stack: newt
```

**Rationale**: 
- Prevents accidental tunnel disruption during targeted deployments
- Requires explicit `deploy_tunnels=true` flag for tunnel operations
- Separates tunnel lifecycle from application stack deployments

### Discovery-Based Stack Loading
**Pattern**: Flexible file resolution with fallback hierarchy
```yaml
- name: Copy stack files {{ cur_stack }}
  copy:
    src: "{{ item }}"
    dest: "{{ docker_compose_dir }}"
    mode: "0664"
  with_first_found:
    - "{{ inventory_hostname }}/{{ cur_stack }}"
    - "common/{{ cur_stack }}"
```

**Benefits**:
- Host-specific overrides take precedence
- Common templates provide consistent defaults
- Eliminates hardcoded paths and conditionals

### Environment Variable Management
**Pattern**: Per-stack .env generation with variable inheritance
```yaml
vars:
  stack_env_vars: >-
    {{ docker_env_vars.common | combine(
      docker_env_vars[cur_stack] | default({}),
      env_vars.common | default({}),
      env_vars[cur_stack] | default({})
    ) }}
```

**Hierarchy** (later values override earlier):
1. `docker_env_vars.common` - Global Docker defaults
2. `docker_env_vars[stack]` - Stack-specific Docker vars
3. `env_vars.common` - Host-specific global vars  
4. `env_vars[stack]` - Host-specific stack vars

### Tunnel Service Template
```yaml
services:
  newt:
    extends:
      file: ../common.yml
      service: base
    image: fosrl/newt:1.2.1
    container_name: newt
    network_mode: host
    environment:
      - NEWT_ID=${NEWT_ID}
      - NEWT_SECRET=${NEWT_SECRET}
      - PANGOLIN_ENDPOINT=${PANGOLIN_ENDPOINT}
    healthcheck:
      test: ["CMD-SHELL", "wget --quiet --spider --timeout=10 --tries=1 https://pangolin.nobasura.org || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    labels:
      - "deunhealth.restart.on.unhealthy=true"
```

**Key Design Decisions**:
- Extends standard `base` for consistency
- Uses `network_mode: host` for tunnel requirements
- Environment variables loaded from .env file (no templating needed)
- Health check validates external connectivity
- Auto-restart on health check failure