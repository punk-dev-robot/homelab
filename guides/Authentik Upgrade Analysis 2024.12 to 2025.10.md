---
title: Authentik Upgrade Analysis 2024.12 to 2025.10
type: note
permalink: guides/authentik-upgrade-analysis-2024-12-to-2025-10
---

# Authentik Upgrade Analysis: 2024.12.2 → 2025.10.1

**Analysis Date**: November 14, 2025
**System**: Production SSO Gateway (gateway-vps)
**Risk Assessment**: MEDIUM-HIGH (Redis removal requires careful testing)
**Recommended Maintenance Window**: 30-45 minutes

## Executive Summary

Upgrading Authentik from 2024.12.2 to 2025.10.1 involves **5 major version jumps** with one critical architectural change: **complete Redis removal** in version 2025.10. This requires careful planning but database migrations are automatic. The system currently has 4 running containers (server, worker, PostgreSQL, Redis) and serves as the primary SSO provider for your infrastructure.

---

## Current State Analysis

### Deployed Version
- **Current Version**: 2024.12.2 (released December 2024)
- **Target Version**: 2025.10.1 (released November 3, 2025)
- **Release Gap**: ~11 months, 5 major versions

### Container Status
```
✓ authentik-server (2024.12.2) - 4h uptime, UNHEALTHY status
✓ authentik-worker (2024.12.2) - 4h uptime, UNHEALTHY status  
✓ authentik-postgresql (16.9 Alpine) - 4h uptime, HEALTHY
✓ authentik-redis (Alpine) - 4h uptime, HEALTHY
```

⚠️ **Pre-Upgrade Issue**: Both server and worker containers showing unhealthy status. Should investigate before upgrade.

### Current Configuration
- **PostgreSQL**: Version 16.9 (Alpine) - Compatible ✓
- **Database Size**: 32 MB (small, fast backup/restore)
- **Redis**: Alpine image (will be removed)
- **Network**: Connected to `pangolin` network for Traefik integration
- **Email**: Configured with Resend SMTP
- **Custom Templates**: Mounted at `/templates`
- **Media Files**: `/opt/appdata/authentik/media`
- **Certificates**: `/opt/appdata/authentik/certs`

### Integration Points
1. **Traefik** (`auth.nobasura.org`) - Routes traffic to authentik-server:9000
2. **CrowdSec** - Protects auth endpoints with bouncer middleware
3. **Pangolin** - SSO integration (no embedded outposts detected)
4. **Applications** - Unknown count of integrated apps (check Admin UI)

---

## Version Release Timeline

| Version | Release Date | Type | Key Changes |
|---------|--------------|------|-------------|
| 2024.12.2 | Dec 2024 | **CURRENT** | Redirect stage, Application entitlements |
| 2025.2.x | Feb 25, 2025 | Major | `:latest` tag frozen, Source stage fix |
| 2025.4.x | May 7, 2025 | Major | Reputation score limits, Session DB migration |
| 2025.6.x | June 5, 2025 | Major | PostgreSQL 15→17 upgrade path, CSS theming |
| 2025.8.x | Aug 20, 2025 | Major | OAuth2 back-channel logout, GeoIP events |
| 2025.10.1 | **Nov 3, 2025** | **TARGET** | **Redis removal**, TLS 1.3 requirement |

### Upgrade Path
**Sequential upgrade required**: 2024.12 → 2025.2 → 2025.4 → 2025.6 → 2025.8 → 2025.10

However, Authentik docs state you can jump directly to 2025.10, but you **must review each intermediate version's breaking changes**.

---

## Breaking Changes Analysis

### 🔴 CRITICAL: Version 2025.10 (Target)

#### 1. Redis Removal (BREAKING)
**Impact**: Highest
- **Change**: Authentik no longer uses Redis at all
- **Why Critical**: Complete architectural change affecting:
  - Caching (moved to PostgreSQL)
  - Task queuing (moved to PostgreSQL)
  - Embedded outpost sessions (moved to PostgreSQL)
  - WebSocket connections (moved to PostgreSQL)
  
