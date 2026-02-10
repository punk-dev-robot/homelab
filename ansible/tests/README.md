# Infrastructure Test Framework

Production-grade test suite for critical authentication flows and infrastructure validation.

## Overview

This test framework provides comprehensive validation of:
- **Security**: Auth bypass protection and SSO enforcement
- **Functionality**: Service accessibility and authentication flows  
- **Health**: Service reachability and response validation

## Architecture

### Production-Grade Design Principles
- **DRY**: Centralized test components eliminate code duplication
- **Separation of Concerns**: Modular design with clear responsibilities
- **Configuration-Driven**: Centralized standards and patterns
- **Error Handling**: Comprehensive error capture and reporting
- **Security**: Proper secret management and logging protection

### Directory Structure
```
tests/
├── common/               # Shared components
│   ├── test_config.yml   # Centralized configuration
│   ├── test_init.yml     # Framework initialization
│   ├── test_base.yml     # HTTP test execution engine
│   └── test_recorder.yml # Result recording and progress
├── security_tests.yml    # Security test orchestrator
├── functionality_tests.yml # Functionality test orchestrator
├── security_test_*.yml   # Individual security tests
├── functionality_test_*.yml # Individual functionality tests
└── test_helpers.yml      # Main framework helpers
```

## Usage

### Quick Start
```bash
# Full test suite
ansible-playbook test_infrastructure.yml

# Quick smoke tests (30 seconds)
ansible-playbook test_infrastructure.yml --tags smoke

# Security tests only
ansible-playbook test_infrastructure.yml --tags security

# Functionality tests only  
ansible-playbook test_infrastructure.yml --tags functionality
```

### Test Categories

| Tag | Description | Critical | Timeout |
|-----|-------------|----------|---------|
| `smoke` | Quick validation | Yes | 10s |
| `security` | Security enforcement | Yes | 10s |
| `functionality` | Feature validation | Yes | 15s |
| `critical` | All critical tests | Yes | Variable |

## Configuration

### Centralized Standards (`common/test_config.yml`)
- **Timeouts**: Standardized timeout values
- **Status Codes**: Accepted HTTP response codes
- **Test Patterns**: Reusable validation patterns
- **Service Lists**: Dynamic service discovery

### Test Patterns
```yaml
test_patterns:
  sso_redirect:
    expected_status: 302
    validation_pattern: "pangolin\\.{{ organization_domain }}"
  
  bypass_success:
    expected_statuses: [200, 307, 401]
    exclude_pattern: "pangolin\\.{{ organization_domain }}"
```

## Components

### 1. Test Execution Engine (`common/test_base.yml`)
Standardized HTTP test execution with:
- Configurable timeouts and headers
- Automatic error handling
- Response validation
- Redirect location checking

### 2. Result Recording (`common/test_recorder.yml`)
Centralized test result management:
- Standardized result format
- Progress tracking
- Critical failure detection
- Performance metrics

### 3. Configuration Management (`common/test_config.yml`)
Production-grade configuration:
- Environment-specific settings
- Reusable test patterns
- Service categorization
- Standards enforcement

### 4. Framework Initialization (`common/test_init.yml`)
Secure initialization:
- Test variable setup
- 1Password secret retrieval
- Configuration loading
- Error-safe defaults

## Security Features

### Secret Management
- **1Password Integration**: Secure runtime secret retrieval
- **No Logging**: Sensitive operations use `no_log: true`
- **Single Retrieval**: Bypass key fetched once and cached
- **Memory Safety**: No secrets in configuration files

### Error Handling
- **Graceful Failures**: All HTTP tests use `ignore_errors: true`
- **Defensive Programming**: Extensive use of `| default()` filters
- **Validation**: Comprehensive input validation
- **Reporting**: Detailed error capture and reporting

## Test Development

### Adding New Tests
1. Create test file in appropriate category
2. Use standardized components from `common/`
3. Follow naming convention: `{category}_test_{name}.yml`
4. Include in main orchestrator file

### Test Structure Template
```yaml
---
# Test description and purpose

- name: Set test context
  set_fact:
    test_name: "Category: Test description"
    test_start_time: "{{ ansible_date_time.epoch }}"

- name: Execute test
  include_tasks: common/test_base.yml
  vars:
    test_config:
      url: "https://{{ target_service }}.{{ organization_domain }}"
      headers: {}
      timeout: "{{ test_categories.category.timeout }}"
      critical: "{{ test_categories.category.critical }}"
      validation_logic: "{{ test_validation_expression }}"
    test_expected: "Expected behavior description"
    test_details: "Additional test context"

- name: Record test result
  include_tasks: common/test_recorder.yml
```

## Performance Features

- **Parallel Execution**: Tests run independently
- **Optimized Loops**: Proper loop controls and variable scoping
- **Caching**: Single 1Password lookup per test run
- **Efficient Reporting**: Batch result processing

## CI Integration

### Exit Codes
- **0**: All critical tests passed
- **1**: Critical test failures detected

### Result Format
Results saved to `/tmp/infrastructure_test_results.json`:
```json
{
  "timestamp": "2025-06-07T17:00:00Z",
  "duration_seconds": 45,
  "summary": {
    "total": 12,
    "passed": 12,
    "failed": 0,
    "critical_failures": []
  },
  "results": [...],
  "exit_code": 0
}
```

## Monitoring and Alerting

### Critical Failure Detection
- Automatic deployment blocking on critical failures
- Detailed failure reporting with context
- Performance metrics tracking
- Error categorization

### Metrics
- Test execution time
- Success/failure rates
- Service response times
- Error patterns

## Maintenance

### Regular Tasks
- Review test timeouts and adjust for infrastructure changes
- Update service lists as infrastructure evolves  
- Monitor test performance and optimize as needed
- Validate test coverage for new services

### Troubleshooting
- Check 1Password CLI authentication
- Verify network connectivity to target services
- Review test logs for detailed error information
- Validate service configurations match test expectations

## Best Practices

1. **Always run tests before infrastructure changes**
2. **Use appropriate tags for different validation levels**
3. **Monitor test performance and adjust timeouts as needed**
4. **Keep test configurations in sync with infrastructure**
5. **Review failed tests thoroughly before overriding**