# Architecture

**Analysis Date:** 2026-02-05

## Pattern Overview

**Overall:** Ansible-driven infrastructure-as-code with multi-host Docker orchestration across a hybrid homelab (private VMs) and external gateway (VPS).

**Key Characteristics:**
- Declarative infrastructure automation using Ansible playbooks and roles
- Docker Compose-based service deployment organized into logical stacks
- Multi-environment deployment: homelab (direct LAN + Caddy) and gateway VPS (external with Traefik)
- Infrastructure-as-code with secret management via 1Password lookup
- Testable infrastructure with comprehensive test suites before deployment
- Service hierarchy: base container patterns extend to specialized stacks

## Layers

**Orchestration Layer:**
- Purpose: Hosts, inventory management, playbook execution
- Location: `ansible/inventory.yml`, `ansible/deploy_docker.yml`, `ansible/deploy_vps.yml`, `ansible/provision.yml`
- Contains: Inventory definitions (groups, host vars, credentials), deployment triggers
- Depends on: Ansible runtime, SSH access to hosts, 1Password CLI
- Used by: All infrastructure deployment workflows

**Role Layer:**
- Purpose: Reusable infrastructure patterns (Docker setup, Pangolin tunnel management, CrowdSec firewall)
- Location: `ansible/roles/{docker,pangolin,crowdsec_firewall_bouncer}/`
- Contains: Task orchestration, handlers, templates, defaults, variable schemas
- Depends on: Ansible core modules, Docker runtime, external APIs (Pangolin, CrowdSec)
- Used by: Playbooks to apply configurations idempotently

**Service Definition Layer:**
- Purpose: Docker Compose definitions for containerized services
- Location: `ansible/files/{inventory_hostname}/{stack_name}/` and `ansible/files/common/`
- Contains: Service definitions, networking, volumes, environment configuration patterns
- Depends on: Docker Compose, base image definitions from `common.yml`
- Used by: Docker role to deploy stacks to target hosts

**Configuration Layer:**
- Purpose: Environment variables, secrets, feature toggles
- Location: `ansible/group_vars/`, `ansible/host_vars/`, generated at runtime in `.env` files
- Contains: Global settings (docker_uid, docker_gid, paths), service-specific environment, secret references
- Depends on: 1Password vault integration, host-specific overrides
- Used by: Service containers and deployment tasks

**Testing Layer:**
- Purpose: Validation before deployment (security, functionality, health)
- Location: `ansible/tests/suites/`, `ansible/tests/validation/`, `ansible/tests/`
- Contains: Test playbooks, assertions, result recording
- Depends on: Deployed infrastructure, network access to services
- Used by: Pre-commit validation workflow

## Data Flow

**Deployment Flow:**

1. User triggers deployment playbook (`deploy_docker.yml` or `deploy_vps.yml`)
2. Ansible loads inventory (`inventory.yml`) with host groups and variables
3. 1Password lookups retrieve secrets during variable resolution
4. Docker role setup phase: installs Docker, creates directories, validates environment
5. Docker role deploy phase iterates through host stacks:
   - Generates `.env` file combining global + host + stack variables
   - Copies `common.yml` base service definitions
   - Copies stack-specific service files (e.g., `apps-vm/ai/litellm.yml`)
   - Templates any Pangolin configurations if `cur_stack == 'pangolin'`
   - Executes `docker compose` with merged configuration
6. Post-deployment tasks run role-specific handlers (Pangolin auth bypass, CrowdSec registration)
7. Test suite validates deployment state (optional pre-commit workflow)

**Service Composition Pattern:**

```
Stack (e.g., "ai")
  ├─ compose.yml (include directive)
  │   └─ Includes: litellm.yml, openwebui.yml, etc.
  ├─ litellm.yml
  │   └─ service: litellm (extends base from common.yml)
  │       └─ Depends on: db service, networks, volumes
  ├─ prometheus.yml
  │   └─ service: prometheus (extends base from common.yml)
  ├─ .env (generated at runtime)
  │   └─ Contains: PUID, PGID, TZ, stack-specific keys
  └─ config/ (optional)
      └─ litellm-config.yaml, etc.
```

**State Management:**

- **Persistent Data:** Docker named volumes (postgres_data, letsencrypt, gerbil, crowdsec_db)
- **Configuration:** Mounted files from `docker_appdata_dir` (`/opt/docker/appdata`)
- **Logs:** Centralized in `docker_logs_dir` (`/opt/docker/logs/`)
- **Infrastructure State:** Pangolin stores in SQLite (`pangolin_db:/app/config/db`)
- **Secret State:** 1Password vault acts as source-of-truth, never stored in repo

## Key Abstractions

**Host Group (docker, gateway, proxmox):**
- Purpose: Logical grouping of similar infrastructure (homelab VMs, external VPS, hypervisors)
- Examples: `docker` group (apps-vm, media-vm, obs-vm), `gateway` group (gateway-vps)
- Pattern: Inherited variables, role application, stack definitions per host

