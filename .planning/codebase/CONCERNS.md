# Codebase Concerns

**Analysis Date:** 2026-02-05

## Tech Debt

**Newt Tunnel Automation Gap:**
- Issue: Pangolin role exists but is never called in deployment playbooks; newt tunnel containers are not deployed automatically
- Files: `ansible/roles/pangolin/`, `ansible/deploy_docker.yml`, `ansible/deploy_vps.yml`
- Impact: External tunnel connectivity for homelab VMs (apps-vm, media-vm, obs-vm) is not automated. Media-vm went offline June 19, 2025 because newt tunnel was missing entirely. Manual configuration is required and breaks on redeploy.
- Fix approach: Integrate pangolin role into `deploy_docker.yml` playbook or create dedicated tunnel deployment playbook that runs after docker deployment; ensure inventory flag `pangolin_newt_enabled` triggers actual tunnel creation

**Docker Role File Replacement During Deployment:**
- Issue: Docker role removes entire compose folder structure, wiping template-generated files like `bypass-routers.yml` that are created by post-task templates
- Files: `ansible/roles/docker/tasks/`, `ansible/deploy_vps.yml` post_tasks (lines 68-84)
- Impact: Auth bypass configuration gets destroyed during standard deployments. Current workaround requires running `--tags auth-bypass` AFTER full deployment and manually restarting Traefik. Creates fragile, multi-step deployment workflow.
- Fix approach: Modify docker role to preserve template-generated files in traefik_rules directory, or restructure workflow to generate templates BEFORE docker deployment, or separate docker deployment from traefik configuration management

**Incomplete Authentik Upgrade Path Documentation:**
- Issue: Authentik currently running 2024.12.2 with notes indicating critical upgrade needed to 2025.10.1. Upgrade requires sequential version progression through 5 major versions with multiple breaking changes (Redis removal, PostgreSQL requirements, OAuth claim defaults).
- Files: `ansible/files/gateway-vps/authentik/compose.yml`, `guides/Authentik Upgrade Analysis 2024.12 to 2025.10.md`
- Impact: Production SSO service at risk. Both authentik-server and authentik-worker containers showing UNHEALTHY status pre-upgrade (noted in upgrade analysis). Redis will need to be removed completely in 2025.10 requiring careful migration planning.
- Fix approach: Plan and execute Authentik upgrade following sequential path (2025.2 → 2025.4 → 2025.6 → 2025.8 → 2025.10); create pre-upgrade validation checklist; test Redis removal impact on PostgreSQL connection limits; validate all integrated applications work with new OAuth claim defaults

## Known Bugs

**Auth Bypass Configuration Loss on Gateway VPS Deployment:**
- Symptoms: All 9 services using auth bypass (bypassed services lose external access) after running `ansible-playbook deploy_vps.yml`
- Files: `ansible/deploy_vps.yml` (lines 7-9 docker role removes pangolin folder), `ansible/roles/pangolin/tasks/`, `ansible/files/gateway-vps/pangolin/traefik_rules/bypass-routers.yml`
- Trigger: Full deployment of VPS stack without subsequent auth bypass template regeneration
- Workaround: Run `ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml --tags auth-bypass` then `docker compose restart traefik` in gateway-vps pangolin folder

**Media-VM External Access Broken (Tunnel Missing):**
- Symptoms: Media site shows "Offline" in Pangolin UI despite apps and obs showing "Online"
- Files: `ansible/inventory.yml` (pangolin_newt_enabled flag), `ansible/roles/pangolin/` (never called), media-vm docker containers
- Trigger: VM redeploy or fresh bootstrap - pangolin role never deployed, no newt tunnel container created
- Workaround: Manually deploy newt tunnel container to media-vm with correct credentials from 1Password

