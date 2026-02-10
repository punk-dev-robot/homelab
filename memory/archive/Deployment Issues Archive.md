---
title: Deployment Issues Archive
type: note
permalink: archive/deployment-issues-archive
tags:
- '["deployment-issues"'
- '"historical"'
- '"troubleshooting"'
- '"lessons-learned"]'
---

# Deployment Issues Archive

## Archive Context
- [purpose] Historical record of container standardization deployment issues and resolutions #historical-record
- [timeframe] June 11, 2025 - Container standardization implementation #implementation-timeframe
- [scope] Issues encountered during migration to common.yml inheritance patterns #standardization-scope

## Container Standardization Implementation Issues

### Issue 1: Duplicate security_opt Configuration
- [issue-type] Configuration duplication causing validation errors #config-duplication
- [impact] Docker Compose validation failures #validation-failure

**Problem Details**:
- [problem] Services extending `base` from common.yml also defining `security_opt` #inheritance-conflict
- [error] `services.gotify.security_opt array items[0,1] must be unique` #validation-error

**Root Cause**:
- [root-cause] Both `common.yml` base service and individual services contained identical security_opt #duplication-source

```yaml
# Duplicated configuration causing conflict
security_opt:
  - no-new-privileges:true
```

**Services Affected**:
- [affected] `gotify` (obs-vm) #gotify-affected
- [affected] `uptime-kuma` (obs-vm) #uptime-kuma-affected

**Resolution Applied**:
- [resolution] Removed redundant `security_opt` declarations from individual services #redundancy-removal
- [reasoning] Security configuration inherited from `base` service template #inheritance-benefit
- [validation] Docker Compose validation passes, services start successfully #resolution-verified

### Issue 2: Neo4j HTTPS Configuration Error
- [issue-type] Service configuration misconfiguration causing startup failure #config-error
- [impact] Neo4j container stuck in restart loop #restart-loop

**Problem Details**:
- [problem] Neo4j container unable to start after standardization changes #startup-failure
- [error] `java.lang.RuntimeException: HTTPS set to enabled, but no SSL policy provided` #ssl-error

**Root Cause Analysis**:
- [root-cause] Neo4j configuration enabled HTTPS without providing SSL certificates #ssl-misconfiguration

```yaml
# Problematic configuration
- NEO4J_server_https_enabled=true  # Missing SSL certificates
```

**Resolution Strategy**:
1. [step] Disabled HTTPS in favor of HTTP + Traefik SSL termination #ssl-termination-strategy
2. [step] Removed unused HTTPS port mapping #port-cleanup
3. [step] Updated Neo4j environment configuration #config-update

**Final Configuration**:
```yaml
- NEO4J_server_http_enabled=true
- NEO4J_server_https_enabled=false
ports:
  - "7474:7474"  # HTTP only
  - "7687:7687"  # Bolt protocol
```

**Validation Result**:
- [validation] Neo4j starts successfully #startup-success
- [validation] Accessible via internal HTTP and external HTTPS through Traefik #access-verified

### Issue 3: Apps-VM Deployment Timeout
- [issue-type] Deployment performance issue with timeout #performance-issue
- [impact] Ansible deployment timeout after 2 minutes #timeout-issue

**Problem Analysis**:
- [symptom] Ansible timeout during apps-vm deployment #timeout-symptom
- [cause] Large container images requiring extended download time #image-download-delay
- [cause] Database initialization requiring additional startup time #initialization-delay

**Resolution Outcome**:
- [outcome] Deployment actually succeeded despite timeout #false-timeout
- [outcome] Containers started successfully after image pulls completed #delayed-success
- [outcome] No configuration changes needed #no-changes-required

**Prevention Strategy**:
- [prevention] Consider increasing Ansible timeout for initial deployments with large images #timeout-adjustment
- [monitoring] Monitor deployment progress independently of Ansible timeout #independent-monitoring

### Issue 4: Permission Denied in Validation Script
- [issue-type] Script execution permission error #permission-error
- [impact] Validation script unable to complete directory scanning #script-failure

**Problem Details**:
- [problem] Validation script encountered permission errors scanning appdata directories #permission-denied

**Error Messages**:
```bash
find: './appdata/neo4j/certificates': Permission denied
grep: ./appdata/stash/config/config.yml: Permission denied
```

**Root Cause**:
- [root-cause] Validation script scanning all directories instead of targeting compose files #scope-too-broad

**Resolution Implementation**:
- [fix] Updated validation script to target only compose directories #scope-restriction

