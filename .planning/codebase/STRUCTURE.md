# Codebase Structure

**Analysis Date:** 2026-02-05

## Directory Layout

```
lab/
├── ansible/
│   ├── inventory.yml                          # Host groups, vars, credentials
│   ├── common.yml                             # Shared base service definitions
│   ├── requirements.yaml                      # Ansible Galaxy role dependencies
│   │
│   ├── deploy_docker.yml                      # Deploy homelab VMs (apps, media, obs)
│   ├── deploy_vps.yml                         # Deploy gateway VPS (Pangolin, Authentik)
│   ├── deploy_crowdsec_firewall_bouncer.yml   # Deploy CrowdSec firewall protection
│   ├── provision.yml                          # Initial setup (hostname, utils)
│   ├── test-connection.yml                    # SSH connectivity check
│   │
│   ├── group_vars/
│   │   ├── all.yml                            # Global vars (docker_uid, paths, TZ)
│   │   └── proxmox/
│   │       ├── main.yml                       # Proxmox cluster config (reference only)
│   │       └── modern_tools.yml               # Tool versions for Proxmox
│   │
│   ├── host_vars/
│   │   └── px-cpu.yml                         # Proxmox-specific overrides
│   │
│   ├── roles/
│   │   ├── docker/                            # Docker installation and compose deployment
│   │   │   ├── tasks/
│   │   │   │   ├── main.yml                   # Entry point: setup + deploy stacks
│   │   │   │   ├── setup.yml                  # Docker install, dir creation, validation
│   │   │   │   └── deploy_stack.yml           # Iterate stacks, template, docker compose
│   │   │   └── defaults/
│   │   │       └── main.yml                   # Docker defaults (restart policy, etc)
│   │   │
│   │   ├── pangolin/                          # Pangolin tunnel infrastructure mgmt
│   │   │   ├── tasks/
│   │   │   │   ├── main.yml                   # Entry point: validate, include sub-tasks
│   │   │   │   ├── resource_management.yml    # API calls to create/update resources
│   │   │   │   ├── host_configuration.yml     # /etc/hosts entries for services
│   │   │   │   ├── auth_bypass.yml            # Static auth rules for services
│   │   │   │   ├── user_management.yml        # User provisioning (stub)
│   │   │   │   └── monitoring.yml             # Health checks (stub)
│   │   │   ├── defaults/
│   │   │   │   └── main.yml                   # Pangolin defaults
│   │   │   ├── vars/
│   │   │   │   └── auth_bypass.yml            # Auth bypass service definitions
│   │   │   ├── templates/
│   │   │   │   └── bypass-routers.yml.j2      # Traefik auth bypass rules
│   │   │   └── handlers/
│   │   │       └── main.yml                   # Handlers (reload traefik, etc)
│   │   │
│   │   └── crowdsec_firewall_bouncer/         # CrowdSec firewall IP blocking
│   │       ├── tasks/
│   │       │   └── main.yml                   # Deploy bouncer container
│   │       ├── defaults/
│   │       │   └── main.yml                   # Bouncer defaults
│   │       ├── files/
│   │       │   ├── compose.yml                # Bouncer service definition
│   │       │   └── config/crowdsec/           # CrowdSec parsers, scenarios, profiles
│   │       └── handlers/
│   │           └── main.yml                   # Handlers for config changes
│   │
│   ├── files/
│   │   ├── common/
│   │   │   ├── newt/
│   │   │   │   └── compose.yml                # Pangolin Newt tunnel client
│   │   │   └── {stack_name}/
│   │   │       └── compose.yml                # Stack files (fallback for all hosts)
│   │   │
│   │   ├── apps-vm/                           # Application VM stacks
│   │   │   ├── ai/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── litellm.yml                # LiteLLM proxy + PostgreSQL + Prometheus
│   │   │   │   ├── openwebui.yml              # OpenWebUI interface
│   │   │   │   ├── openhands.yml              # OpenHands agent (disabled)
│   │   │   │   ├── prometheus.yml             # Standalone Prometheus for LiteLLM
│   │   │   │   └── litellm-config.yaml        # LiteLLM model configuration
│   │   │   │
│   │   │   ├── dbs/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   └── neo4j.yml                  # Neo4j graph database
│   │   │   │
│   │   │   ├── lab/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── homepage.yml               # Homepage service portal
│   │   │   │   └── homepage-config/           # Homepage widget/service definitions
│   │   │   │
│   │   │   ├── tools/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── it-tools.yml               # IT utility tools
│   │   │   │   ├── enclosed.yml               # Enclosed password manager
│   │   │   │   ├── atuin.yml                  # Shell history sync
│   │   │   │   └── karakeep.yml               # Karaoke library manager + MeiliSearch
│   │   │   │
│   │   │   └── oam/
│   │   │       ├── compose.yml                # Stack includes
│   │   │       ├── socket-proxy.yml           # Docker socket proxy
│   │   │       ├── watchtower.yml             # Container auto-updater
│   │   │       ├── portainer-agent.yml        # Portainer management agent
│   │   │       ├── dozzle-agent.yml           # Log aggregator agent
│   │   │       ├── docker-gc.yml              # Garbage collection
│   │   │       └── deunhealth.yml             # Health check monitor
│   │   │
│   │   ├── media-vm/                          # Media streaming and content management
│   │   │   ├── jelly/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── jellyfin.yml               # Media server
│   │   │   │   ├── jellyseerr.yml             # Media request UI
│   │   │   │   ├── jellystat.yml              # Usage statistics
│   │   │   │   ├── stash.yml                  # Adult content library
│   │   │   │   └── janitorr.yml               # Automated cleanup
│   │   │   │
│   │   │   ├── servarr/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── gluetun.yml                # VPN proxy for downloads
│   │   │   │   ├── deluge.yml                 # Torrent client
│   │   │   │   ├── prowlarr.yml               # Indexer manager
│   │   │   │   ├── radarr.yml                 # Movie manager
│   │   │   │   ├── sonarr.yml                 # TV show manager
│   │   │   │   ├── lidarr.yml                 # Music manager
│   │   │   │   ├── whisparr.yml               # Adult content manager
│   │   │   │   ├── bazarr.yml                 # Subtitle manager
│   │   │   │   ├── sabnzbd.yml                # Usenet downloader
│   │   │   │   ├── nzbget.yml                 # Usenet queue manager
│   │   │   │   ├── notifiarr.yml              # Notification hub
│   │   │   │   ├── flaresolverr.yml           # CloudFlare bypass
│   │   │   │   └── recyclarr.yml              # Config sync tool
│   │   │   │
│   │   │   └── oam/
│   │   │       └── (same as apps-vm/oam)
│   │   │
│   │   ├── obs-vm/                            # Observability and monitoring stack
│   │   │   ├── grafana/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── grafana.yml                # Grafana dashboards
│   │   │   │   ├── prometheus.yml             # Prometheus metrics
│   │   │   │   ├── loki.yml                   # Log aggregation
│   │   │   │   ├── prometheus-config.yml      # Prometheus targets
│   │   │   │   ├── loki-config.yaml           # Loki configuration
│   │   │   │   └── promtail-config.yaml       # Log shipping config
│   │   │   │
│   │   │   ├── graylog/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── graylog.yml                # Graylog server
│   │   │   │   ├── mongodb.yml                # Graylog backend
│   │   │   │   ├── datanode.yml               # Graylog data node
│   │   │   │   └── common.yml                 # Graylog shared config
│   │   │   │
│   │   │   ├── obs-apps/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   ├── gotify.yml                 # Push notifications
│   │   │   │   ├── uptime-kuma.yml            # Uptime monitoring
│   │   │   │   ├── portainer.yml              # Container management UI
│   │   │   │   └── socket-proxy.yml           # Docker socket proxy
│   │   │   │
│   │   │   ├── tick/
│   │   │   │   ├── compose.yml                # Stack includes
│   │   │   │   └── influxdb2.yml              # Time-series database
│   │   │   │
│   │   │   └── oam/
│   │   │       └── (same as apps-vm/oam)
│   │   │
│   │   ├── gateway-vps/
│   │   │   ├── pangolin/
│   │   │   │   ├── compose.yml                # Pangolin, Gerbil, Traefik, CrowdSec stack
│   │   │   │   ├── pangolin.yml               # Pangolin tunnel controller + Gerbil + Traefik
│   │   │   │   ├── middleware-manager.yml     # Traefik middleware definitions
│   │   │   │   ├── auth-bypass.yml            # Auth bypass service definitions
│   │   │   │   ├── beszel-agent.yml           # System monitor agent
│   │   │   │   ├── dozzle.yml                 # Log viewer (optional)
│   │   │   │   ├── config/
│   │   │   │   │   └── config.yml.j2          # Pangolin config (templated)
│   │   │   │   ├── traefik_static_config/     # Traefik static configuration
│   │   │   │   ├── traefik_rules/             # Traefik dynamic routing rules
│   │   │   │   │   ├── dynamic_config.yml     # Main rules (templated)
│   │   │   │   │   ├── resource-overrides.yml # Resource-specific overrides
│   │   │   │   │   └── bypass-routers.yml     # Auth bypass rules (generated)
│   │   │   │   └── mm_config/
│   │   │   │       ├── templates.yaml         # Middleware manager templates
│   │   │   │       └── templates_services.yaml # Service middleware mappings
│   │   │   │
│   │   │   ├── authentik/
│   │   │   │   ├── compose.yml                # Authentik server + PostgreSQL + worker
│   │   │   │   └── config/
│   │   │   │       └── custom-templates/      # Custom email/HTML templates
│   │   │   │
│   │   │   └── crowdsec/
│   │   │       └── config/crowdsec/           # CrowdSec configuration
│   │   │           ├── acquis.d/              # Acquisition rules
│   │   │           ├── parsers/               # Log parsing rules
│   │   │           ├── scenarios/             # Threat detection scenarios
│   │   │           ├── profiles.yaml          # Alert profile definitions
│   │   │           └── whitelists.yaml        # IP whitelists
│   │   │
│   │   └── playbooks/
│   │       ├── initial-ssh-setup.yml          # SSH key configuration (stub)
│   │       └── proxmox-base.yml               # Proxmox cluster setup (reference)
│   │
│   └── tests/
│       ├── suites/
│       │   ├── gateway_vps_test_suite.yml     # Full gateway testing (security, functionality, health)
│       │   └── homelab_vms_test_suite.yml     # Homelab VMs testing
│       │
│       ├── validation/
│       │   ├── container_standardization.yml  # Verify all services follow base patterns
│       │   └── crowdsec_firewall_bouncer.yml  # CrowdSec rules validation
│       │
│       ├── common/
│       │   ├── test_base.yml                  # Base test definitions
│       │   ├── test_config.yml                # Test configuration
│       │   ├── test_init.yml                  # Test framework initialization
│       │   └── test_recorder.yml              # Result recording utilities
│       │
│       ├── security_tests.yml                 # Auth bypass security validation
│       ├── security_test_*.yml                # Individual security tests
│       ├── functionality_tests.yml             # Service accessibility testing
│       ├── functionality_test_*.yml            # Individual functionality tests
│       ├── authentik_auth_tests.yml            # OpenID authentication testing
│       ├── crowdsec_bouncer_validation.yml    # IP blocking verification
│       ├── test_helpers.yml                   # Test utility functions
│       └── *.yml                              # Other test modules
│
├── guides/                                     # Documentation (Intel GPU, Authentik, backups)
├── images/                                     # Screenshots/diagrams
├── HOMELAB_SERVICES.md                         # Service inventory
├── CLAUDE.md                                   # Project instructions
└── README.md (implied)                         # Project overview
```

