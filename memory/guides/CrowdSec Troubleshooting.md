---
title: CrowdSec Troubleshooting
type: note
permalink: guides/crowd-sec-troubleshooting
---

# CrowdSec Troubleshooting

## Common Issues and Solutions

### Container and Service Issues

#### CrowdSec Container Won't Start
**Symptoms**: Container exits immediately, health check failures
**Diagnosis**:
```bash
# Check container logs
docker logs crowdsec

# Verify configuration
docker exec crowdsec cscli config show
```

**Common Causes & Solutions**:
- [issue] Invalid enrollment key #enrollment-issue
  - **Solution**: Verify `CROWDSEC_ENROLLMENT_KEY` in environment
  - **Check**: 1Password secret lookup in Ansible deployment
- [issue] Journal mount permission issues #journal-permissions
  - **Solution**: Ensure `/var/log/journal:/var/log/host:ro` mount is correct
  - **Check**: Debian image required for journalctl compatibility on Ubuntu 24.10
- [issue] API key file missing or invalid permissions #api-key-issue
  - **Solution**: Verify `secrets/crowdsec-api-key` exists with 600 permissions
  - **Command**: `ls -la secrets/crowdsec-api-key`

#### Traefik 502 Bad Gateway with CrowdSec
**Symptoms**: Services return 502 errors after CrowdSec integration
**Root Cause**: Network namespace or API connectivity issues

**Solution Pattern** (Based on Pangolin breakthrough):
```yaml
# Ensure containers share proper network namespace
crowdsec:
  networks:
    - pangolin-network  # Must match Traefik network

traefik:
  networks:
    - pangolin-network  # Shared network critical
```

**Verification Steps**:
```bash
# Check network connectivity
docker exec traefik ping crowdsec
docker exec crowdsec netstat -tulpn | grep 8080

# Test API connectivity
curl -H "X-Api-Key: $(cat secrets/crowdsec-api-key)" \
     http://crowdsec:8080/v1/decisions
```

### API and Bouncer Issues

#### Bouncer Registration Failures
**Symptoms**: Traefik can't connect to CrowdSec API
**Diagnosis**:
```bash
# Check bouncer registration
docker exec crowdsec cscli bouncers list

# Test API connectivity
docker exec crowdsec cscli bouncers test
```

**Solutions**:
- [fix] API key file approach #file-api-key
  ```yaml
  # Use file-based API key instead of environment variable
  crowdsecLapiKeyFile: "/secrets/crowdsec-api-key"
  ```
- [fix] Network configuration #network-fix
  ```yaml
  # Correct API endpoint configuration
  crowdsecLapiHost: "crowdsec:8080"    # No http:// prefix
  crowdsecLapiScheme: "http"           # Separate scheme
  ```

#### Plugin Loading Issues
**Symptoms**: Traefik fails to load CrowdSec plugin
**Diagnosis**:
```bash
# Check Traefik logs for plugin errors
docker logs traefik | grep crowdsec
```

**Solutions**:
- [fix] Plugin version pinning #version-pinning
  ```yaml
  experimental:
    plugins:
      crowdsec-bouncer:
        moduleName: "github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin"
        version: "v1.3.5"  # Pin specific version
  ```
- [fix] Template syntax conflicts #template-conflicts
  - **Issue**: Traefik template syntax conflicts with Go templates
  - **Solution**: Use file-based API key instead of environment variables

### Decision and Protection Issues

#### False Positives on Admin IPs
**Symptoms**: Admin access blocked despite whitelisting
**Immediate Resolution**:
```bash
# Emergency decision removal
docker exec crowdsec cscli decisions delete --ip ADMIN_IP

# Check current decisions
docker exec crowdsec cscli decisions list
```

**Permanent Solutions**:
- [solution] Multi-layer protection #multi-layer-whitelist
  ```yaml
  # Parser level protection
  name: admin-ip-parser-whitelist
  filter: "evt.Parsed.remote_addr == '<ADMIN_HOME_IP>'"
  onsuccess: next_stage
  
  # Profile level protection  
  name: admin-ip-profile
  filter: "evt.Meta.source_ip == '<ADMIN_HOME_IP>'"
  decisions: []
  
  # Traefik middleware level
  clientTrustedIPs:
    - "<ADMIN_HOME_IP>/32"
  ```

#### Decisions Not Being Enforced
**Symptoms**: Known bad IPs continue to access services
**Diagnosis**:
```bash
# Check active decisions
docker exec crowdsec cscli decisions list

# Verify bouncer connectivity
docker exec crowdsec cscli bouncers list
```

**Solutions**:
- [fix] Middleware application #middleware-application
  ```yaml
  # Ensure CrowdSec middleware is applied to routes
  http:
    routers:
      external-service:
        middlewares:
          - crowdsec-bouncer  # Must be present
  ```
- [fix] Selective protection strategy #selective-protection
  - **Issue**: Internal services shouldn't have CrowdSec middleware
  - **Solution**: Apply protection only to external-facing services

### Logging and Detection Issues

#### SSH Attack Detection Not Working
**Symptoms**: SSH brute force attacks not generating decisions
**Diagnosis**:
```bash
# Check journal access
docker exec crowdsec journalctl --since "1 hour ago" | grep ssh

# Verify SSH scenario status
docker exec crowdsec cscli scenarios list | grep ssh
```

