---
title: Oracle Cloud VPS Backup Strategy
type: note
permalink: guides/oracle-cloud-vps-backup-strategy
tags:
- backup
- oracle-cloud
- disaster-recovery
- vps
- critical
---

# Oracle Cloud VPS Backup Strategy

## Overview

The gateway VPS (`vps.nobasura.org`) is a critical single point of failure running:
- Pangolin (tunnel infrastructure)
- Traefik (external routing)
- CrowdSec (security)
- Auth-bypass (SSO)
- Beszel monitoring
- Dozzle logs

**Backup Method**: Oracle Cloud Boot Volume Snapshots
- 100% complete system backup (OS + all Docker volumes)
- Fast restore (5-10 minutes)
- Point-in-time recovery
- Automated scheduling available

## Critical Volumes to Protect

Located on VPS at `/opt/docker/compose/pangolin/`:
- `pangolin_db` - Pangolin database (users, resources, config)
- `letsencrypt` - SSL certificates
- `crowdsec_db` - CrowdSec decisions and ban lists
- `gerbil` - WireGuard keys and tunnel config

## Method 1: Manual Snapshots (Oracle Cloud Console)

### Creating a Manual Snapshot

1. **Access Oracle Cloud Console**
   - Navigate to https://cloud.oracle.com
   - Sign in to your tenancy

2. **Navigate to Boot Volumes**
   - Hamburger menu → **Compute** → **Instances**
   - Click your VPS instance name
   - Under **Resources** (left sidebar) → Click **Boot volume**
   - Click the boot volume name link

3. **Create Snapshot**
   - Click **"Create Boot Volume Backup"** button
   - **Name**: `vps-manual-YYYY-MM-DD` (e.g., `vps-manual-2025-11-11`)
   - **Backup Type**: **Full**
   - **Compartment**: (leave default)
   - Click **"Create Boot Volume Backup"**

4. **Wait for Completion**
   - Status will show "Creating..." then "Available"
   - Typical time: 5-10 minutes for 50GB volume

### When to Use Manual Snapshots

- Before major infrastructure changes
- Before Pangolin upgrades
- Before Ansible playbook deployments that modify VPS config
- After adding new critical services

## Method 2: Automated Snapshots (Backup Policies)

### Setting Up Automated Backup Policy

1. **Navigate to Backup Policies**
   - Oracle Cloud Console → Hamburger menu
   - **Storage** → **Block Storage** → **Backup Policies**

2. **Create Custom Policy** (Recommended)
   - Click **"Create Backup Policy"**
   - **Name**: `vps-daily-backup-policy`
   - **Compartment**: (your compartment)

3. **Configure Schedule**
   ```
   Schedule 1 - Daily Incrementals:
   - Period: Daily
   - Hour: 02:00 UTC (3am UK time)
   - Backup Type: Incremental
   - Retention: 7 days
   
   Schedule 2 - Weekly Full:
   - Period: Weekly
   - Day: Sunday
   - Hour: 03:00 UTC
   - Backup Type: Full
   - Retention: 4 weeks
   
   Schedule 3 - Monthly Full:
   - Period: Monthly
   - Day: 1st
   - Hour: 04:00 UTC
   - Backup Type: Full
   - Retention: 3 months
   ```

4. **Click "Create Backup Policy"**

### Assign Policy to Boot Volume

1. **Navigate to Boot Volume**
   - Compute → Instances → Your VPS → Boot volume

2. **Assign Backup Policy**
   - Click **"Assign"** under "Backup Policy"
   - Select your `vps-daily-backup-policy`
   - Click **"Assign"**

3. **Verify**
   - Policy will show as "Assigned"
   - First backup runs at next scheduled time
   - Check "Boot Volume Backups" tab to see automated backups

### Using Oracle Predefined Policies (Quick Option)

Oracle provides 3 predefined policies:

| Policy | Schedule | Retention | Use Case |
|--------|----------|-----------|----------|
| **Bronze** | Weekly full | 4 weeks | Low-criticality |
| **Silver** | Daily incremental, Weekly full | 7 days + 4 weeks | Medium-criticality |
| **Gold** | Daily incremental, Weekly full, Monthly full | 7 days + 4 weeks + 12 months | High-criticality |

**Recommendation**: Use **Gold** policy for VPS (high-criticality)

## Method 3: OCI CLI Automated Snapshots

### Installing OCI CLI

On your local machine (not VPS):

```bash
# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Verify installation
oci --version
```

### Configuring OCI CLI

```bash
# Run setup wizard
oci setup config

# Provide when prompted:
# - User OCID: (from Oracle Console → Profile → User Settings)
# - Tenancy OCID: (from Oracle Console → Profile → Tenancy)
# - Region: (e.g., uk-london-1)
# - Generate new RSA key pair: Y
```