**Container Health Status Inconsistency:**
- Symptoms: Authentik containers (authentik-server, authentik-worker) report UNHEALTHY status in production environment despite being operational
- Files: `ansible/files/gateway-vps/authentik/compose.yml`, `ansible/files/gateway-vps/pangolin/compose.yml`
- Trigger: Complex health check logic or PostgreSQL migration issues during startup
- Workaround: Monitor via external health checks (Beszel, Uptime Kuma) rather than relying on container health status; upgrade to 2025.10 may resolve

## Security Considerations

**SSH Permission Issue in Test Suite:**
- Risk: Gateway VPS test suite reports 1 SSH permission failure (noted in VPS Recovery notes, 261/262 tests passing). Could indicate misconfigured SSH access or permission inheritance problem.
- Files: `ansible/tests/suites/gateway_vps_test_suite.yml`
- Current mitigation: Tests are passing at 99.6% and only affects validation, not critical path access
- Recommendations: Investigate SSH permission failure in test suite; ensure consistent file permissions for automated access; add specific SSH permission validation test

**CrowdSec Firewall Bouncer API Key Management:**
- Risk: API keys for firewall bouncer stored in secrets file written by deployment playbook
- Files: `ansible/deploy_vps.yml` (lines 13-25 creates secrets file), `ansible/files/gateway-vps/crowdsec/config/crowdsec/`
- Current mitigation: Secrets file created with 0600 permissions, keys fetched from 1Password integration
- Recommendations: Verify 1Password integration is always available before deployment; ensure bouncer registration failure doesn't silently fail; add pre-deployment validation that secrets are accessible

**Authentik Media Directory Permissions:**
- Risk: Authentik media directories created with 1000:1000 ownership and 0775 permissions - overly permissive
- Files: `ansible/deploy_vps.yml` (lines 36-59, creates `/opt/appdata/authentik/media` with 0775)
- Current mitigation: Container runs with limited privileges, socket proxy restricts Docker API access
- Recommendations: Reduce media directory to 0750 permissions; evaluate if public branding files need world-readable access; ensure Authentik container uid:gid is properly mapped

## Performance Bottlenecks

**PostgreSQL Connection Pressure from Redis Removal:**
- Problem: Authentik 2025.10 removes Redis entirely, moving caching and session storage to PostgreSQL. Current setup has no analysis of expected connection pool increase or PostgreSQL tuning.
- Files: `ansible/files/gateway-vps/authentik/compose.yml`, `guides/Authentik Upgrade Analysis 2024.12 to 2025.10.md` (notes ~50% more connections expected)
- Cause: Architecture change in Authentik increases database pressure; PostgreSQL container may not be sized for load
- Improvement path: Analyze current PostgreSQL connection usage pre-upgrade; increase max_connections parameter if needed; consider connection pooling (pgBouncer) for gateway VPS; monitor connection pool saturation post-upgrade

**Missing Resource Limits on Docker Containers:**
- Problem: `common.yml` defines base service template but includes no memory/CPU limits. 59 containers across infrastructure with no resource constraints could cause cascading failures.
- Files: `ansible/files/common.yml`, all service compose files
- Cause: Kubernetes-style resource constraints not defined; relies on host-level management
- Improvement path: Add recommended resource limits to base and socket-base templates; implement per-service overrides for high-load services (Jellyfin, Radarr, Sonarr, Graylog); monitor resource usage and tune based on actual demand

## Fragile Areas

**Gateway VPS Deployment Workflow - Multi-Step, Order-Dependent:**
- Files: `ansible/deploy_vps.yml`, `ansible/roles/docker/`, `ansible/roles/pangolin/`
- Why fragile: Deployment requires: (1) docker role, (2) auth bypass template generation, (3) Traefik restart, (4) bouncer registration. If any step fails or is skipped, auth fails silently. No built-in validation that auth bypass is active post-deploy.
- Safe modification: Add health check task at end of deploy_vps.yml that validates auth bypass routes are loaded in Traefik config; add failure handler that stops deployment if health check fails; consider consolidating into single role instead of post_tasks
- Test coverage: `ansible/tests/suites/gateway_vps_test_suite.yml` validates auth bypass and SSO but doesn't validate Traefik configuration persistence

