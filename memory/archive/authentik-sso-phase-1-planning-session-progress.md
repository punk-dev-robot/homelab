---
title: Authentik SSO Phase 1 Planning Session Progress
type: note
permalink: decisions/authentik-sso-phase-1-planning-session-progress
---

# Authentik SSO Phase 1 Planning Session Progress

## Session Context
- **Date**: June 18, 2025
- **Project**: Implementing Authentik SSO for homelab infrastructure
- **Current Branch**: feat (authentik implementation)
- **Status**: Planning phase - architecture decisions being made

## Key Decisions Made

### 1. **Primary Requirement**: External Access SSO
- Need SSO for external access via .nobasura.org domains
- Current system uses Pangolin for tunnel/proxy management
- Goal: Add modern identity management with OIDC capability

### 2. **Architecture Decision**: Authentik as Identity Provider for Pangolin
- **Approach**: Use Authentik as identity provider for Pangolin (not replacing Pangolin)
- **Authentication Flow**: User → Pangolin login → Authentik auth → Pangolin session → Service
- **Benefit**: Keeps Pangolin's excellent tunneling + adds Authentik's identity features

### 3. **Location Decision**: Gateway VPS Deployment
- **Deployment**: Authentik on gateway VPS at `auth.nobasura.org`
- **Reason**: Optimal performance, no homelab dependency for external auth
- **Architecture**: All external authentication infrastructure on secure gateway VPS

### 4. **Dual OIDC Capability Requirement** 
- **Problem**: Pangolin SSO doesn't support direct OIDC for applications
- **Solution**: Authentik provides both:
  1. Identity provider for Pangolin (web users)
  2. Direct OIDC for applications (Jellyfin, Nextcloud, etc.)

### 5. **Stack Architecture Discussion**
Two approaches under consideration:

#### Option A: Separate Authentik Docker Stack
- Independent docker-compose stack for Authentik
- Inter-stack communication via Docker networks
- Clean separation of concerns

#### Option B: Authentik as Pangolin Site (Preferred)
- Authentik runs as services on gateway VPS
- Pangolin manages `auth.nobasura.org` as "local connection" site
- Similar to current midman service pattern
- Follows existing monorepo patterns

## Current Gateway VPS Architecture

### Existing Components
- **CrowdSec**: Multi-layer threat protection
- **Traefik**: External routing and SSL termination  
- **Pangolin**: Single Sign-On tunnel management
- **Services**: All external .nobasura.org access

### Integration Points
- **CrowdSec Protection**: Authentik gets automatic protection
- **Traefik Integration**: Routes `auth.nobasura.org` to Authentik
- **Pangolin Integration**: Uses Authentik for identity provider
- **Network**: All on same VPS for optimal performance

## Technical Requirements Identified

### 1. **Infrastructure Setup**
- Redis (session caching)
- PostgreSQL (user database)
- Authentik server + worker
- Domain: `auth.nobasura.org`

### 2. **Integration Points**
- **Pangolin OIDC**: Configure Authentik as identity provider
- **Auto-provisioning**: Map Authentik groups to Pangolin roles
- **Direct OIDC**: Applications connect directly to Authentik

### 3. **Jellyfin Integration Plan**
```yaml
# Triple access pattern for Jellyfin
1. Mobile/API: Bypass headers (unchanged)
2. Direct OIDC: App → Authentik → Direct access  
3. Web: Pangolin → Authentik → Pangolin session → Jellyfin
```

### 4. **User Management Structure**
```yaml
groups:
  - homelab-admin: Full administrative access
  - homelab-users: Standard user access
  - family: Family member privileges  
  - friends: Limited friend access
```

## Next Steps to Resolve

### 1. **Deployment Pattern Decision**
- Need to examine current midman setup as example
- Understand existing monorepo patterns for service deployment
- Choose between separate stack vs Pangolin site approach

### 2. **Secret Management Integration**
- Use existing 1Password + Ansible patterns
- Follow monorepo conventions for secret handling
- Generate required secrets (DB password, Authentik secret key, OIDC credentials)

### 3. **Implementation Planning**
- Create Ansible playbook following existing patterns
- Define deployment steps and testing procedures
- Plan rollback strategy and emergency access

## Research Completed

### Documentation Sources
- Authentik official documentation and guides
- Pangolin identity provider configuration docs
- HomeServer tutorials and deployment guides
- Current homelab architecture documentation

### Key Findings
- Authentik + Pangolin integration is well-supported
- OIDC auto-provisioning provides flexible user management
- Gateway VPS deployment optimal for external authentication
- Can maintain existing dual access patterns (web + mobile/API)

## Session Status
- **Planning Phase**: Architecture decisions 95% complete
- **Next Session**: Finalize deployment approach and begin implementation
- **Implementation Ready**: Once deployment pattern is chosen

---

*Session saved for continuation of Authentik SSO Phase 1 implementation*