**Stack (oam, ai, servarr, jelly, pangolin, authentik, etc.):**
- Purpose: Logical grouping of related services deployed as atomic unit
- Examples: `oam` (operations/administration: docker-gc, watchtower, portainer-agent, dozzle), `servarr` (media stack)
- Pattern: Compose file with includes, shared environment, common networking

**Service Extension Pattern:**
- Purpose: Enforce consistent base configuration across all containers
- Example: Services extend `base` or `socket-base` from `common.yml`
- Base service provides: security settings, restart policy, standard environment (PUID, PGID, TZ), timezone mounting
- Socket-base adds: network proxy connectivity via socket-proxy for secure Docker API access

**Pangolin Tunnel Infrastructure:**
- Purpose: Secure VPN tunnel management for service exposure from internal homelab to external VPS
- Abstractions: Resources (service definitions), Sites (infrastructure endpoints), Organizations, Hosts
- Pattern: Declarative resource definitions via API, Newt client (tunnel endpoint), dynamic Traefik routing

**CrowdSec Protection Layer:**
- Purpose: Threat detection and IP-based bouncing for SSH and HTTP
- Abstractions: Collections (detection rules), Bouncers (enforcement engines: Traefik, Firewall)
- Pattern: Enrollment-based registration, scenario-driven rules, whitelist protection for admin IPs

## Entry Points

**deploy_docker.yml:**
- Location: `ansible/deploy_docker.yml`
- Triggers: Manual execution or pre-commit workflow
- Responsibilities:
  - Mount NFS data (media-vm only)
  - Apply Docker role to all docker group hosts
  - Deploy all configured stacks per host

**deploy_vps.yml:**
- Location: `ansible/deploy_vps.yml`
- Triggers: Manual execution or pre-commit workflow
- Responsibilities:
  - Create directory structure for Pangolin and Authentik
  - Apply Docker role to gateway-vps
  - Generate auth bypass router configuration
  - Register CrowdSec bouncers (Traefik + Firewall)

**provision.yml:**
- Location: `ansible/provision.yml`
- Triggers: Initial infrastructure setup
- Responsibilities:
  - Set hostnames on all docker group hosts
  - Install system utilities (git, wget, curl, neovim, ripgrep, zoxide)

**Docker Role (Core Orchestrator):**
- Location: `ansible/roles/docker/tasks/main.yml`
- Triggers: Called from deployment playbooks
- Responsibilities:
  - Execute setup.yml for infrastructure validation
  - Iterate through host's configured stacks
  - Deploy each stack by templating compose files
  - Handle service lifecycle (down, up)

## Error Handling

**Strategy:** Fail-fast with detailed error messages, idempotent where possible, manual intervention recovery.

**Patterns:**

- **Task Failure:** Ansible assertions validate prerequisites before execution
- **Service Health:** Docker healthchecks on critical services (litellm, authentik, pangolin, crowdsec)
- **Deployment Rollback:** docker compose down removes failed stacks; re-run playbook to retry
- **Test Validation:** Pre-commit test suites block deployment on critical failures (`test_exit_code`)
- **API Errors:** URI module calls check status_code, fail_when validates response
- **Recovery:** Manual docker commands available for emergency service restart (documented in CLAUDE.md)

## Cross-Cutting Concerns

**Logging:**
- Host-level: Centralized in `/opt/docker/logs/` mounted to containers
- Container-level: Each service logs to stdout/stderr, captured by Docker
- Aggregation: Dozzle (agent on each VM), Graylog/Loki (ELK-like stack on obs-vm)

**Validation:**
- Ansible variables: Pre-task assertions verify required vars are defined
- Service startup: Healthchecks with exponential backoff (interval 30s, retries 3-15)
- Deployment: Post-task test suites validate auth flows, service accessibility, security rules

**Authentication:**
- Service-level: Authentik (OpenID provider for Karakeep, internal services)
- Infrastructure-level: Pangolin auth bypass for static routes (API keys per service)
- VPN-level: Newt (Pangolin client) tunnel authentication, WireGuard keys managed in inventory
- Secret Storage: 1Password vault with lookup plugins during Ansible execution

**Authorization:**
- Container permissions: PUID/PGID injection for consistent file ownership
- Docker socket access: Socket-proxy restricts API methods (no AUTH, SECRETS, BUILD)
- Traefik routing: Middleware manager enforces auth rules, CrowdSec bouncer blocks malicious IPs

**Networking:**
- Homelab VMs: Direct .lan addresses + internal Caddy reverse proxy for .lab.nobasura.org
- Gateway VPS: External Traefik + Gerbil (WireGuard) for .nobasura.org services
- Inter-service: Docker bridge networks per stack, socket-proxy network for privileged access
- DNS: OpnSense Unbound forwards homelab domains, external DNS for vps

**Resource Management:**
- Allocation: No explicit CPU/memory limits defined (uses host defaults)
- Persistence: Named volumes for databases, mounted paths for config files
- Cleanup: Docker-gc (runs daily) removes unused images and containers
- Monitoring: Prometheus scrapes metrics, Grafana visualizes resource usage
