# Coding Conventions

**Analysis Date:** 2026-02-05

## Naming Patterns

**Files:**
- YAML playbooks: `lowercase_with_underscores.yml` (e.g., `deploy_docker.yml`, `security_tests.yml`)
- Docker Compose: `service_name.yml` (e.g., `litellm.yml`, `jellyfin.yml`)
- Ansible roles: `role_name/` with standard structure: `tasks/`, `handlers/`, `templates/`, `defaults/`, `vars/`, `meta/`, `roles/`
- Test files: `<type>_test_<subject>.yml` (e.g., `security_test_invalid_key.yml`, `functionality_test_bypass.yml`)
- Test helpers: `common/<function_name>.yml` (e.g., `common/test_base.yml`, `common/test_recorder.yml`)
- Configuration: `*.cfg`, `*.yml`, `*.yaml`, `config.yaml`, `config.json`
- Templates: `*.j2` (Jinja2 templates in role `templates/` directories)

**Ansible Variables:**
- snake_case for all variable names (e.g., `docker_appdata_dir`, `ansible_host`, `pangolin_newt_enabled`)
- PascalCase for environment variables read from 1Password (e.g., `TRAEFIK_AUTH_BYPASS_KEY`, `AUTHENTIK_SECRET_KEY`)
- Environment variable names: UPPERCASE_WITH_UNDERSCORES (e.g., `PUID`, `PGID`, `TZ`, `DOCKER_HOST`)
- Grouped variables: `dict_name.property_access` (e.g., `docker_env_vars.common`, `test_categories.security`)
- Loop variables: descriptive names (e.g., `loop_var: target_service`, `loop_var: cur_stack`)

**Task Names:**
- Clear, human-readable descriptions starting with action verb
- Format: `[Action] [what] [condition if needed]` (e.g., `Set test context`, `Execute HTTP test with invalid key`, `Deploy docker apps`)
- Security-sensitive tasks use clear intent (e.g., `Test invalid bypass key is blocked`)

**Service/Container Names:**
- container_name: lowercase (e.g., `litellm`, `litellm_db`, `litellm_prometheus`)
- stack names: lowercase (e.g., `oam`, `ai`, `tools`, `dbs`, `servarr`, `jelly`)
- hostname references: dot notation for domain access (e.g., `apps.lan`, `media.lan`, `grafana.lab.nobasura.org`)

## Code Style

**Formatting:**
- YAML linting: ansible-lint enabled (no violations reported)
- Config: `ansible/ansible.cfg` controls formatting behavior
- YAML indentation: 2 spaces (standard Ansible convention)
- Line continuations: backslash `\` for long commands (see `deploy_docker.yml` NFS mount options)
- Comment style: `# [space] comment text` on separate lines above relevant code

**Linting:**
- Tool: `ansible-lint`
- Configuration: No custom config file (uses Ansible defaults)
- Status: Zero violations enforced (verified in CLAUDE.md)
- Run before commits: `ansible-lint ansible/`

**Comments and Documentation:**
- Header comments on playbooks: describe purpose, usage examples, and tag options
- File-level documentation: explain scope and context (e.g., "Production-grade test suite...")
- Section comments: mark major logical sections with blank line before comment
- No redundant comments: code should be self-explanatory; comments explain "why", not "what"
- Test comments: include expected outcomes and conditions (e.g., "Production-grade security test using standardized patterns")

## Import Organization

**Include/Import Order:**
1. Variables (vars, include_vars)
2. Tasks from common libraries or helpers
3. Role-specific tasks
4. Integration with other components

**Example Pattern from playbooks:**
```yaml
pre_tasks:
  - name: Load auth bypass variables
    include_vars: "../../roles/pangolin/vars/auth_bypass.yml"
    tags: ["always"]

  - name: Verify test prerequisites
    block:
      # Prerequisites verification

tasks:
  - name: Initialize test framework
    include_tasks: ../test_helpers.yml
    tags: ["always"]

  - name: Security Validation Tests
    include_tasks: ../security_tests.yml
    tags: ["security", "critical", "smoke", "always"]
```

**Path Usage:**
- Relative paths: `../` for parent directories within playbook context
- Absolute playbook paths: Full paths in `ansible_playbook` commands
- Variable interpolation: `{{ variable_name }}` for dynamic path construction

## Task Design

**Task Structure:**
- Each task performs one logical unit of work
- Use `block` for grouping related tasks with common conditions/error handling
- Set facts for intermediate results that multiple tasks consume
- Use `include_tasks` to organize complex logic into separate files