**Add public key to Oracle Cloud:**
1. Oracle Console → Profile → User Settings
2. Resources → **API Keys**
3. Click **Add API Key**
4. Paste contents of `~/.oci/oci_api_key_public.pem`
5. Click **Add**

### Finding Your Boot Volume OCID

```bash
# List all boot volumes
oci bv boot-volume list --compartment-id <YOUR_COMPARTMENT_OCID>

# Or find via instance
oci compute instance list --compartment-id <YOUR_COMPARTMENT_OCID>
oci compute boot-volume-attachment list --availability-domain <AD> --compartment-id <COMPARTMENT_OCID>
```

Save your boot volume OCID for scripting.

### Creating Snapshot via CLI

```bash
#!/bin/bash
# Script: /home/kuba/scripts/oracle-vps-snapshot.sh

BOOT_VOLUME_OCID="ocid1.bootvolume.oc1.uk-london-1.xxx"
SNAPSHOT_NAME="vps-manual-$(date +%Y-%m-%d-%H%M)"

echo "Creating boot volume snapshot: $SNAPSHOT_NAME"

oci bv boot-volume-backup create \
  --boot-volume-id "$BOOT_VOLUME_OCID" \
  --display-name "$SNAPSHOT_NAME" \
  --type FULL

echo "Snapshot creation initiated. Check Oracle Console for completion."
```

**Make executable:**
```bash
chmod +x /home/kuba/scripts/oracle-vps-snapshot.sh
```

### Automating with Cron (Optional)

Only use if NOT using Oracle Backup Policies (avoid duplicate backups):

```bash
# Edit crontab
crontab -e

# Add: Weekly snapshot every Sunday at 3am
0 3 * * 0 /home/kuba/scripts/oracle-vps-snapshot.sh >> /var/log/oracle-vps-snapshot.log 2>&1
```

## Restore Procedures

### Emergency Restore (VPS Failure)

**Estimated Time**: 10-15 minutes total

#### Step 1: Locate Snapshot

1. Oracle Cloud Console → **Storage** → **Boot Volume Backups**
2. Find most recent successful backup
3. Note the backup OCID or name

#### Step 2: Create Instance from Snapshot

1. **Navigate to Instances**
   - Compute → Instances → Click **"Create Instance"**

2. **Configure Instance**
   - **Name**: `vps-restored` (or same name if old instance deleted)
   - **Image**: Click **"Change Image"**
   - **Boot Volume**: Click **"Change Boot Volume"**
   - Select **"Boot Volume Backups"**
   - Choose your snapshot
   - Click **"Select Boot Volume Backup"**

3. **Networking** (CRITICAL)
   - **VCN**: Select same VCN as original
   - **Subnet**: Select same subnet
   - **Assign Public IP**: Yes
   - Note the new public IP address

4. **SSH Keys**
   - Paste your existing SSH public key
   - (Same key that was on original instance)

5. **Click "Create"**

6. **Wait for Provisioning**
   - Status: Provisioning → Running
   - Time: 2-5 minutes

#### Step 3: Update DNS

New instance will have different public IP. Update DNS records:

**Cloudflare DNS Updates**:
```
A record: vps.nobasura.org → <NEW_IP>
A record: *.nobasura.org → <NEW_IP>
```

**Propagation**: 1-5 minutes with Cloudflare

#### Step 4: Verify Services

```bash
# SSH to new instance
ssh ubuntu@<NEW_IP>

# Check Docker containers
docker ps

# Expected containers running:
# - pangolin
# - gerbil
# - traefik
# - crowdsec
# - beszel-agent
# - dozzle

# Test Pangolin
curl -I https://pangolin.nobasura.org

# Test protected service
curl -I https://homepage.lab.nobasura.org
```

#### Step 5: Test Homelab Connectivity

From local machine:
```bash
# Test homepage (through Pangolin tunnel)
curl -I https://homepage.lab.nobasura.org

# Check Beszel connection
# (Visit https://beszel.nobasura.org - VPS should appear online)
```

### Partial Restore (Specific Volume Recovery)

If you only need to restore specific data (e.g., Pangolin database):

1. **Create temporary instance from snapshot** (as above)
2. **SSH to temporary instance**
3. **Copy volume data**:
   ```bash
   # Example: Restore Pangolin database
   docker run --rm -v pangolin_db:/source -v $(pwd):/backup \
     alpine tar czf /backup/pangolin_db.tar.gz -C /source .
   ```
4. **Transfer to current VPS**:
   ```bash
   scp pangolin_db.tar.gz ubuntu@vps.nobasura.org:/tmp/
   ```
