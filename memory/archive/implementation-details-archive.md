# Implementation Details Archive

Detailed implementation patterns and discoveries for future reference.

## Docker Stack Organization Implementation

### Stack-Based Composition Pattern
Each VM organizes services into logical stacks for better management:

#### Stack Categories Implementation
```yaml
# OAM Stack (Operations & Management)
# files/*/oam/compose.yml
services:
  watchtower:
    image: containrrr/watchtower
    # Automatic container updates
  portainer-agent:
    image: portainer/agent
    # Container management UI
  dozzle-agent:
    image: amir20/dozzle
    # Container log aggregation
```

#### File Structure Implementation
```
files/{vm-name}/{stack-name}/
├── compose.yml              # Stack orchestration file
├── service1.yml            # Individual service definitions
├── service2.yml
└── config/
    ├── config.yml.j2       # Jinja2 templates for dynamic config
    └── static-config.yml   # Static configuration files
```

### Benefits Realized
- **Logical Separation**: Clear boundaries between service types
- **Independent Scaling**: Can restart/update stacks independently
- **Resource Management**: Stack-level resource allocation
- **Maintenance Simplicity**: Stack-based operations

## Traefik Priority-Based Routing Implementation

### Multiple Router Pattern Details
```yaml
# traefik_rules/dynamic_config.yml
http:
  routers:
    # Higher priority bypass router
    jellyseerr-mobile-bypass:
      rule: "Host(`jellyseerr.nobasura.org`) && Header(`traefik-auth-bypass-key`, `${TRAEFIK_AUTH_BYPASS_KEY}`)"
      priority: 300
      service: "jellyseerr-direct@file"
      tls:
        certResolver: "letsencrypt"
    
    # Lower priority auth router
    jellyseerr-auth:
      rule: "Host(`jellyseerr.nobasura.org`)"
      priority: 100
      middlewares:
        - "auth@file"
      service: "jellyseerr@http"
      tls:
        certResolver: "letsencrypt"

  services:
    # Direct IP access for bypass
    jellyseerr-direct:
      loadBalancer:
        servers:
          - url: "http://10.100.20.4:5055"
    
    # Pangolin routing for normal auth
    jellyseerr:
      loadBalancer:
        servers:
          - url: "http://pangolin:3000/jellyseerr"
```

### Template Generation Pattern
```yaml
# ansible/roles/pangolin/templates/bypass-routers.yml.j2
{% for service in auth_bypass_services %}
    {{ service.name }}-mobile-bypass:
      rule: "Host(`{{ service.host }}`) && Header(`traefik-auth-bypass-key`, `${TRAEFIK_AUTH_BYPASS_KEY}`)"
      priority: 300
      service: "{{ service.name }}-direct@file"
    
    {{ service.name }}-auth:
      rule: "Host(`{{ service.host }}`)"
      priority: 100
      middlewares:
        - "auth@file"
      service: "{{ service.name }}@http"
{% endfor %}
```

## 1Password Ansible Integration Implementation

### Lookup Pattern Details
```yaml
# Basic secret lookup
traefik_auth_bypass_key: "{{ lookup('community.general.onepassword', 'TRAEFIK_AUTH_BYPASS_KEY', vault='Homelab') }}"

# Complex environment variable injection
pangolin_env_vars:
  ORGANIZATION_ID: "{{ lookup('community.general.onepassword', 'PANGOLIN_ORGANIZATION_ID', vault='Homelab') }}"
  RESEND_API_KEY: "{{ lookup('community.general.onepassword', 'RESEND_API_KEY', vault='Homelab') }}"
  AUTH_SECRET: "{{ lookup('community.general.onepassword', 'PANGOLIN_AUTH_SECRET', vault='Homelab') }}"
```

### Secure Template Processing
```yaml
# Ansible task with secret handling
- name: "Process Pangolin configuration"
  template:
    src: config.yml.j2
    dest: "{{ pangolin_config_path }}/config.yml"
    mode: '0600'
  no_log: true  # Prevent secret exposure in logs
  notify: "Restart pangolin service"
```

### Vault Organization Strategy
```
1Password Vault: Homelab
├── TRAEFIK_AUTH_BYPASS_KEY    # Mobile API access
├── PANGOLIN_ORGANIZATION_ID   # Pangolin configuration
├── PANGOLIN_AUTH_SECRET       # Internal auth
├── RESEND_API_KEY            # Email notifications
├── NEO4J_AUTH               # Database credentials
└── GOTIFY_TOKEN             # Notification service
```

## CrowdSec Integration Implementation

### Multi-Layer Protection Setup
```yaml
# Firewall Bouncer Configuration
crowdsec_firewall_bouncer:
  api_url: "http://crowdsec:8080"
  api_key: "{{ lookup('community.general.onepassword', 'CROWDSEC_API_KEY', vault='Homelab') }}"
  log_level: "info"
  log_compression: true
  
# Traefik Plugin Configuration
crowdsec_traefik_plugin:
  enabled: true
  default_decision_timeout: "10s"
  http_timeout_seconds: 5
  update_frequency_seconds: 60
```

### Protection Layers
```
Internet → iptables/ipset → Traefik Plugin → Applications
```

1. **Network Layer**: iptables rules via Firewall Bouncer (INPUT chain)
2. **Application Layer**: Traefik Plugin (DOCKER-USER chain)
3. **Real-time Updates**: Automatic IP blocking/unblocking

