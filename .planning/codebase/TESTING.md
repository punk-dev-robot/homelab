# Testing Patterns

**Analysis Date:** 2026-02-05

## Test Framework

**Runner:**
- Framework: Ansible playbooks with `ansible-playbook` CLI
- Execution: Via command line with `-i` inventory and optional `--tags` filtering
- Configuration: `ansible/ansible.cfg` with debug callback enabled
- Output format: YAML with colored debug output

**Test Execution Commands:**
```bash
# Full test suites (mandatory before commits)
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml         # Gateway VPS auth/SSO testing
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml       # Homelab VM service testing
ansible-playbook -i ansible/inventory.yml ansible/tests/validation/container_standardization.yml  # Container standards
ansible-playbook -i ansible/inventory.yml ansible/tests/validation/crowdsec_firewall_bouncer.yml # CrowdSec validation

# Quick validation with smoke tag
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml --tags smoke
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml --tags smoke

# Tag-specific filtering
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml --tags security     # Security tests only
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml --tags functionality # Functionality tests only
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml --tags critical     # Critical tests only
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml --tags direct      # Direct .lan access only
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml --tags proxy       # Caddy proxy .lab access only
```

**Assertion/Validation:**
- HTTP status codes: `status_code:` parameter in uri module
- Redirect validation: regex pattern matching on `location:` header
- Custom logic: `validation_logic:` variable containing conditional expression
- Results recording: standardized facts collection in test_recorder.yml

## Test File Organization

**Location Structure:**
```
ansible/tests/
├── common/              # Shared test framework
│   ├── test_init.yml           # Framework initialization
│   ├── test_base.yml           # HTTP test execution engine
│   ├── test_config.yml         # Centralized configuration
│   └── test_recorder.yml       # Result recording
├── suites/              # Main test suites
│   ├── gateway_vps_test_suite.yml     # VPS auth/SSO tests
│   └── homelab_vms_test_suite.yml    # Homelab VM availability tests
├── validation/          # Validation checks
│   ├── container_standardization.yml  # Docker compose standards
│   └── crowdsec_firewall_bouncer.yml # CrowdSec validation
├── security_*.yml       # Individual security test scenarios
├── functionality_*.yml  # Individual functionality test scenarios
├── authentik_auth_tests.yml     # Authentik-specific tests
├── test_helpers.yml    # Test framework helpers
└── [other validation files]
```

**Test File Naming:**
- Main suites: `<target>_test_suite.yml` (e.g., `gateway_vps_test_suite.yml`)
- Individual tests: `<type>_test_<scenario>.yml` (e.g., `security_test_invalid_key.yml`)
- Validation: `validation/<component>.yml` or `<component>_validation.yml`
- Helpers: `<function>_helpers.yml` or `common/<function>.yml`

**Relation to Source Code:**
- Tests are independent of deployment playbooks
- Can run against any environment (dev/prod) via inventory
- Tests are located in `ansible/tests/` parallel to `ansible/roles/` and `ansible/files/`

## Test Structure

**Test Suite Anatomy:**
```yaml
---
# Header: Purpose, usage examples, and available tags
- name: Test Suite Name
  hosts: localhost  # or specific hosts
  gather_facts: true
  connection: local

  vars:
    # Configuration specific to suite

  pre_tasks:
    - name: Verify prerequisites
      # Check tools/access requirements

    - name: Initialize test framework
      include_tasks: ../test_helpers.yml
      tags: ["always"]

    - name: Display test suite information
      # Provide context to operator

  tasks:
    - name: Feature Test Group 1
      include_tasks: ../feature_tests_1.yml
      tags: ["tag1", "critical", "smoke"]

    - name: Feature Test Group 2
      include_tasks: ../feature_tests_2.yml
      tags: ["tag2", "critical"]

  post_tasks:
    - name: Generate final test report
      include_tasks: ../test_helpers.yml
      vars:
        generate_final_report: true
      tags: ["always"]

    - name: Block deployment on critical failures
      fail:
        msg: "Test failures detected"
      when: (test_summary.critical_failures | default([])) | length > 0
      tags: ["always"]
```

**Individual Test Pattern:**
```yaml
---
# Header: Clear description of test purpose

- name: Set test context
  set_fact:
    test_name: "Feature: Clear description"
    test_start_time: "{{ ansible_date_time.epoch }}"

- name: Execute test action
  include_tasks: common/test_base.yml
  vars:
    test_config:
      url: "{{ url_to_test }}"
      method: "{{ method | default('GET') }}"
      headers: "{{ headers_dict }}"
      timeout: "{{ timeout_seconds }}"
      expected_statuses: [200, 302]
      critical: true  # Mark as blocking deployment
      validation_logic: "{{ condition_expression }}"
    test_expected: "Expected outcome description"
    test_details: "Additional context"

- name: Record test result
  include_tasks: common/test_recorder.yml
```