5. **Restore on current VPS**:
   ```bash
   # Stop Pangolin
   cd /opt/docker/compose/pangolin
   docker compose stop pangolin
   
   # Restore volume
   docker run --rm -v pangolin_db:/target -v /tmp:/backup \
     alpine tar xzf /backup/pangolin_db.tar.gz -C /target
   
   # Start Pangolin
   docker compose start pangolin
   ```
6. **Delete temporary instance** (to avoid charges)

## Testing Restore (Quarterly Recommended)

**Schedule**: Every 3 months, test restore procedure

1. **Choose off-peak time** (Sunday 2am)
2. **Create test instance from latest snapshot**
3. **Verify all services start**
4. **Test one critical function** (e.g., access homepage through tunnel)
5. **Document any issues**
6. **Delete test instance within 1 hour**
7. **Update runbook if procedure changed**

## Monitoring and Alerts

### Verify Backups Are Running

**Weekly Check** (Monday morning):
1. Oracle Console → Boot Volume Backups
2. Verify backups from past week exist
3. Check "State" is "Available" (not "Failed")

### Backup Retention Verification

Current retention (with Gold policy):
- **Daily incrementals**: 7 days (7 snapshots)
- **Weekly full**: 4 weeks (4 snapshots)
- **Monthly full**: 12 months (12 snapshots)
- **Total**: ~23 snapshots at any time

### Storage Costs

Oracle Cloud snapshot pricing (UK London region):
- **Boot volume backup**: ~$0.0255/GB/month
- **Estimated cost** for 50GB volume with Gold policy:
  - Daily incrementals (~5GB each x 7): $0.89/month
  - Weekly full (~50GB each x 4): $5.10/month
  - Monthly full (~50GB each x 12): $15.30/month
  - **Total**: ~$21/month for comprehensive backup

**Note**: First 10GB included in free tier (check current allowance)

## Recovery Time Objectives (RTO/RPO)

| Metric | Target | Actual |
|--------|--------|--------|
| **RPO** (Recovery Point Objective) | 24 hours | 1-24 hours (daily backups) |
| **RTO** (Recovery Time Objective) | 30 minutes | 10-15 minutes (snapshot restore) |
| **Data Loss** (worst case) | 1 day | Up to 24 hours of changes |

## Disaster Scenarios

### Scenario 1: VPS Becomes Unresponsive
- **Detection**: Monitoring alerts, services unreachable
- **Action**: Attempt reboot via Oracle Console
- **Fallback**: Restore from snapshot (15 min)
- **Impact**: 15-30 min downtime

### Scenario 2: Corrupted Docker Volumes
- **Detection**: Services failing, database errors
- **Action**: Partial restore of specific volume
- **Fallback**: Full restore from snapshot
- **Impact**: 30-60 min downtime

### Scenario 3: Accidental Configuration Change
- **Detection**: Services broken after config change
- **Action**: Revert via Git + Ansible redeploy
- **Fallback**: Restore from snapshot before change
- **Impact**: 5-15 min downtime (revert), 15 min (restore)

### Scenario 4: Oracle Region Failure
- **Detection**: Cannot access Oracle Console
- **Action**: Wait for Oracle region recovery
- **Mitigation**: Snapshots stored in same region (limitation)
- **Impact**: Dependent on Oracle SLA
- **Future**: Consider cross-region snapshot copies (manual)

## Quick Reference Commands

### Oracle CLI - List Snapshots
```bash
# List all boot volume backups
oci bv boot-volume-backup list --compartment-id <COMPARTMENT_OCID>

# Get snapshot details
oci bv boot-volume-backup get --boot-volume-backup-id <BACKUP_OCID>
```

### Oracle CLI - Create Manual Snapshot
```bash
oci bv boot-volume-backup create \
  --boot-volume-id <BOOT_VOLUME_OCID> \
  --display-name "vps-manual-$(date +%Y-%m-%d)" \
  --type FULL
```

### Oracle CLI - Delete Old Snapshot
```bash
oci bv boot-volume-backup delete --boot-volume-backup-id <BACKUP_OCID>
```

## Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Verify automated backups ran | Weekly (Monday) | Kuba |
| Test restore procedure | Quarterly (Q1, Q2, Q3, Q4) | Kuba |
| Review retention policy | Annually (January) | Kuba |
| Review storage costs | Monthly | Kuba |
| Update documentation | As needed after changes | Kuba |

## Related Documentation

- **Pangolin Configuration**: `memory://guides/operations-guide`
- **VPS Deployment**: `ansible/deploy_vps.yml`
- **Infrastructure Overview**: `memory://architecture/system-architecture-overview`

## Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2025-11-11 | Initial backup strategy created | VPS identified as SPOF with no backups |

---

**Last Updated**: 2025-11-11  
**Next Review**: 2026-01-11