**Solutions**:
- [fix] Journal mounting #journal-mounting
  ```yaml
  # Ensure proper journal access
  volumes:
    - /var/log/journal:/var/log/host:ro
  ```
- [fix] Debian image requirement #debian-compatibility
  - **Issue**: Ubuntu 24.10 systemd compatibility
  - **Solution**: Use `crowdsecurity/crowdsec:latest-debian` image

#### Web Attack Detection Issues
**Symptoms**: HTTP attacks not triggering CrowdSec decisions
**Diagnosis**:
```bash
# Check Traefik log format
docker exec traefik cat /var/log/traefik/access.log | head -5

# Verify HTTP scenarios
docker exec crowdsec cscli scenarios list | grep http
```

**Solutions**:
- [fix] JSON log format requirement #json-logs
  ```yaml
  # traefik_config.yml
  accessLog:
    format: "json"
    filePath: "/var/log/traefik/access.log"
  ```
- [fix] Log acquisition configuration #log-acquisition
  ```yaml
  # acquis.yaml
  filenames:
    - /var/log/traefik/*.log
  labels:
    type: traefik
  ```

### Performance and Resource Issues

#### High CPU Usage
**Symptoms**: CrowdSec consuming excessive CPU resources
**Diagnosis**:
```bash
# Check metrics
docker exec crowdsec cscli metrics

# Monitor resource usage
docker stats crowdsec
```

**Solutions**:
- [optimization] Decision caching #decision-caching
  - **Default**: Decisions cached for performance
  - **Tuning**: Adjust cache TTL if needed
- [optimization] Log processing optimization #log-optimization
  - **Issue**: High-volume log processing
  - **Solution**: Filter logs before CrowdSec processing

#### Memory Leaks
**Symptoms**: CrowdSec memory usage continuously growing
**Diagnosis**:
```bash
# Monitor memory over time
docker stats --no-stream crowdsec

# Check for stuck processes
docker exec crowdsec ps aux
```

**Solutions**:
- [fix] Container restart strategy #restart-strategy
  ```yaml
  # Automatic restart on memory issues
  restart: unless-stopped
  ```
- [fix] Log rotation #log-rotation
  - **Issue**: Log files growing without rotation
  - **Solution**: Implement proper log rotation strategy

## Emergency Procedures

### Complete Service Isolation
**When**: Critical issues affecting all services
**Steps**:
1. **Disable CrowdSec middleware**: Remove from router configurations
2. **Stop CrowdSec container**: `docker stop crowdsec`
3. **Verify service restoration**: Test all external services
4. **Gradual re-enablement**: Restore protection incrementally

### Admin Lockout Recovery
**When**: Admin IP accidentally banned or blocked
**Emergency Access**:
```bash
# Console API access (if available)
curl -H "X-Api-Key: CONSOLE_API_KEY" \
     https://app.crowdsec.net/api/v1/decisions \
     -X DELETE -d '{"scope": "ip", "value": "ADMIN_IP"}'

# Local API access
docker exec crowdsec cscli decisions delete --ip ADMIN_IP

# Multi-layer bypass verification
docker exec crowdsec cscli parsers list | grep admin
docker exec crowdsec cscli scenarios list | grep admin
```

### Configuration Rollback
**When**: New configuration causes widespread issues
**Steps**:
1. **Identify last working configuration**: Git history or backup
2. **Stop services**: `docker compose down`
3. **Restore configuration**: Replace config files
4. **Restart services**: `docker compose up -d`
5. **Verify operation**: Test critical services

## Health Monitoring

### Regular Health Checks
```bash
# Daily status verification
docker exec crowdsec cscli status
docker exec crowdsec cscli bouncers list
docker exec crowdsec cscli metrics

# Weekly decision review
docker exec crowdsec cscli decisions list
docker exec crowdsec cscli scenarios list | grep -v OK
```

### Performance Monitoring
```bash
# Response time testing
time curl -s https://protected-service.domain.com > /dev/null

# Resource utilization
docker stats --no-stream crowdsec traefik

# Log processing rates
docker exec crowdsec cscli metrics show
```

## Diagnostic Commands Reference

### Container Health
```bash
# Container status
docker ps | grep crowdsec
docker logs crowdsec --tail 50

# Health check status
docker inspect crowdsec | grep -A 5 -B 5 Health
```

### CrowdSec Status
```bash
# Service status
docker exec crowdsec cscli status
docker exec crowdsec cscli version

# Configuration validation
docker exec crowdsec cscli config validate
```

### Network Connectivity
```bash
# Container networking
docker exec traefik ping crowdsec
docker exec crowdsec netstat -tulpn

# API connectivity
curl -f http://localhost:8080/v1/decisions
```

### Decision Management
```bash
# Current decisions
docker exec crowdsec cscli decisions list

# Decision manipulation
docker exec crowdsec cscli decisions add --ip IP --type ban -d 1h
docker exec crowdsec cscli decisions delete --ip IP
```

## Relations
- supports [[CrowdSec Security Architecture]]
- references [[CrowdSec Traefik Integration]]
- references [[CrowdSec Pangolin Integration]]
- implements [[Operations Guide]]