## Test Framework Implementation

### Architecture-First Testing Pattern
```yaml
# tests/common/test_base.yml
- name: "Test service accessibility"
  uri:
    url: "{{ service_url }}"
    method: GET
    headers:
      User-Agent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    follow_redirects: none
    status_code: "{{ expected_status_codes }}"
  register: result
  
expected_status_codes:
  - 200  # Direct access
  - 307  # Application login redirect
```

### Service-Specific Testing
```yaml
# *arr applications require browser user-agent
arr_test_headers:
  User-Agent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
  
# Auth bypass testing
bypass_test_headers:
  traefik-auth-bypass-key: "{{ traefik_auth_bypass_key }}"
  User-Agent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
```

## Container Standardization Implementation

### Common Service Templates
```yaml
# common.yml - Base service template
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

# Socket-enabled base for Docker management tools
socket-base:
  extends:
    service: base
  environment:
    - DOCKER_HOST=tcp://socket-proxy:2375
  depends_on:
    - socket-proxy
```

### Service Inheritance Pattern
```yaml
# Service extends base template
services:
  service-name:
    extends:
      file: ../common.yml
      service: base
    image: service:latest
    container_name: service-name
    ports:
      - "3000:3000"
    # Only service-specific configuration here
```

## Related Notes
- [Completed Tasks History](../archive/completed-tasks-history.md) - Project completions
- [Technical Investigations Archive](../archive/technical-investigations-archive.md) - Research findings
- [Container Standardization Patterns](../patterns/container-standardization-patterns.md) - Current patterns
## Tunnel Infrastructure Automation Implementation

### Production Issue Resolution
**Date**: June 19, 2025  
**Issue**: Media site showing "Offline" in Pangolin UI  
**Root Cause**: Missing newt tunnel automation in Docker role  
**Resolution**: Comprehensive tunnel automation with safety patterns

### Key Implementation Patterns

#### 1. Conditional Deployment with Safety Flags
```yaml
- name: Deploying newt tunnel stack
  include_tasks: deploy_stack.yml
  when: docker_deploy and deploy_tunnels | default(false) and pangolin_newt_enabled | default(false)
  vars:
    cur_stack: newt
```

**Safety Design**:
- Conservative defaults (`false`) prevent accidental changes
- Explicit opt-in required (`deploy_tunnels=true`)
- Host-level control (`pangolin_newt_enabled`)
- Separation of tunnel and application lifecycles

#### 2. Discovery-Based Stack Loading
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

**Benefits Achieved**:
- Eliminated hardcoded conditional logic
- Host-specific overrides when needed
- Consistent common templates
- Future-proof for new services

#### 3. Environment Variable Inheritance
```yaml
stack_env_vars: >-
  {{ docker_env_vars.common | combine(
    docker_env_vars[cur_stack] | default({}),
    env_vars.common | default({}),
    env_vars[cur_stack] | default({})
  ) }}
```

**Variable Hierarchy**:
1. Global Docker defaults (PUID/PGID/TZ)
2. Stack-specific Docker vars
3. Host-specific global vars
4. Host-specific stack vars (credentials)

#### 4. Credential Management Pattern
```yaml
# inventory.yml
newt_id: "{{ lookup('community.general.onepassword', 'PANGOLIN_MEDIA_SITE_NEWT', field='username', vault='Homelab') }}"
newt_secret: "{{ lookup('community.general.onepassword', 'PANGOLIN_MEDIA_SITE_NEWT', vault='Homelab') }}"
env_vars:
  newt:
    NEWT_ID: "{{ newt_id }}"
    NEWT_SECRET: "{{ newt_secret }}"
    PANGOLIN_ENDPOINT: "https://pangolin.nobasura.org"
```

### Service Template Implementation
```yaml
# files/common/newt/compose.yml
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

### Deployment Patterns
```bash
# Safe application deployment (tunnels unchanged)
ansible-playbook deploy_docker.yml

# Explicit tunnel deployment
ansible-playbook deploy_docker.yml -e deploy_tunnels=true

# Targeted VM with tunnels
ansible-playbook deploy_docker.yml -e deploy_tunnels=true --limit media-vm
```

### Validation Results
**Container Status**: ✅ `Up 3 minutes (healthy)`  
**Tunnel Connectivity**: ✅ 8 TCP proxies active with 3-4ms latency  
**Production Status**: ✅ Media site "Offline" → "Online" in Pangolin UI  
**Services Connected**: Radarr, Readarr, Bazarr, qBittorrent, Jellyfin, Overseerr, Homepage, Jackett

### Benefits Achieved
1. **Eliminated Manual Fixes**: Production issue resolved with automation
2. **Safety Mechanisms**: Prevented accidental tunnel disruption
3. **Code Consistency**: Followed existing Docker role patterns
4. **Credential Security**: Maintained 1Password integration
5. **Health Monitoring**: Continuous connectivity validation
6. **Auto-Recovery**: Restart on health check failure

### Files Modified
- `ansible/files/common/newt/compose.yml` (new)
- `ansible/roles/docker/tasks/main.yml` (conditional deployment)
- `ansible/roles/docker/tasks/deploy_stack.yml` (discovery pattern)
- `ansible/inventory.yml` (credentials and env_vars)