**Tunnel Connectivity Infrastructure - No Automation:**
- Files: `ansible/roles/pangolin/` (never called), `ansible/inventory.yml` (newt_enabled flag unused), media-vm/apps-vm/obs-vm docker deployments
- Why fragile: Newt tunnels are critical for external access but deployment is not automated. If tunnel goes down, manual intervention required. June 19 incident shows media-vm went offline for exactly this reason.
- Safe modification: Create dedicated playbook for tunnel deployment separate from docker; run after docker stack is healthy; add tunnel health checks to test suite; ensure inventory properly controls tunnel deployment
- Test coverage: No tunnel connectivity tests in current test suite

**Authentik SSO Integration - Incomplete Pattern Across Services:**
- Files: `ansible/files/gateway-vps/authentik/compose.yml`, `AUTHENTIK_IMPLEMENTATION_STATE.md`, `KARAKEEP_SSO_SETUP.md`
- Why fragile: Authentik deployment completed but service integrations are incomplete. Karakeep SSO setup documented as manual steps. Other services may not be integrated. If Authentik version/configuration changes, multiple services need manual reconfiguration.
- Safe modification: Create reusable Authentik integration templates for services; document which services support OAuth2 vs OIDC vs SAML; add integration validation tests; version Authentik configuration in code, not just in running instance
- Test coverage: `ansible/tests/functionality_test_sso.yml` and `ansible/tests/authentik_auth_tests.yml` exist but coverage of service-specific integrations unknown

**Auth Bypass Hardcoding - Services List in Template:**
- Files: `ansible/roles/pangolin/templates/bypass-routers.yml.j2`, `ansible/files/gateway-vps/pangolin/auth-bypass.yml`
- Why fragile: Bypass services hardcoded in template; if new service needs bypass or existing service removed, template must be manually edited
- Safe modification: Move bypass service list to inventory variables; generate template from structured config; add validation that bypass list matches actual services
- Test coverage: Security tests validate that bypass works but don't validate comprehensiveness of bypass list

## Scaling Limits

**Docker Compose Scale Limitations:**
- Current capacity: 59 containers across 3 homelab VMs + 10 containers on gateway VPS = 69 total
- Limit: Docker Compose on single host supports this without issue; scaling to multiple gateway instances requires significant refactoring. Newt tunnel approach doesn't distribute well across multiple gateways.
- Scaling path: If more external services needed, consider: (1) moving to Kubernetes for orchestration, (2) implementing proxy load balancing across multiple VPS instances, (3) restructuring to separate inbound and outbound traffic paths

**PostgreSQL Shared Database Pattern:**
- Current capacity: Single PostgreSQL instance on apps-vm supports multiple applications (Authentik metadata, future apps)
- Limit: If more applications added or query load increases, single shared database becomes bottleneck
- Scaling path: Implement separate PostgreSQL instances per application with replication/backup strategy; or migrate to managed database service

**CrowdSec Single Instance on Gateway:**
- Current capacity: Single CrowdSec instance protecting entire gateway
- Limit: If threat volume increases dramatically, single instance may not scale. Community-driven threat intel is valuable but depends on external connectivity.
- Scaling path: CrowdSec has clustering support for enterprise deployments; for now, monitor CPU/memory on single instance and add explicit resource limits

## Dependencies at Risk

**Authentik Version - Significant Upgrade Required:**
- Risk: Authentik 2024.12.2 is 11 months old with breaking changes in 2025.10 (Redis removal). Service will become out-of-date quickly.
- Impact: Security patches may stop for 2024.12, OAuth2/OIDC implementations may diverge from upstream, integration examples will reference newer versions
- Migration plan: Execute version upgrade path with proper testing; upgrade should happen within 3-4 months to maintain support