## Directory Purposes

**ansible/:**
- Purpose: Infrastructure-as-code orchestration
- Contains: Playbooks, roles, inventory, file templates
- Key files: `deploy_docker.yml`, `deploy_vps.yml`, `inventory.yml`

**ansible/roles/:**
- Purpose: Reusable Ansible patterns
- Contains: docker (install/deploy), pangolin (tunnel mgmt), crowdsec_firewall_bouncer (protection)

**ansible/files/common/:**
- Purpose: Shared service definitions used by all hosts
- Contains: Base stack templates, fallback service includes
- Key files: `newt/compose.yml` (tunnel client), `{stack}/compose.yml` (stack includes)

**ansible/files/{host}/:**
- Purpose: Host-specific service definitions
- Contains: Stack service files, configuration, data mounts
- Examples: `apps-vm/ai/litellm.yml`, `media-vm/jelly/jellyfin.yml`

**ansible/tests/:**
- Purpose: Pre-deployment validation
- Contains: Test playbooks, helpers, result recording
- Key files: `gateway_vps_test_suite.yml`, `homelab_vms_test_suite.yml`

**guides/:**
- Purpose: Operational procedures and investigations
- Contains: Intel GPU passthrough, Authentik migration, backup strategies

## Key File Locations

**Entry Points:**
- `ansible/deploy_docker.yml`: Deploy homelab VMs (NFS mount, Docker setup, all stacks)
- `ansible/deploy_vps.yml`: Deploy gateway VPS (Pangolin, Authentik, CrowdSec)
- `ansible/provision.yml`: Initial VM setup (hostname, utilities)
- `ansible/tests/suites/gateway_vps_test_suite.yml`: Test gateway infrastructure