```bash
# Before (problematic approach)
find . -name "*.yml" -type f

# After (targeted approach)  
find ./compose -name "*.yml" -type f 2>/dev/null
```

**Validation Result**:
- [validation] Script runs cleanly without permission errors #clean-execution

### Issue 5: Template Escaping in Ansible Docker Format
- [issue-type] Template engine conflict between Ansible and Docker #template-conflict
- [impact] Ansible playbook execution failure #playbook-failure

**Problem Details**:
- [problem] Ansible template engine conflicted with Docker format strings #format-conflict

**Error Message**:
```bash
template error while templating string: unexpected '.'. String: docker ps --format "table {{.Names}}"
```

**Root Cause Analysis**:
- [root-cause] Ansible interpreted Docker's `{{.Names}}` as Jinja2 template syntax #template-interpretation-conflict

**Resolution Strategy**:
- [fix] Simplified docker command to avoid format string conflicts #command-simplification

```bash
# Before (template conflict)
docker ps --format "table {{.Names}}"

# After (conflict-free)
docker ps | tail -n +2 | wc -l
```

**Validation Result**:
- [validation] Command executes successfully in Ansible playbooks #execution-success

## Best Practices Established

### Configuration Management Practices
1. [practice] Always validate Docker Compose files after adding `extends:` directives #validation-practice
2. [practice] Remove redundant configurations inherited from base services #redundancy-elimination
3. [practice] Test deployments in isolated environments first #isolated-testing

### Service Configuration Standards
1. [standard] Use HTTP internally with HTTPS via reverse proxy for SSL termination #ssl-termination-standard
2. [standard] Document port reservations to prevent conflicts #port-documentation
3. [standard] Maintain separation between direct Docker socket access and proxy access #socket-separation

### Deployment Process Improvements
1. [process] Deploy stack-by-stack to isolate issues #stack-isolation
2. [process] Verify container health before proceeding to next stack #health-verification
3. [process] Use validation scripts to catch configuration redundancy #redundancy-detection

### Script Development Guidelines
1. [guideline] Target specific directories to avoid permission issues #directory-targeting
2. [guideline] Escape or avoid template conflicts in Ansible #template-conflict-avoidance
3. [guideline] Include error handling and fallback options #error-handling

## Lessons Learned

### Technical Insights
1. [insight] Configuration Inheritance: Docker Compose `extends` requires careful attention to avoid duplication #inheritance-awareness
2. [insight] Service Dependencies: Complex services like databases need specific configuration tuning #database-tuning
3. [insight] Validation First: Always validate configurations before large-scale deployments #validation-first
4. [insight] Permission Awareness: Consider file permissions when developing automation scripts #permission-consideration
5. [insight] Template Conflicts: Be aware of syntax conflicts between different template systems #syntax-awareness

### Operational Improvements
1. [improvement] Pre-deployment validation using `docker compose config` prevents issues #pre-validation
2. [improvement] Staged deployment approach isolates problems effectively #staged-approach
3. [improvement] Configuration reviews catch inheritance conflicts early #review-process
4. [improvement] Monitoring integration enables quick issue detection #monitoring-integration
5. [improvement] Clear documentation reduces resolution time #documentation-value

## Preventive Measures Implementation

### Quality Assurance Measures
1. [measure] Pre-deployment Validation: Run `docker compose config` on all modified files #config-validation
2. [measure] Staged Deployment: Deploy one stack at a time with health checks #health-checks
3. [measure] Configuration Reviews: Check for inheritance conflicts before standardization #conflict-prevention
4. [measure] Monitoring Integration: Ensure health monitoring catches issues quickly #issue-detection
5. [measure] Documentation Maintenance: Clear documentation of special cases and exceptions #exception-documentation

### Automation Improvements
- [automation] Validation scripts integrated into deployment process #integrated-validation
- [automation] Health checks automated for faster issue detection #automated-health-checks
- [automation] Configuration conflict detection built into workflow #conflict-detection

## Historical Significance
- [significance] Foundation for 95.7% inheritance adoption rate #adoption-foundation
- [significance] Enabled zero manual restart requirement achievement #automation-success
- [significance] Established patterns for future infrastructure scaling #scaling-patterns
- [significance] Created robust deployment methodology #deployment-methodology

## Relations
- documented_in [[ADR-001: Container Availability Improvements]]
- supports [[Container Service Architecture]]
- informs [[Operations Guide]]
- archived_from deployment-issues-resolutions.md (June 2025)