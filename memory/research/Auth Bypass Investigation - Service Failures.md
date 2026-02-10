---
title: Auth Bypass Investigation - Service Failures
type: note
permalink: research/auth-bypass-investigation-service-failures
---

# Auth Bypass Investigation - Service Failures

## Problem
Auth bypass tests failing for jellyseerr, sonarr, and radarr:
- Expected: Direct access with bypass header
- Actual: 302 redirect to Pangolin auth
- Status: This worked before, now broken

## Failed Services
1. **jellyseerr** - redirecting to resource/38
2. **sonarr** - redirecting to resource/40  
3. **radarr** - redirecting to resource/41

## Investigation Required
- Check if auth bypass configuration changed
- Verify bypass keys are correctly configured
- Compare current vs previous Traefik routing
- Check if Pangolin service configurations changed
- Verify environment variables are loaded

## Critical Note
This is a regression - functionality that previously worked is now broken.

#investigation #auth-bypass #regression #critical