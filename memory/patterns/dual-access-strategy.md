# Dual Access Strategy

## Overview
Every service supports both web auth and mobile/API access through Traefik routing priorities.

## Priority Routing Pattern
```yaml
# Priority routing: Bypass (300) > Auth (100)
service-mobile-bypass:
  rule: "Host(`service.nobasura.org`) && Header(`traefik-auth-bypass-key`, `${KEY}`)"
  priority: 300
  
service-auth:
  rule: "Host(`service.nobasura.org`)"
  priority: 100
  middlewares: ["auth@file"]
```

## Implementation Details

### Bypass Route (Priority 300)
- Triggered by special header: `traefik-auth-bypass-key`
- Value stored in environment variable for security
- No authentication middleware applied
- Direct access to service

### Auth Route (Priority 100)
- Default route for all requests
- Applies authentication middleware
- Web users get login prompt
- Protects against unauthorized access

## Use Cases

### Mobile Applications
- iOS Shortcuts
- Android apps
- API clients
- Automation tools

### Web Access
- Browser access with authentication
- Session-based login
- Secure by default

## Security Considerations
- Bypass key must be kept secret
- Use environment variables, never hardcode
- Rotate keys periodically
- Monitor access logs

## Example Configuration
```yaml
# In docker-compose.yml
labels:
  # Mobile bypass route
  - "traefik.http.routers.jellyfin-mobile-bypass.rule=Host(`jellyfin.lab.nobasura.org`) && Header(`traefik-auth-bypass-key`, `${TRAEFIK_AUTH_BYPASS_KEY}`)"
  - "traefik.http.routers.jellyfin-mobile-bypass.priority=300"
  
  # Standard auth route
  - "traefik.http.routers.jellyfin-auth.rule=Host(`jellyfin.lab.nobasura.org`)"
  - "traefik.http.routers.jellyfin-auth.priority=100"
  - "traefik.http.routers.jellyfin-auth.middlewares=auth@file"
```

## Related Notes
- [Ansible Commands Quick Reference](ansible-commands-quick-reference.md) - Deployment commands
- [Critical Infrastructure Rules](../core/critical-infrastructure-rules.md) - Infrastructure rules
- [Troubleshooting Guide](../reference/troubleshooting-guide.md) - Common auth issues