**Test Initialization Pattern:**
```yaml
---
# Test framework initialization

- name: Initialize test framework
  include_tasks: common/test_init.yml
  when: test_results is not defined

- name: Load test configuration
  include_vars: test_config.yml

- name: Initialize bypass key (once)
  set_fact:
    bypass_key: "{{ lookup('community.general.onepassword', 'TRAEFIK_AUTH_BYPASS_KEY', vault='Homelab') }}"
  no_log: true
  when: bypass_key is not defined
```

## Test Patterns & Execution

**HTTP Testing Pattern:**
```yaml
- name: Execute standardized HTTP test
  uri:
    url: "{{ test_config.url }}"
    method: "{{ test_config.method | default('GET') }}"
    headers: "{{ (test_config.headers | default({})) | combine({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}) }}"
    follow_redirects: "{{ test_config.follow_redirects | default('none') }}"
    status_code: "{{ test_config.expected_statuses | default([200]) }}"
    timeout: "{{ test_config.timeout | default(test_standards.timeout) }}"
    return_content: "{{ test_config.return_content | default(false) }}"
  register: http_result
  ignore_errors: true
```

**Validation Logic Pattern:**
```yaml
- name: Calculate test result based on pattern
  set_fact:
    test_passed: "{{ test_validation_result }}"
  vars:
    test_validation_result: "{{
      test_config.validation_logic if test_config.validation_logic is defined
      else (
        http_result.status is defined and
        http_result.status in (test_config.expected_statuses | default([200])) and
        (location_valid | default(true)) and
        not (http_result.failed | default(false)))
    }}"
```

**Result Recording Pattern:**
```yaml
- name: Record standardized test result
  set_fact:
    test_results: "{{ test_results + [standardized_test_entry] }}"
    test_summary: "{{ test_summary | combine(updated_summary) }}"
  vars:
    standardized_test_entry:
      name: "{{ test_name }}"
      status: "{{ 'PASS' if test_passed else 'FAIL' }}"
      critical: "{{ test_config.critical | default(false) }}"
      duration_ms: "{{ test_duration_ms | default(0) }}"
      details: "{{ test_details | default('') }}"
      expected: "{{ test_expected | default('Expected result') }}"
      actual: "{{ test_actual | default('') }}"
      error: "{{ test_error | default('') }}"
    updated_summary:
      total: "{{ (test_summary.total | int) + 1 }}"
      passed: "{{ (test_summary.passed | int) + (1 if test_passed else 0) }}"
      failed: "{{ (test_summary.failed | int) + (0 if test_passed else 1) }}"
      critical_failures: "{{ test_summary.critical_failures + ([test_name] if (not test_passed and (test_config.critical | default(false))) else []) }}"
```

## Test Configuration

**Centralized Configuration:**
- Location: `ansible/tests/common/test_config.yml`
- Contains: standard timeouts, patterns, service definitions, category metadata

**Config Structure:**
```yaml
test_standards:
  timeout: 10
  long_timeout: 15
  bypass_header_name: "{{ pangolin_auth_bypass_header }}"

test_categories:
  security:
    critical: true
    timeout: "{{ test_standards.timeout }}"
    description: "Critical security validation tests"
  functionality:
    critical: true
    timeout: "{{ test_standards.long_timeout }}"
    description: "Critical functionality validation tests"

test_patterns:
  sso_redirect:
    expected_status: 302
    validation_pattern: "pangolin\\.{{ organization_domain }}"
    description: "SSO authentication redirect pattern"

test_services:
  auth_bypass: "{{ (pangolin_auth_bypass_services | map(attribute='name') | list)[:3] }}"
  sso_protected: ["grafana", "openwebui", "jellyfin"]
```

## Test Types & Coverage

**Gateway VPS Test Suite:**
- File: `ansible/tests/suites/gateway_vps_test_suite.yml`
- Scope: Tests external HTTPS services via Traefik + Pangolin
- Tests included:
  - Security validation (invalid keys, missing headers blocked)
  - Functionality validation (auth bypass works, SSO flow works)
  - Authentik service health
  - CrowdSec bouncer validation
- Requirements: 1Password CLI access to TRAEFIK_AUTH_BYPASS_KEY

**Homelab VMs Test Suite:**
- File: `ansible/tests/suites/homelab_vms_test_suite.yml`
- Scope: Tests direct .lan and Caddy proxy .lab access methods
- Tests included:
  - Direct HTTP connectivity (.lan addresses)
  - Caddy reverse proxy functionality (.lab.nobasura.org)
  - Container health status
  - Service-specific endpoints
