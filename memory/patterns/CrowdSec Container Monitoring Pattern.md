---
title: CrowdSec Container Monitoring Pattern
type: note
permalink: patterns/crowd-sec-container-monitoring-pattern
---

# CrowdSec Container Monitoring Pattern

## Overview
This pattern describes how to configure CrowdSec to monitor Docker container logs for security threats, specifically for authentication services.

## Prerequisites
- CrowdSec running in Docker container
- Target containers producing logs
- Docker socket access for CrowdSec container

## Implementation Pattern

### 1. Docker Socket Access
```yaml
# In docker-compose.yml or similar
services:
  crowdsec:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

**Security Note**: Read-only mount is sufficient for log monitoring.

### 2. Acquisition Configuration
Create acquisition file in `/etc/crowdsec/acquis.d/`:

```yaml
---
# Monitor specific containers
source: docker
container_name:
  - target-container-1
  - target-container-2
labels:
  type: application_name
---
# Optional: Monitor log files directly
filenames:
  - /var/log/application/access.log
labels:
  type: application_name
```

### 3. Collection Installation
```bash
# Install relevant collection for the application
cscli collections install vendor/application-name

# Verify installation
cscli collections list
cscli scenarios list
```

### 4. Validation Steps
1. **Container Health**: Verify CrowdSec container starts successfully
2. **Log Processing**: Check metrics show log lines being processed
3. **Parser Function**: Confirm logs are being parsed (not just read)
4. **Scenario Activation**: Validate security scenarios are detecting threats

## Authentik SSO Example

### Acquisition File
```yaml
---
source: docker
container_name:
  - authentik-server
  - authentik-worker
labels:
  type: authentik
```

### Required Collection
- **Collection**: `firix/authentik`
- **Scenarios**: `firix/authentik-bf` (brute force detection)
- **Parsers**: `firix/authentik-logs`

### Validation Commands
```bash
# Check container monitoring
docker logs crowdsec | grep "start tail for container"

# View metrics
docker exec crowdsec cscli metrics

# Check scenarios
docker exec crowdsec cscli scenarios list | grep authentik
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure Docker socket has correct permissions
   - Verify CrowdSec container runs with appropriate user

2. **Container Not Found**
   - Check container names match exactly
   - Verify containers are running in same Docker network

3. **Logs Not Parsed**
   - Confirm parser is installed and enabled
   - Check log format matches parser expectations
   - Review unparsed log metrics

4. **No Detections**
   - Verify scenarios are enabled
   - Check if log patterns match scenario triggers
   - Test with known attack patterns

### Debug Commands
```bash
# Check acquisition sources
docker exec crowdsec cscli acquisition list

# View parser status
docker exec crowdsec cscli parsers list

# Check metrics breakdown
docker exec crowdsec cscli metrics --detailed

# Monitor live logs
docker logs -f crowdsec
```

## Security Considerations

### Best Practices
1. **Read-Only Access**: Always mount Docker socket as read-only
2. **Least Privilege**: Only monitor necessary containers
3. **Log Rotation**: Ensure proper log rotation to prevent disk issues
4. **Network Isolation**: Consider running CrowdSec in isolated network
5. **Regular Updates**: Keep collections and scenarios updated

### Monitoring
- **Log Volume**: Monitor for excessive log processing
- **Container Health**: Ensure target containers remain healthy
- **Detection Rate**: Track scenario trigger frequency
- **False Positives**: Monitor and tune scenario sensitivity

## Related Patterns
- [[CrowdSec Bouncer Integration Pattern]]
- [[Authentication Service Protection Pattern]]
- [[Docker Security Monitoring Pattern]]

## Use Cases
- Authentication service protection (Authentik, Keycloak, etc.)
- Web application monitoring (Nginx, Apache)
- Database access monitoring (PostgreSQL, MySQL)
- API gateway protection (Traefik, Kong)
- Application-specific threat detection