**Migration Requirements**:
- Remove Redis container with `--remove-orphans` flag
- Remove all `AUTHENTIK_REDIS__*` environment variables
- Expect **~50% more PostgreSQL connections**
- Database will handle all caching/sessions

**Docker Compose Changes**:
```diff
- redis:
-   image: docker.io/library/redis:alpine
-   # ... entire redis service can be deleted

  server:
    environment:
-     AUTHENTIK_REDIS__HOST: redis
      # Remove this line from both server and worker
```

#### 2. PostgreSQL TLS Requirements
**Impact**: Medium (if using external PostgreSQL with TLS)
- **Change**: Requires TLS 1.3 OR Extended Master Secret extension
- **Your Setup**: Using local PostgreSQL container (no TLS) - **NOT AFFECTED** ✓

#### 3. OAuth `email_verified` Claim
**Impact**: Low-Medium (depends on app integrations)
- **Change**: Default changed from `true` → `false`
- **Action**: Check if any integrated apps require `email_verified=true`
- **Fix**: Create custom scope mapping if needed

### 🟡 MEDIUM: Version 2025.6

#### 1. PostgreSQL Image Unpinned
**Impact**: Low (you're already on v16)
- **Change**: Default PostgreSQL upgraded 15 → 17 in Helm charts
- **Your Setup**: Using Docker Compose with explicit `postgres:16-alpine` - **NOT AFFECTED** ✓
- **Optional**: Could upgrade to PostgreSQL 17 separately after Authentik upgrade

#### 2. CSS/Theming Changes
**Impact**: Low (unless custom CSS)
- **Change**: Theming system improvements may affect custom CSS
- **Your Setup**: Using custom templates, check `/templates` directory
- **Action**: Visual inspection of login flows post-upgrade

### 🟡 MEDIUM: Version 2025.4

#### 1. Reputation Score Limits
**Impact**: Low (unless custom policies)
- **Change**: Default limits -5 to +5 (previously unlimited)
- **Action**: Check if any custom policies use reputation scores
- **Fix**: Adjust limits in System > Settings if needed

#### 2. Session Storage Migration
**Impact**: Medium during rolling upgrades
- **Change**: Sessions moved from cache to database
- **Your Setup**: Docker Compose with `restart: unless-stopped` - will restart both containers together - **LOW RISK** ✓

### 🟢 LOW: Version 2025.2

#### 1. `:latest` Tag Frozen
**Impact**: None (you use explicit version tags) ✓
- **Change**: `:latest` tag frozen at 2025.2, won't update
- **Your Config**: Uses `${AUTHENTIK_VERSION:-2024.12.2}` - **GOOD PRACTICE** ✓

#### 2. Source Stage Behavior Fix
**Impact**: Low (unless using Source stages)
- **Change**: Source stage now correctly executes enrollment/auth flows
- **Action**: Test any Source-based authentication flows

### 🟢 LOW: Version 2024.12 (Current)

#### PostgreSQL Connection Pooler Settings
**Impact**: None (not using PgBouncer/PgPool) ✓
- **Deprecated**: `AUTHENTIK_POSTGRESQL__USE_PGBOUNCER` / `USE_PGPOOL`
- **Your Setup**: Direct PostgreSQL connection - **NOT AFFECTED** ✓

---

## Backup Strategy

### 1. PostgreSQL Database (CRITICAL)
**Size**: 32 MB (very small, fast backup)

**Backup Command**:
```bash
# Via Ansible
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql pg_dump -U authentik -F c -d authentik > /opt/backup/authentik_$(date +%Y%m%d_%H%M%S).dump"

# Direct (if SSH'd into gateway-vps)
docker exec authentik-postgresql pg_dump -U authentik -F c authentik > /tmp/authentik_backup_$(date +%Y%m%d_%H%M%S).dump

# Download to local machine
scp ubuntu@vps.nobasura.org:/tmp/authentik_backup_*.dump ~/backups/
```

**Verification**:
```bash
# Check backup file exists and has content
ls -lh /tmp/authentik_backup_*.dump
file /tmp/authentik_backup_*.dump  # Should show "PostgreSQL custom database dump"
```

### 2. Media Files (IMPORTANT)
**Location**: `/opt/appdata/authentik/media`
**Contents**: Logos, backgrounds, custom branding

**Backup Command**:
```bash
# Via Ansible
ansible gateway -i ansible/inventory.yml -a \
  "tar -czf /opt/backup/authentik_media_$(date +%Y%m%d).tar.gz -C /opt/appdata authentik/media"

# Direct
cd /opt/appdata
tar -czf /tmp/authentik_media_$(date +%Y%m%d).tar.gz authentik/media

# Download to local machine
scp ubuntu@vps.nobasura.org:/tmp/authentik_media_*.tar.gz ~/backups/
```

### 3. Custom Templates (IMPORTANT)
**Location**: `ansible/files/gateway-vps/authentik/config/custom-templates`
**Status**: Already in Git ✓

**Verification**:
```bash
cd /home/kuba/dev/lab
git status ansible/files/gateway-vps/authentik/config/
```

### 4. Environment Variables (CRITICAL)
**Location**: Managed by Ansible variables

**Backup Command**:
```bash
# Backup current .env file from gateway (if exists)
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-server env | grep AUTHENTIK_ > /tmp/authentik_env_backup.txt"

# Or just ensure your ansible vars are committed
cd /home/kuba/dev/lab
git log -1 --oneline ansible/group_vars/ ansible/host_vars/
```

### 5. Configuration Files (NICE-TO-HAVE)
Already in Git:
- `compose.yml` ✓
- Traefik routing rules ✓
- CrowdSec acquis configuration ✓

---

## Rollback Strategy

### Rollback Points

#### Point of No Return: Database Migration
⚠️ **Once PostgreSQL migrations run, rollback becomes complex**

**Timeline**:
1. **Before container start**: Safe to rollback (restore DB, revert compose file)
2. **After first container start**: Migrations run automatically
3. **After migrations complete**: Rollback requires database restore

### Rollback Procedure

#### If caught during upgrade (before migrations complete):
```bash
# 1. Stop all containers immediately
ansible gateway -i ansible/inventory.yml -a \
  "cd /opt/compose/authentik && docker compose down"

# 2. Restore database backup
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql pg_restore -U authentik -d authentik --clean < /tmp/authentik_backup_TIMESTAMP.dump"

# 3. Revert compose file to 2024.12.2
cd /home/kuba/dev/lab
git checkout HEAD -- ansible/files/gateway-vps/authentik/compose.yml

# 4. Redeploy old version
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml --tags authentik
```

#### If migrations already completed:
```bash
# 1. Stop containers
ansible gateway -i ansible/inventory.yml -a \
  "cd /opt/compose/authentik && docker compose down"

# 2. Drop and recreate database
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -c 'DROP DATABASE authentik;'"

ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -c 'CREATE DATABASE authentik;'"

# 3. Restore backup
ansible gateway -i ansible/inventory.yml -a \
  "docker exec -i authentik-postgresql pg_restore -U authentik -d authentik --clean < /tmp/authentik_backup_TIMESTAMP.dump"

# 4. Restore media files
ansible gateway -i ansible/inventory.yml -a \
  "tar -xzf /tmp/authentik_media_TIMESTAMP.tar.gz -C /opt/appdata"

# 5. Revert compose file and redeploy
git checkout HEAD -- ansible/files/gateway-vps/authentik/compose.yml
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml --tags authentik
```

### Rollback Testing
**Test restore procedure BEFORE upgrade**:
```bash
# Create a test restore on separate database
docker exec authentik-postgresql pg_restore -U authentik -d postgres --create /tmp/authentik_backup_TEST.dump
docker exec authentik-postgresql psql -U authentik -d postgres -c '\l'  # Verify
docker exec authentik-postgresql psql -U authentik -d postgres -c 'DROP DATABASE authentik_test;'
```

---

## Upgrade Procedure

### Pre-Flight Checklist

- [ ] Review all breaking changes above
- [ ] Check Admin UI for number of configured applications
- [ ] Check Admin UI for any custom policies using reputation scores
- [ ] Check Admin UI for any embedded outposts (should be none)
- [ ] Verify no custom CSS in `/opt/appdata/authentik/media/`
- [ ] Verify current health status (fix unhealthy containers first!)
- [ ] Announce maintenance window to users
- [ ] Backup PostgreSQL database (see Backup Strategy)
- [ ] Backup media files
- [ ] Backup environment variables
- [ ] Test backup restore procedure
- [ ] Verify Git status clean for Authentik configs
- [ ] Create VM snapshot in Proxmox (if available)

### Maintenance Window Steps

**Estimated Duration**: 30-45 minutes
**Recommended Time**: Off-peak hours (early morning/late night)

#### Phase 1: Pre-Upgrade (5 min)

```bash
# 1. Navigate to lab directory
cd /home/kuba/dev/lab

# 2. Create backup directory
ansible gateway -i ansible/inventory.yml -a "mkdir -p /opt/backup"

# 3. Backup PostgreSQL database
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql pg_dump -U authentik -F c authentik > /opt/backup/authentik_pre_upgrade_$(date +%Y%m%d_%H%M%S).dump"

# 4. Backup media files
ansible gateway -i ansible/inventory.yml -a \
  "tar -czf /opt/backup/authentik_media_$(date +%Y%m%d).tar.gz -C /opt/appdata authentik/media"

# 5. Verify backups exist
ansible gateway -i ansible/inventory.yml -a "ls -lh /opt/backup/authentik_*"

# 6. Take note of current application count
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-server ak version && docker exec authentik-postgresql psql -U authentik -d authentik -c 'SELECT COUNT(*) FROM authentik_core_application;'"
```

#### Phase 2: Update Configuration (5 min)

```bash
# 1. Edit compose file to update version and remove Redis config
nano ansible/files/gateway-vps/authentik/compose.yml
```

**Changes to make**:
```yaml
# Line 39 & 87: Update version
image: ghcr.io/goauthentik/server:${AUTHENTIK_VERSION:-2025.10.1}

# Lines 22-36: Delete entire redis service block
# REMOVE:
#  redis:
#    image: docker.io/library/redis:alpine
#    container_name: authentik-redis
#    ...
#    (entire service)

# Lines 44 & 92: Remove Redis environment variables
# REMOVE from both server and worker:
#      AUTHENTIK_REDIS__HOST: redis

# Lines 72 & 112-114: Keep PostgreSQL and Redis in depends_on for now
# (Docker will ignore Redis since it's not in services)
```

**Safer approach** - Use separate compose files:
```bash
# Backup current compose
cp ansible/files/gateway-vps/authentik/compose.yml \
   ansible/files/gateway-vps/authentik/compose.yml.2024.12.2.bak

# Create updated compose (manual edit or sed)
```

#### Phase 3: Deploy Upgrade (10-15 min)

```bash
# 1. Deploy updated configuration
ansible-playbook -i ansible/inventory.yml ansible/deploy_vps.yml --tags authentik

# Alternative: Manual deployment via SSH
ssh ubuntu@vps.nobasura.org
cd /opt/compose/authentik
docker compose pull
docker compose up -d --remove-orphans  # This removes Redis container
docker compose ps  # Should show 3 containers now (no redis)
```

**Expected output**:
```
[+] Running 4/4
 ✔ Container authentik-postgresql  Running
 ✔ Container authentik-server      Started
 ✔ Container authentik-worker      Started
 ✔ Container authentik-redis       Removed  <-- This is good!
```

#### Phase 4: Monitor Migration (10-15 min)

```bash
# 1. Watch server logs for migration process
ansible gateway -i ansible/inventory.yml -a "docker logs -f authentik-server --tail 100"

# Look for:
# - "Running migrations..." 
# - "Applied XXXX migrations"
# - "Starting server..."
# - "Listening on http://0.0.0.0:9000"

# 2. Watch worker logs
ansible gateway -i ansible/inventory.yml -a "docker logs -f authentik-worker --tail 100"

# Look for:
# - "Worker started successfully"
# - No Redis connection errors
# - Task processing messages

# 3. Monitor container health
watch -n 5 "ansible gateway -i ansible/inventory.yml -a 'docker ps --filter name=authentik'"

# Wait for healthy status (may take 2-3 minutes)
```

**Warning Signs** (require rollback):
- Repeated "migration failed" errors
- PostgreSQL connection errors
- Containers crash-looping
- Health checks failing after 5+ minutes

#### Phase 5: Verification (10 min)

```bash
# 1. Check version
ansible gateway -i ansible/inventory.yml -a "docker exec authentik-server ak version"
# Should show: 2025.10.1

# 2. Verify PostgreSQL connection count increase
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -d authentik -c 'SELECT count(*) FROM pg_stat_activity;'"
# Expected: ~50% more connections than before

# 3. Check database migrations applied
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -d authentik -c 'SELECT COUNT(*) FROM django_migrations;'"
# Should be higher than pre-upgrade count

# 4. Verify application count unchanged
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -d authentik -c 'SELECT COUNT(*) FROM authentik_core_application;'"
# Should match pre-upgrade count

# 5. Test Admin UI access
curl -I https://auth.nobasura.org/if/admin/
# Should return 200 or 307 (redirect to login)

# 6. Check Traefik integration
ansible gateway -i ansible/inventory.yml -a "docker logs traefik --tail 50 | grep authentik"
# Should show successful backend connections
```

### Post-Upgrade Testing

#### Critical Smoke Tests

1. **Admin Interface Login**
   - Navigate to: `https://auth.nobasura.org/if/admin/`
   - Action: Login with admin credentials
   - Expected: Successful login, dashboard loads
   - Check: Version shown in bottom-left: "2025.10.1"

2. **Dashboard Overview**
   - Navigate to: Dashboards > Overview
   - Check: All metrics displaying (users, apps, logins)
   - Check: No error messages or warnings

3. **Application Access Test**
   - Navigate to: Applications > Applications
   - Action: Note count, verify all expected apps listed
   - Check: No missing or broken applications

4. **SSO Flow Test** (CRITICAL)
   - Action: Open integrated app (e.g., Pangolin admin)
   - Expected: Redirect to Authentik login
   - Action: Enter credentials
   - Expected: Redirect back to app, successful auth
   - Check: User session persists on refresh

5. **User Management**
   - Navigate to: Directory > Users
   - Action: Search for test user
   - Check: User details load correctly
   - Check: Recent login events visible

6. **Event Logging**
   - Navigate to: Events > Logs
   - Check: Recent authentication events appearing
   - Check: No Redis connection errors in logs

7. **Email Testing** (if configured)
   - Action: Trigger password reset email
   - Check: Email sends successfully via Resend
   - Verify: Email received and formatted correctly

8. **Reputation System** (if used)
   - Navigate to: System > Settings
   - Check: Reputation score limits visible (-5 to +5)
   - Adjust if custom policies require different limits

9. **Custom Templates**
   - Check: Login page displays correctly
   - Check: Custom branding/logos intact
   - Check: No CSS rendering issues

#### Integration Smoke Tests

1. **Traefik Routing**
   ```bash
   # Test external access
   curl -I https://auth.nobasura.org
   # Expected: 200 OK or 307 redirect

   # Verify Traefik backend
   ansible gateway -i ansible/inventory.yml -a \
     "docker exec traefik wget -O- http://authentik-server:9000/-/health/live/"
   # Expected: Response with "healthy" status
   ```

2. **CrowdSec Protection**
   ```bash
   # Check CrowdSec logs for Authentik events
   ansible gateway -i ansible/inventory.yml -a \
     "docker logs crowdsec --tail 100 | grep authentik"
   # Should show normal access logs, no blocks
   ```

3. **Pangolin Integration**
   - Test: Login to Pangolin dashboard
   - Expected: SSO redirects to Authentik
   - Check: Successful authentication and return

4. **Integrated Applications**
   - Test each SSO-protected application:
     - [ ] Application 1: ___________
     - [ ] Application 2: ___________
     - [ ] Application 3: ___________
   - Verify: All authenticate through Authentik
   - Check: User sessions persist correctly

#### Performance Validation

```bash
# 1. Check PostgreSQL connection usage
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -d authentik -c \
  'SELECT count(*), state FROM pg_stat_activity GROUP BY state;'"

# 2. Monitor PostgreSQL cache hit ratio
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -d authentik -c \
  'SELECT sum(blks_hit)*100/sum(blks_hit+blks_read) as cache_hit_ratio FROM pg_stat_database;'"
# Expected: >95% after warmup

# 3. Check database size growth
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -d authentik -c \
  \"SELECT pg_size_pretty(pg_database_size('authentik'));\""
# Expected: Slight increase due to Redis data migration

# 4. Monitor container resource usage
ansible gateway -i ansible/inventory.yml -a "docker stats --no-stream authentik-server authentik-worker authentik-postgresql"
```

---

## Risk Assessment

### Risk Level: MEDIUM-HIGH

**Rationale**:
1. ✅ **Low Risk Factors**:
   - Small database (32 MB, fast backup/restore)
   - No PgBouncer/PgPool complexity
   - Already on PostgreSQL 16 (no major upgrade needed)
   - Not using custom CSS (minimal theme risk)
   - Explicit version tags (no surprise updates)
   - Docker Compose deployment (simpler than Kubernetes)
   - Infrastructure-as-code (easy revert)

2. ⚠️ **Medium Risk Factors**:
   - Major architectural change (Redis removal)
   - 5 version jumps (2024.12 → 2025.10)
   - Production SSO system (impacts all integrated apps)
   - Session storage migration (could affect active users)
   - Unknown count of integrated applications
   - Current unhealthy container status (pre-existing issue)

3. 🔴 **High Risk Factors**:
   - **Single point of failure**: Only authentication provider
   - **User impact**: All SSO users affected during downtime
   - **No staged rollout**: All-or-nothing upgrade
   - **Automatic migrations**: Can't preview database changes
   - **No test environment**: Upgrading directly in production

### Mitigation Strategies

1. **Timing**:
   - Schedule during lowest traffic period
   - Allow 45-60 minute window (buffer for issues)
   - Have rollback plan ready

2. **Communication**:
   - Announce maintenance window 24h advance
   - Post maintenance notice on status page
   - Have admin available via alternate auth

3. **Monitoring**:
   - Keep terminal windows open with logs
   - Monitor container health continuously
   - Have Traefik logs visible
   - Watch for user reports

4. **Rollback Readiness**:
   - Backup verified and tested
   - Rollback commands prepared in text file
   - Know rollback decision point (5 min mark)
   - Have someone available to help if needed

---

## Success Criteria

### Upgrade Considered Successful When:

- [x] All containers healthy (`docker ps` shows healthy status)
- [x] Version confirmed as 2025.10.1 (`ak version`)
- [x] Redis container removed (`docker ps` shows only 3 containers)
- [x] Admin UI accessible and loads correctly
- [x] Dashboard shows correct user/app counts
- [x] Test SSO flow completes successfully
- [x] At least 2 integrated applications tested and working
- [x] No error logs in server/worker containers (past initial startup)
- [x] PostgreSQL connection count increased but stable
- [x] Database cache hit ratio >90%
- [x] Email sending functional (if configured)
- [x] User events appearing in logs
- [x] Traefik routing working (no 502/503 errors)
- [x] CrowdSec protection still active
- [x] No user complaints about access issues

### Rollback Triggers

Initiate rollback immediately if:

- Database migrations fail repeatedly (>3 attempts)
- Containers stuck in crash-loop for >5 minutes
- PostgreSQL corruption detected
- Unable to login to Admin UI after 10 minutes
- More than 50% of integrated apps failing SSO
- Database connection errors persist after restart
- Critical data missing (users, applications)

---

## Open Questions / Pre-Upgrade Research

Before proceeding, answer these:

1. **Application Inventory**
   - [ ] How many applications are integrated with Authentik?
   - [ ] What are the critical applications that MUST work?
   - [ ] Are there any applications requiring `email_verified=true`?

2. **Current Issues**
   - [ ] Why are server/worker containers showing unhealthy status?
   - [ ] Are there any error logs indicating problems?
   - [ ] Is the current system fully functional despite unhealthy status?

3. **Custom Policies**
   - [ ] Are there any custom policies using reputation scores?
   - [ ] Do any policies need reputation limits beyond -5/+5?

4. **Outposts**
   - [ ] Are there any embedded outposts configured?
   - [ ] Are there any proxy outposts that need version matching?

5. **Business Continuity**
   - [ ] What is acceptable downtime for SSO system?
   - [ ] Is there a fallback auth method for critical systems?
   - [ ] Who needs to be notified of maintenance window?

6. **Testing Environment**
   - [ ] Can a test Authentik instance be spun up?
   - [ ] Can we test the upgrade on a clone first?
   - [ ] Is there budget/time for test environment setup?

---

## Post-Upgrade Optimization

After successful upgrade and stable operation:

### Optional Improvements

1. **PostgreSQL Upgrade to 17**
   - Benefit: Latest features and performance
   - Risk: Medium (separate migration process)
   - Timeline: 1-2 weeks after Authentik stable

2. **Review Reputation Score Policies**
   - Navigate: System > Settings > Reputation
   - Adjust limits if needed for custom policies

3. **Audit OAuth Scope Mappings**
   - Check if any apps need `email_verified=true`
   - Create custom mappings if required

4. **Update Documentation**
   - Update internal docs with new version
   - Document any behavioral changes noticed
   - Update runbooks with new troubleshooting

5. **Monitor Long-term Performance**
   - Track PostgreSQL query performance
   - Monitor connection pool usage
   - Evaluate if more DB tuning needed
   - Consider connection pooling if high load

6. **Custom CSS Review**
   - If using custom CSS, review new theming system
   - Optimize for new features in 2025.10

---

## References

- [Authentik 2025.10 Release Notes](https://docs.goauthentik.io/releases/2025.10)
- [Authentik Upgrade Guide](https://docs.goauthentik.io/install-config/upgrade)
- [Authentik 2025.2 Breaking Changes](https://docs.goauthentik.io/releases/2025.2)
- [Authentik 2025.4 Breaking Changes](https://docs.goauthentik.io/releases/2025.4)
- [Authentik 2025.6 PostgreSQL Upgrade](https://docs.goauthentik.io/releases/2025.6)
- [Authentik 2025.8 Release Notes](https://docs.goauthentik.io/releases/2025.8)
- [Redis Removal Documentation](https://docs.goauthentik.io/releases/2025.10#redis-removal)

---

## Quick Reference Commands

```bash
# Check current version
ansible gateway -i ansible/inventory.yml -a "docker exec authentik-server ak version"

# View server logs
ansible gateway -i ansible/inventory.yml -a "docker logs authentik-server --tail 100"

# Check container health
ansible gateway -i ansible/inventory.yml -a "docker ps --filter name=authentik"

# Backup database
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql pg_dump -U authentik -F c authentik > /opt/backup/authentik_$(date +%Y%m%d_%H%M%S).dump"

# Restore database
ansible gateway -i ansible/inventory.yml -a \
  "docker exec -i authentik-postgresql pg_restore -U authentik -d authentik --clean < /opt/backup/authentik_TIMESTAMP.dump"

# Restart services
ansible gateway -i ansible/inventory.yml -a "cd /opt/compose/authentik && docker compose restart"

# Check PostgreSQL connections
ansible gateway -i ansible/inventory.yml -a \
  "docker exec authentik-postgresql psql -U authentik -d authentik -c 'SELECT count(*) FROM pg_stat_activity;'"

# Run gateway VPS tests
ansible-playbook -i ansible/inventory.yml ansible/tests/suites/gateway_vps_test_suite.yml
```

---

**Analysis Completed**: November 14, 2025
**Next Action**: Review open questions and pre-upgrade health check
**Contact**: Kuba (homelab administrator)