**Configuration:**
- `ansible/inventory.yml`: Host groups, vars, credentials (all from 1Password)
- `ansible/group_vars/all.yml`: Global variables (paths, UIDs, timezones)
- `ansible/host_vars/px-cpu.yml`: Proxmox-specific overrides

**Core Logic:**
- `ansible/roles/docker/tasks/deploy_stack.yml`: Stack deployment (compose generation + execution)
- `ansible/roles/pangolin/tasks/resource_management.yml`: Pangolin API calls for tunnel setup
- `ansible/roles/pangolin/tasks/auth_bypass.yml`: Auth bypass rule generation

**Service Definitions:**
- `ansible/files/common.yml`: Base service patterns (extends, environment, security)
- `ansible/files/{host}/{stack}/compose.yml`: Stack includes (list of services)
- `ansible/files/{host}/{stack}/{service}.yml`: Individual service definitions

**Testing:**
- `ansible/tests/test_helpers.yml`: Test framework utilities
- `ansible/tests/security_tests.yml`: Auth/bypass validation
- `ansible/tests/functionality_tests.yml`: Service accessibility checks

## Naming Conventions

**Files:**
- Playbooks: `{verb}_{noun}.yml` (deploy_docker.yml, provision.yml)
- Roles: `{infrastructure_component}` (docker, pangolin, crowdsec_firewall_bouncer)
- Service files: `{service_name}.yml` (litellm.yml, jellyfin.yml, radarr.yml)
- Stack includes: `compose.yml` (collection of service includes for logical unit)
- Configuration: `{config_type}.yaml` or `{config_type}.yml` (prometheus-config.yml, loki-config.yaml)