- Services tested: 9+ across 3 VMs (apps-vm, media-vm, obs-vm)

**Container Standardization Validation:**
- File: `ansible/tests/validation/container_standardization.yml`
- Purpose: Verify all containers follow base service inheritance pattern
- Checks: extends declarations, required fields, naming conventions

**CrowdSec Firewall Bouncer Validation:**
- File: `ansible/tests/validation/crowdsec_firewall_bouncer.yml`
- Purpose: Validate CrowdSec integration and IP bouncing rules
- Scope: VPS-only (security component)

## Test Result Reporting

**Test Summary Structure:**
```yaml
test_summary:
  total: <int>           # Total tests run
  passed: <int>         # Passed tests
  failed: <int>         # Failed tests
  critical_failures: [<test_names>]  # Names of critical test failures
```

**Individual Test Result:**
```yaml
test_result_entry:
  name: "Test Name"
  status: "PASS|FAIL"
  critical: true|false
  duration_ms: <int>
  details: "Additional context"
  expected: "What should happen"
  actual: "What happened"
  error: "Error message if failed"
```

**Result Persistence:**
- Location: `/tmp/infrastructure_test_results.json`
- Format: JSON with timestamp, duration, summary, results array, exit_code
- Usage: CI/CD integration, audit trail
- Created in: post_tasks of test suites

**Output Format:**
```yaml
---
🧪 INFRASTRUCTURE TEST RESULTS
================================
Total Tests: {{ test_summary.total }}
Passed: {{ test_summary.passed }}
Failed: {{ test_summary.failed }}
Duration: {{ duration }}s

[Failed tests listed with details]

🚨 CRITICAL FAILURES DETECTED (if any)
Deployment should be blocked!
```

## Critical/Blocking Tests

**Critical Test Marking:**
- Set via `test_config.critical: true` in test definition
- Blocks deployment if failed via post_task fail condition
- Examples: security tests (auth bypass), functionality tests (SSO)

**Deployment Blocking:**
- Test suite fails if: `(test_summary.critical_failures | default([])) | length > 0`
- All critical tests must pass before proceeding with deployment
- Exit code: 1 on critical failures, 0 on success

**MANDATORY Pre-Commit Tests:**
- Gateway VPS changes: `ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml`
- Homelab changes: `ansible-playbook -i ansible/inventory.yml ansible/tests/suites/homelab_vms_test_suite.yml`
- Container changes: `ansible-playbook -i ansible/inventory.yml ansible/tests/validation/container_standardization.yml`

## Mocking & Test Data

**Secrets Handling in Tests:**
- 1Password lookups: Live lookups during test execution (no mocking)
- Bypass key: Retrieved once, cached in `bypass_key` fact
- Sensitive output: `no_log: true` on all secret-related tasks
- Test fixtures: Use actual service URLs (tests are integration-style)

**Service Definitions:**
- Hardcoded in test playbooks (apps.lan, media.lan, obs.lan)
- Proxy domains: Referenced via variables ({{ organization_domain }})
- Port mappings: Defined in homelab_services variable structure
- No external mocking layer

**Test Data Sources:**
- Service inventory: `ansible/inventory.yml` (host definitions)
- Test configuration: `ansible/tests/common/test_config.yml`
- Variable files: `ansible/roles/pangolin/vars/auth_bypass.yml`
- Secrets: 1Password vault during execution

## Common Test Patterns

**Async Testing:**
Not applicable - Ansible uri module handles async HTTP operations natively

**Conditional Testing:**
```yaml
when:
  - test_config.validation_pattern is defined
  - http_result.status is defined
  - http_result.status == 302
```

**Error Testing:**
```yaml
- name: Execute test with expected error handling
  uri:
    url: "{{ invalid_url }}"
  register: error_result
  ignore_errors: true

- name: Verify error behavior
  set_fact:
    test_passed: "{{ error_result.failed | default(false) }}"
```

**Timeout Testing:**
- timeout: 10s (standard)
- timeout: 15s (long operations)
- Configurable per test via `test_config.timeout`

**Looped Testing:**
```yaml
- name: Test each service
  include_tasks: test_scenario.yml
  loop: "{{ test_services.auth_bypass }}"
  loop_control:
    loop_var: target_service
```

## Coverage Gaps

**Current Gaps:**
- No unit tests for Ansible roles (role testing via integration only)
- No performance/load testing
- No chaos engineering tests
- Limited testing of failure paths (mostly happy path)
- No multi-region/failover testing

**Recommendations:**
- Add role validation tests for variable validation
- Implement performance baselines for critical services
- Add negative test cases for error scenarios
- Test service dependency ordering

---

*Testing analysis: 2026-02-05*
