---
title: Enclosed Service Implementation
type: note
permalink: patterns/enclosed-service-implementation
---

# Enclosed Service Implementation

## Service Overview
- **Purpose**: End-to-end encrypted note and file sharing service
- **Location**: `apps-vm` in `tools` category
- **Port**: `8787:8787` (following homelab rule to reuse service default port)
- **Image**: `corentinth/enclosed:latest`

## Key Features
- End-to-end encryption with AES-GCM 256-bit
- Zero knowledge server architecture
- File attachment support
- Optional password protection and TTL
- Self-destruct after reading option
- Minimalistic UI with dark mode support
- Very lightweight (single container)

## Container Configuration
```yaml
services:
  enclosed:
    extends:
      file: ../common.yml
      service: base
    image: corentinth/enclosed:latest
    container_name: enclosed
    ports:
      - "8787:8787"
    labels:
      - "deunhealth.restart.on.unhealthy=true"
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8787/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

## Access Methods
- **Direct**: `http://apps.lan:8787`
- **Caddy Proxy**: `https://enclosed.lab.nobasura.org`

## Implementation Details
- **Files Created**: `/ansible/files/apps-vm/tools/enclosed.yml`
- **Files Modified**: `/ansible/files/apps-vm/tools/compose.yml`
- **Architecture**: Extends `base` service (standard application, no Docker socket access)
- **Security**: Standard homelab security practices applied
- **Health Monitoring**: Integrated with deunhealth for automatic restart on failure

## Deployment Status
- ✅ Service definition created
- ✅ Compose file updated
- ✅ Test framework validated
- 🔄 Ready for deployment via `ansible-playbook -i inventory.yml site.yml`

## Benefits
- Privacy-focused alternative to cloud note-sharing services
- Perfect for homelab users needing secure ephemeral communication
- Lightweight resource usage
- Zero maintenance overhead
- Follows established infrastructure patterns