**Directories:**
- Role directories: `{component_name}/` inside `roles/`
- Host-specific: `{inventory_hostname}/` (apps-vm, media-vm, obs-vm, gateway-vps)
- Stack directories: `{stack_name}/` (ai, dbs, oam, servarr, jelly, grafana, graylog, tick)
- Configuration subdirs: `config/`, `traefik_rules/`, `mm_config/`, `homepage-config/`

**Variable Naming:**
- Global: `docker_uid`, `docker_gid`, `docker_appdata_dir`, `docker_compose_dir`
- Stack-scoped: `env_vars[cur_stack]`, `docker_env_vars[stack_name]`
- Service-specific: Referenced in `.env` files, injected at runtime

## Where to Add New Code

**New Service/Stack:**

1. **For homelab VM (apps-vm, media-vm, obs-vm):**
   - Create directory: `ansible/files/{host}/{new_stack}/`
   - Create stack file: `ansible/files/{host}/{new_stack}/compose.yml` (include directives)
   - Create service files: `ansible/files/{host}/{new_stack}/{service}.yml` (each service)
   - Each service MUST extend `base` from `../common.yml`
   - Add stack to host's `stacks` list in `ansible/inventory.yml`
   - Generate environment vars: Add to `env_vars[new_stack]` in inventory or group_vars

2. **For gateway VPS (gateway-vps):**
   - Create directory: `ansible/files/gateway-vps/{new_stack}/`
   - Create files per above pattern
   - Add to `stacks` list in gateway-vps host definition
   - If using Traefik routing: Add rules to `traefik_rules/dynamic_config.yml`
   - If requiring auth bypass: Add service to `roles/pangolin/vars/auth_bypass.yml`

**New Role:**

- Location: `ansible/roles/{component_name}/`
- Structure: Follow Ansible role layout (tasks/, defaults/, handlers/, templates/, vars/)
- Entry point: `tasks/main.yml`
- Include from playbooks using `- role: {component_name}`

**New Test:**

- Location: `ansible/tests/{test_category}.yml` or `ansible/tests/suites/{suite_name}.yml`
- Pattern: Include from suite playbook, register results in test framework
- Use test_helpers.yml for assertions and result recording

## Special Directories

**ansible/files/gateway-vps/pangolin/traefik_rules/:**
- Purpose: Traefik dynamic routing configuration
- Generated: `bypass-routers.yml` is generated by deploy_vps.yml post_tasks
- Committed: `dynamic_config.yml`, `resource-overrides.yml` are committed

**ansible/files/{host}/{stack}/config/:**
- Purpose: Service-specific configuration files
- Generated: Some templated during deployment (pangolin/config.yml.j2 → config.yml)
- Committed: Static config files checked in (prometheus.yml, litellm-config.yaml)

**ansible/tests/**
- Purpose: Infrastructure validation before deployment
- Generated: `/tmp/infrastructure_test_results.json` saved after test run
- Committed: Test playbooks and helpers are committed

**docker_appdata_dir (/opt/docker/appdata):**
- Purpose: Persistent application data
- Generated: Created by Docker role setup phase, populated by compose deploy
- Committed: Not tracked (runtime data)

**docker_compose_dir (/opt/docker/compose):**
- Purpose: Deployed compose files and environment
- Generated: Created at runtime, .env files generated per stack
- Committed: Not tracked (generated from templates)

**docker_logs_dir (/opt/docker/logs):**
- Purpose: Centralized container logs
- Generated: Created by Docker role, populated by services
- Committed: Not tracked (logs)
