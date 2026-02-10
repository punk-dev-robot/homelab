---
title: Ansible Test Framework Analysis for Authentik Integration
type: note
permalink: patterns/ansible-test-framework-analysis-for-authentik-integration
---

# Ansible Test Framework Analysis for Authentik Integration

## Test Framework Architecture

### Gateway VPS Test Suite Structure
- **Main File**: `ansible/tests/suites/gateway_vps_test_suite.yml`
- **Framework**: Production-grade test suite with standardized patterns
- **Test Categories**: Security (critical), Functionality (critical), Health (important)
- **Tags**: smoke, security, functionality, critical for selective execution

### Test Pattern Components

#### 1. Test Base Framework (`common/test_base.yml`)
```yaml
# Standardized HTTP test execution
- uri:
    url: "{{ test_config.url }}"
    headers: "{{ test_config.headers }}"
    follow_redirects: "{{ test_config.follow_redirects | default('none') }}"
    status_code: "{{ test_config.expected_statuses }}"
    timeout: "{{ test_config.timeout }}"
```

#### 2. Test Configuration (`common/test_config.yml`)
```yaml
test_standards:
  timeout: 10
  long_timeout: 15

test_categories:
  security:
    critical: true
    timeout: 10
  functionality:
    critical: true
    timeout: 15

test_patterns:
  sso_redirect:
    expected_status: 302
    validation_pattern: "pangolin\\.{{ organization_domain }}"
  bypass_success:
    expected_status: 200
```

#### 3. Test Recording (`common/test_recorder.yml`)
```yaml
# Standardized result tracking
test_results: "{{ test_results + [standardized_test_entry] }}"
test_summary: "{{ test_summary | combine(updated_summary) }}"
```

### Current Authentication Test Patterns

#### Security Tests
1. **Invalid Bypass Key Test** (`security_test_invalid_key.yml`)
   - Tests invalid auth bypass header rejection
   - Expects 302 redirect to Pangolin SSO
   
2. **No Header Test** (`security_test_no_header.yml`)
   - Tests missing auth bypass header
   - Expects 302 redirect to authentication

3. **Non-Bypass Services** (`security_test_non_bypass.yml`)
   - Tests SSO-protected services require authentication
   - Services: grafana, openwebui, jellyfin

#### Functionality Tests
1. **Auth Bypass Test** (`functionality_test_bypass.yml`)
   - Tests valid bypass key allows access
   - Uses 1Password CLI for secure key retrieval

2. **SSO Flow Test** (`functionality_test_sso.yml`)
   - Tests normal SSO authentication redirect
   - Validates redirect to `pangolin.{{ organization_domain }}`

### Current Service Categories

#### Auth Bypass Services (9 services)
- jellyseerr, sonarr, radarr, lidarr, readarr, bazarr, prowlarr, sabnzbd, nzbget
- Use `traefik-auth-bypass-key` header for testing
- 3 services tested for performance (configurable)

#### SSO Protected Services (3 services)
- grafana, openwebui, jellyfin
- Must redirect to Pangolin for authentication

### Authentik Current Configuration

#### Infrastructure
- **URL**: `auth.nobasura.org`
- **Internal**: `authentik-server:9000`
- **Network**: Connected to pangolin network
- **Health Check**: `/-/health/live/` endpoint

#### Traefik Integration
```yaml
# Existing routes in dynamic_config.yml
auth-router:
  rule: "Host(`auth.nobasura.org`)"
  service: authentik-service
  middlewares: [crowdsec-bouncer]
```

## Authentik Test Requirements

### 1. Health Check Tests
- Service availability at `auth.nobasura.org`
- Health endpoint validation
- Database and Redis connectivity

### 2. Authentication Flow Tests
- Initial authentication redirect
- Login page accessibility
- Post-authentication redirect
- Session validation

### 3. Integration Tests
- Pangolin SSO integration
- ForwardAuth middleware validation
- Service protection verification

### 4. Security Tests
- Invalid credentials rejection
- Session timeout enforcement
- CSRF protection validation

## Recommended Test Implementation

### Test Files to Create
1. `functionality_test_authentik_health.yml` - Health checks
2. `functionality_test_authentik_auth.yml` - Authentication flow
3. `security_test_authentik_protection.yml` - Security validation
4. `integration_test_authentik_sso.yml` - SSO integration

### Test Configuration Updates
```yaml
test_services:
  auth_bypass: "{{ (pangolin_auth_bypass_services | map(attribute='name') | list)[:3] }}"
  sso_protected: ["grafana", "openwebui", "jellyfin"]
  authentik_protected: ["homepage", "dozzle", "grafana"]  # New category
  
test_patterns:
  authentik_redirect:
    expected_status: 302
    validation_pattern: "auth\\.{{ organization_domain }}"
  authentik_health:
    expected_status: 200
    validation_pattern: "authentik"
```

### Critical Test Points
1. **Health Validation**: Ensure Authentik service is operational
2. **Redirect Validation**: Verify authentication redirects work
3. **Integration Validation**: Confirm ForwardAuth middleware integration
4. **Security Validation**: Test unauthorized access rejection