---
title: Ansible Environment Variable Management Patterns
type: note
permalink: patterns/ansible-environment-variable-management-patterns
---

# Ansible Environment Variable Management Patterns

## Overview

The Ansible setup uses a hierarchical environment variable management system with multiple layers of configuration that get merged during deployment.

## Environment Variable Architecture

### 1. Common Base Variables (`common.yml`)

```yaml
# /ansible/files/common.yml
services:
  base:
    environment:
      - PUID=$PUID
      - PGID=$PGID  
      - TZ=$TZ
      - UMASK=$UMASK
      - LOG_LEVEL=$LOG_LEVEL
  socket-base:
    environment:
      - DOCKER_HOST=tcp://socket-proxy:2375
```

### 2. Global Docker Environment Variables (`inventory.yml`)

```yaml
# Set at group level for all docker hosts
vars:
  docker_env_vars:
    common:
      PUID: "1001"
      PGID: "1001" 
      TZ: "Europe/London"
      UMASK: "022"
      LOG_LEVEL: "info"
      APP_DATA: "/opt/docker/appdata"
    oam:
      WT_GOTIFY_TOKEN: "{{ lookup('community.general.onepassword', 'WT_GOTIFY_TOKEN', vault='Homelab') }}"
```

### 3. Host-Specific Environment Variables

```yaml
# In inventory.yml for each host
hosts:
  apps-vm:
    env_vars:
      ai:
        LITELLM_DB_USER: llmproxy
        LITELLM_DB_PASS: "{{ lookup('community.general.onepassword', 'LITELLM_DB_PASS', vault='Homelab') }}"
        OPENAI_API_KEY: "{{ lookup('community.general.onepassword', 'OpenAiApiKey', vault='Homelab') }}"
      tools:
        ATUIN_DB_USER: atuin
        FIRECRAWL_API_KEY: "{{ lookup('community.general.onepassword', 'FIRECRAWL_API_KEY', vault='Homelab') }}"
```

### 4. Gateway VPS Environment Variables  

```yaml
# Gateway VPS has its own env_vars section
gateway-vps:
  env_vars:
    pangolin:
      DOMAIN: pangolin.nobasura.org
      CLOUDFLARE_API_TOKEN: "{{ lookup('community.general.onepassword', 'CLOUDFLARE_API_TOKEN', vault='Homelab') }}"
      PANGOLIN_ROOT_API_KEY: "{{ lookup('community.general.onepassword', 'PANGOLIN_ROOT_API_KEY', vault='Homelab') }}"
```

## Environment Variable Merging Process

The `deploy_stack.yml` task merges environment variables in this priority order:

```yaml
stack_env_vars: >-
  {{ docker_env_vars.common | combine(
    docker_env_vars[cur_stack] | default({}),
    env_vars.common | default({}),
    env_vars[cur_stack] | default({})
  ) }}
```

**Priority Order (highest to lowest):**
1. `env_vars[stack_name]` - Host+stack specific
2. `env_vars.common` - Host-level common
3. `docker_env_vars[stack_name]` - Global stack-specific  
4. `docker_env_vars.common` - Global common

## .env File Generation

The deployment process generates a `.env` file for each stack:

```yaml
- name: Generate env file {{ cur_stack }}
  copy:
    content: |
      {% for key, value in stack_env_vars.items() %}
        {{ key }}={{ value }}
      {% endfor %}
    dest: "{{ docker_compose_dir }}/{{ cur_stack }}/.env"
    mode: "0664"
```

## Usage in Docker Compose Files

### Using .env File Variables
```yaml
# Service references variables from .env file
environment:
  DATABASE_URL: "postgresql://${LITELLM_DB_USER}:${LITELLM_DB_PASS}@db:5432/litellm"
  POSTGRES_USER: ${LITELLM_DB_USER}
  POSTGRES_PASSWORD: ${LITELLM_DB_PASS}

env_file:
  - .env # Load local .env file
```

### Direct Environment Variables
```yaml
# Some services define environment directly
environment:
  AUTHENTIK_REDIS__HOST: redis
  AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
  AUTHENTIK_EMAIL__FROM: auth@nobasura.org
```

## Secret Management

Secrets are managed through 1Password lookups:

```yaml
# Secrets retrieved from 1Password vault
LITELLM_MASTER_KEY: "{{ lookup('community.general.onepassword', 'LITELLM_MASTER_KEY', vault='Homelab') }}"
OPENAI_API_KEY: "{{ lookup('community.general.onepassword', 'OpenAiApiKey', vault='Homelab') }}"
```

## Key Patterns

### 1. Stack Organization
- Variables grouped by stack name (ai, tools, pangolin, etc.)
- Stack-specific variables override global ones

### 2. Common Variables
- Standard variables (PUID, PGID, TZ) defined globally
- Service-specific secrets defined per stack

### 3. Host Separation  
- Each VM host has its own env_vars section
- Gateway VPS has separate configuration

### 4. Security
- All secrets pulled from 1Password
- No hardcoded secrets in configuration files
- .env files generated at deploy time

## Example Stack Configuration

For LiteLLM service on apps-vm:
1. Inherits: PUID, PGID, TZ from `docker_env_vars.common`
2. Gets: LITELLM_DB_USER, LITELLM_DB_PASS from `env_vars.ai`
3. Uses: Variables in compose via `${VARIABLE_NAME}` syntax
4. Loads: All variables from generated `.env` file

This creates a flexible, secure, and maintainable environment variable management system across the entire infrastructure.