**Conditional Logic:**
- `when:` clauses check variables, facts, or previous results
- `when: <var> is defined` for optional configuration
- Complex conditions: use `vars:` block to calculate intermediate values
- Default values: `variable | default(fallback_value)`

**Error Handling:**
- `ignore_errors: true` for non-critical checks (e.g., version checks)
- `changed_when: false` for read-only operations (e.g., `command` module used for queries)
- `failed_when: false` for soft failures that need explicit handling
- `block` with `rescue` for exception-like handling in Ansible

**Looping:**
- `loop:` with `loop_control.loop_var:` to name loop variables clearly
- Example: `loop: "{{ test_services.auth_bypass }}"` with `loop_var: target_service`

## Module Usage Patterns

**URI Module (HTTP Testing):**
```yaml
uri:
  url: "{{ test_config.url }}"
  method: "{{ test_config.method | default('GET') }}"
  headers: "{{ headers_dict }}"
  follow_redirects: "{{ test_config.follow_redirects | default('none') }}"
  status_code: "{{ test_config.expected_statuses | default([200]) }}"
  timeout: "{{ test_config.timeout }}"
  return_content: "{{ test_config.return_content | default(false) }}"
register: http_result
ignore_errors: true
```

**Facts & Set Facts:**
- Use `set_fact` for calculated values consumed by later tasks
- Dictionary merging with `|combine()`: merge multiple dicts into final configuration
- Facts persist across task executions within same play

**Copy/Template Modules:**
- Create directories with separate `file` task before copying content
- Preserve file ownership/permissions with `owner:`, `group:`, `mode:` parameters
- Template variables: use `{{ variable }}` syntax in .j2 template files

## Docker/Container Conventions

**Compose File Structure:**
- Header comment: brief description and any special notes
- Services section: includes from base service definitions
- Extends pattern: `extends: { file: ../common.yml, service: base }` for inheritance
- Environment variables: inline or via `env_file:`
- Health checks: always included with standardized format
- Labels: for orchestration tools (e.g., `deunhealth.restart.on.unhealthy`)
- Volumes: named volumes with `driver: local`
- Dependencies: explicit with `depends_on:`

**Service Base Definitions:**
- Location: `ansible/files/common.yml` shared by all homelab VMs
- Base service: provides security, restart policy, environment, volumes
- Socket-base service: adds Docker socket proxy networking for privileged operations
- All services MUST extend base or socket-base (mandatory pattern)

**Port Mapping:**
- Internal port: service default (e.g., `:3000`, `:8080`)
- Host port: explicitly mapped (e.g., `"4000:4000"`)
- Configuration: via environment variables or config files

## Environment Configuration

**Secrets Management:**
- Source: 1Password via `lookup('community.general.onepassword', ...)`
- Location: `ansible/inventory.yml` in `env_vars` sections
- Format: `LOOKUP_NAME` in 1Password, mapped to environment variable
- No log: `no_log: true` on sensitive lookups
- Vault: All secrets in 'Homelab' vault

**Environment Variable Categories:**
- `docker_env_vars.common`: PUID, PGID, TZ, UMASK, LOG_LEVEL (all services)
- Stack-specific: nested under stack name (e.g., `env_vars.ai`, `env_vars.dbs`)
- Host-specific overrides: in `env_vars:` section of host inventory

## Vault/Secrets Access

**1Password Lookup Pattern:**
```yaml
"{{ lookup('community.general.onepassword', 'VAULT_ITEM_NAME', vault='Homelab') }}"
```

**Community Plugin Required:**
- Plugin: `community.general.onepassword`
- Must be installed: `ansible-galaxy collection install community.general`
- Authentication: requires `op` CLI logged in before playbook execution

## Version Management

**Ansible Version Requirements:**
- Minimum: Ansible 2.9+ (for native jinja2 types)
- Configuration: `jinja2_native` is default (no explicit config needed per comments)
- Python interpreter: `auto_silent` (auto-detect without warnings)

## Standards Enforcement

**Mandatory Patterns:**
- Docker compose services MUST extend `base` or `socket-base` from `common.yml`
- Test files MUST use standardized test framework (test_base.yml, test_recorder.yml)
- All variable references in templates MUST use `{{ variable }}` syntax
- All plays MUST include appropriate tags for filtering (smoke, security, functionality, critical, always)

**Pre-commit Checklist:**
- Run `ansible-lint ansible/` (zero violations required)
- Run appropriate test suite based on changes
- Verify all secret lookups use 1Password correctly
- Check that new containers extend base services

---

*Convention analysis: 2026-02-05*