**CrowdSec Community Threat Intelligence Dependency:**
- Risk: Firewall bouncer effectiveness depends on CrowdSec community sharing threat data. If community participation drops or service goes offline, protection degrades.
- Impact: Malicious IPs discovered by community may not be blocked if data sharing stops
- Migration plan: CrowdSec has enterprise/self-hosted option with curated intelligence; for now, monitor community activity; implement fallback to whitelist-only mode if threat intel fails

**Traefik Configuration Format Stability:**
- Risk: Traefik configuration using file-based dynamic config. Future Traefik versions may change config format or remove features (auth bypass, middleware).
- Impact: If Traefik major version upgrade breaks config, auth bypass stops working until config updated
- Migration plan: Track Traefik release notes closely; test config format against new versions before upgrading; consider alternative reverse proxies as backup option

**Docker Socket Proxy Security:**
- Risk: Socket proxy restricts Docker API access but relies on proxy implementation security. If proxy has vulnerability, attackers get Docker API access.
- Impact: Compromised socket proxy means compromised host
- Migration plan: Keep socket proxy image updated; audit proxy permissions regularly; consider alternative like Docker API authorization plugin

## Missing Critical Features

**No Automated Failover for External Access:**
- Problem: Single VPS gateway is single point of failure for external access. If VPS goes down, all external services unreachable.
- Blocks: High-availability setup, disaster recovery
- Solution: Implement DNS failover to secondary VPS or implement gateway redundancy with keepalived/heartbeat

**No Service Mesh / Circuit Breaking:**
- Problem: If one internal service fails, dependent services don't gracefully degrade
- Blocks: Resilience testing, chaos engineering
- Solution: Implement Istio or Linkerd for service mesh, or add circuit breaker pattern to Traefik

**No Secrets Rotation / Key Cycling:**
- Problem: API keys, passwords, certificates stored in 1Password but not automatically rotated
- Blocks: Compliance with security best practices
- Solution: Implement automated secrets rotation with Vault or AWS Secrets Manager; establish key rotation policy

**No Infrastructure Cost Tracking:**
- Problem: No visibility into resource usage or cost implications
- Blocks: Scaling decisions without cost awareness
- Solution: Add Prometheus metrics for resource consumption; track VPS costs vs self-hosted infrastructure

## Test Coverage Gaps

**No Tunnel Connectivity Tests:**
- What's not tested: Whether newt tunnels to media-vm, apps-vm, obs-vm are actually functional
- Files: `ansible/tests/suites/homelab_vms_test_suite.yml`, test suite is missing tunnel health checks
- Risk: Tunnels can go down silently; June 19 incident shows this exact scenario
- Priority: HIGH - critical for external access

**No Service Integration Tests for Authentik:**
- What's not tested: Whether integrated services (Jellyfin, Karakeep, etc.) actually work with Authentik SSO
- Files: `ansible/tests/authentik_auth_tests.yml` tests Authentik but not downstream service integrations
- Risk: Service integrations could break after Authentik upgrade or config change
- Priority: MEDIUM - affects user experience

**No PostgreSQL Connection Pool Saturation Tests:**
- What's not tested: Whether Authentik 2025.10 (with Redis removal) will saturate PostgreSQL connections
- Files: No pre-upgrade testing for connection load
- Risk: Upgrade to 2025.10 could cause PostgreSQL connection pool exhaustion
- Priority: HIGH - critical before upgrade

**No Disaster Recovery / Restore Testing:**
- What's not tested: Whether backups can actually be restored and services recovered
- Files: No recovery tests defined
- Risk: Backups could be corrupted but failure only discovered when needed
- Priority: HIGH - critical for business continuity

**No Cross-VLAN Connectivity Tests:**
- What's not tested: Whether services can communicate across VLAN boundaries (network isolation validation)
- Files: Tests don't validate network isolation
- Risk: Network segmentation could have gaps allowing unauthorized access
- Priority: MEDIUM - security-related

---

*Concerns audit: 2026-02-05*
