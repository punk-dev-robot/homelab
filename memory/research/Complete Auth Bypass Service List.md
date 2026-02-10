---
title: Complete Auth Bypass Service List
type: note
permalink: research/complete-auth-bypass-service-list
---

# Complete Auth Bypass Service List

## Required Auth Bypass Services
The following services should ALL have auth bypass functionality configured:

### Media Management Services
1. **sabnzbd** - Usenet downloader
2. **nzbget** - Alternative usenet downloader  
3. **sonarr** - TV series management
4. **radarr** - Movie management
5. **lidarr** - Music management
6. **readarr** - Book/ebook management
7. **overseerr** - Media request management (note: test shows jellyseerr, need to verify)
8. **bazarr** - Subtitle management
9. **prowlarr** - Indexer management

### Current Test Status
Tests are only checking 3 services:
- jellyseerr (possibly should be overseerr?)
- sonarr ✅
- radarr ✅

### Missing from Tests
6+ services not being tested for auth bypass:
- sabnzbd
- nzbget  
- lidarr
- readarr
- bazarr
- prowlarr

### Critical Gap
The force file replacement wiped out ALL auth bypass routes, not just the 3 being tested. This means 6+ additional services lost their bypass functionality.

### Required Actions
1. Add ALL 9 services to `dynamic_config.yml` with dual access pattern
2. Update test suite to verify ALL 9 services  
3. Verify all services have proper backend connectivity
4. Deploy and test comprehensive solution

### Priority
**CRITICAL** - This affects mobile app access to all media management services.

#auth-bypass #media-services #testing #comprehensive