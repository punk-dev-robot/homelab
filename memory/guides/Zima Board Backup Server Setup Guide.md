---
title: Zima Board Backup Server Setup Guide
type: note
permalink: guides/zima-board-backup-server-setup-guide
---

# Zima Board Backup Server Setup Guide

## Overview

This guide sets up a single 2TB SSD with degraded RAID 1 (ready for second drive), partitioned for Proxmox Backup Server (1.2TB) and btrbk laptop backups (800GB), with bonded 2x2.5GbE network.

**Hardware:**
- Zima Board (Intel N105, 16GB RAM)
- 1x 2TB SSD (/dev/sda) - second drive to be added later
- 2x 2.5GbE network interfaces
- Proxmox Backup Server already installed on internal MMC

**Architecture:**
```
/dev/sda (2TB SSD)
  ↓
mdadm RAID 1 (degraded, /dev/md0)
  ↓
LVM Volume Group (vg-backup)
  ├─ pbs-datastore (1.2TB) → ext4 → /mnt/pbs-datastore
  └─ laptop-backups (800GB) → btrfs → /mnt/btrbk
```

---

## Step 1: Prerequisites & Verification

### 1.1 Verify the drive

```bash
# List all block devices
lsblk

# Verify /dev/sda is your 2TB drive
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT /dev/sda

# Check if anything is using the drive
mount | grep sda
```

**Expected output:** You should see /dev/sda with ~2TB size, not mounted.

### 1.2 Identify network interfaces

```bash
# List network interfaces
ip link show

# Identify your 2x 2.5GbE interfaces
# Look for interfaces like enp1s0, enp2s0, eth0, eth1, etc.
ip -br link show
```

**Note down the two interface names** - you'll need them for bonding setup. Let's assume `enp1s0` and `enp2s0` for this guide.

---

## Step 2: Network Bond Configuration

### 2.1 Install bonding support (if not already present)

```bash
# Install ifenslave for bonding
apt update
apt install -y ifenslave

# Load bonding kernel module
modprobe bonding

# Ensure it loads on boot
echo "bonding" >> /etc/modules
```

### 2.2 Configure bond interface

**Option A: Using /etc/network/interfaces (traditional)**

```bash
# Backup existing network config
cp /etc/network/interfaces /etc/network/interfaces.backup

# Edit network configuration
nano /etc/network/interfaces
```

Add the following configuration (adjust interface names and IP as needed):

```
# Bonding configuration
auto bond0
iface bond0 inet static
    address 192.168.1.50        # Change to your network
    netmask 255.255.255.0
    gateway 192.168.1.1         # Change to your gateway
    bond-slaves enp1s0 enp2s0   # Your interface names
    bond-mode 1                 # active-backup (use 4 for LACP if switch supports it)
    bond-miimon 100
    bond-downdelay 200
    bond-updelay 200

# Slave interfaces
auto enp1s0
iface enp1s0 inet manual
    bond-master bond0

auto enp2s0
iface enp2s0 inet manual
    bond-master bond0
```

**Bond modes explanation:**
- **Mode 1 (active-backup)**: One active, one standby. Works with any switch. 2.5Gbps active + failover.
- **Mode 4 (802.3ad LACP)**: Link aggregation. Requires switch support. Up to 5Gbps combined.

Choose mode 1 unless your switch supports LACP.

### 2.3 Apply network configuration

```bash
# Restart networking
systemctl restart networking

# Or reboot to be safe
reboot

# After reboot, verify bond is up
ip addr show bond0
cat /proc/net/bonding/bond0

# Test connectivity
ping -c 3 192.168.1.1  # Your gateway
```

**Expected output:** bond0 should show as UP with your IP address. The bonding status should show both slaves.

---

## Step 3: Storage Setup - Degraded RAID 1

### 3.1 Prepare the drive

**⚠️ WARNING: This will destroy all data on /dev/sda!**

```bash
# Wipe any existing filesystem signatures
wipefs -a /dev/sda

# Verify it's clean
lsblk -f /dev/sda
```

### 3.2 Create degraded RAID 1 array

```bash
# Create RAID 1 with one device (degraded)
# The 'missing' keyword reserves space for the second drive
mdadm --create /dev/md0 \
    --level=1 \
    --raid-devices=2 \
    /dev/sda missing

# You'll be prompted to confirm - type 'y'
```

**What this does:** Creates a RAID 1 (mirror) array that currently only has one drive. The second drive slot is reserved as "missing" and can be added later without rebuilding.

### 3.3 Verify RAID array

```bash
# Check RAID status
cat /proc/mdstat

# Detailed array info
mdadm --detail /dev/md0
```

**Expected output:**
```
Personalities : [raid1]
md0 : active raid1 sda[0]
      1953383360 blocks super 1.2 [2/1] [U_]
```

The `[U_]` indicates one disk active, one missing.

### 3.4 Save RAID configuration

```bash
# Scan and save the array configuration
mdadm --detail --scan | tee -a /etc/mdadm/mdadm.conf

# Update initramfs to include RAID config
update-initramfs -u

# Verify it's saved
cat /etc/mdadm/mdadm.conf
```

**Why:** This ensures the RAID array is assembled automatically on boot.

---

## Step 4: LVM Setup

### 4.1 Create LVM physical volume

```bash
# Initialize /dev/md0 as LVM physical volume
pvcreate /dev/md0

# Verify
pvdisplay /dev/md0
```

### 4.2 Create volume group

```bash
# Create volume group named 'vg-backup'
vgcreate vg-backup /dev/md0

# Verify
vgdisplay vg-backup
```

**Expected output:** Should show ~1.86TB total size.

### 4.3 Create logical volumes

```bash
# Create PBS datastore volume (1.2TB)
lvcreate -n pbs-datastore -L 1.2T vg-backup

# Create btrbk volume (800GB)
lvcreate -n laptop-backups -L 800G vg-backup

# Verify both volumes
lvdisplay vg-backup
lvs
```

**Expected output:** Two logical volumes:
- `/dev/vg-backup/pbs-datastore` (1.2TB)
- `/dev/vg-backup/laptop-backups` (800GB)

---

## Step 5: Create Filesystems

### 5.1 Format PBS volume with ext4

```bash
# Create ext4 filesystem on PBS volume
mkfs.ext4 -L pbs-datastore /dev/vg-backup/pbs-datastore

# Verify
lsblk -f /dev/vg-backup/pbs-datastore
```

**Why ext4:** Simple, stable, proven. PBS handles compression and checksums, so we don't need ZFS features here.

### 5.2 Format btrbk volume with btrfs

```bash
# Create btrfs filesystem on btrbk volume
mkfs.btrfs -L laptop-backups /dev/vg-backup/laptop-backups

# Verify
lsblk -f /dev/vg-backup/laptop-backups
```

**Why btrfs:** Native format for btrbk, provides efficient snapshots and subvolumes.

---

## Step 6: Mount Filesystems

### 6.1 Create mount points

```bash
# Create mount directories
mkdir -p /mnt/pbs-datastore
mkdir -p /mnt/btrbk
```

### 6.2 Mount filesystems

```bash
# Mount PBS datastore
mount /dev/vg-backup/pbs-datastore /mnt/pbs-datastore

# Mount btrbk volume
mount /dev/vg-backup/laptop-backups /mnt/btrbk

# Verify
df -h | grep backup
```

### 6.3 Configure automatic mounting (fstab)

```bash
# Backup fstab
cp /etc/fstab /etc/fstab.backup

# Add entries to fstab
cat >> /etc/fstab << 'EOF'

# Backup volumes
/dev/vg-backup/pbs-datastore  /mnt/pbs-datastore  ext4   defaults  0  2
/dev/vg-backup/laptop-backups /mnt/btrbk          btrfs  defaults  0  2
EOF

# Verify fstab syntax
mount -a

# Check everything is still mounted
df -h | grep backup
```

---

## Step 7: Configure Proxmox Backup Server

### 7.1 Set permissions

```bash
# Set ownership for PBS datastore
chown -R backup:backup /mnt/pbs-datastore
chmod 750 /mnt/pbs-datastore
```

### 7.2 Access PBS Web UI

1. Open browser: `https://<zima-ip>:8007`
2. Login with root credentials
3. Navigate to **Configuration → Datastore**
4. Click **Add Datastore**
5. Configure:
   - **Name:** `zima-backup` (or your preference)
   - **Backing Path:** `/mnt/pbs-datastore`
   - **GC Schedule:** `daily` (garbage collection)
   - **Prune Schedule:** Configure retention (e.g., keep 7 daily, 4 weekly, 3 monthly)
6. Click **Add**

### 7.3 Test PBS from Proxmox

On your Proxmox host:

1. Navigate to **Datacenter → Storage → Add → Proxmox Backup Server**
2. Configure:
   - **ID:** `zima-pbs`
   - **Server:** `<zima-ip>`
   - **Username:** `root@pam`
   - **Password:** (set in PBS)
   - **Datastore:** `zima-backup`
   - **Namespace:** (optional)
3. Click **Add**

Test with a small VM backup:
```bash
# On Proxmox host
vzdump <vmid> --storage zima-pbs --mode snapshot
```

---

## Step 8: Configure btrbk Mount

### 8.1 Create btrfs subvolume structure

```bash
# Create subvolume for laptop backups
btrfs subvolume create /mnt/btrbk/laptop

# Create .snapshots directory for btrbk
mkdir -p /mnt/btrbk/laptop/.snapshots

# Verify
btrfs subvolume list /mnt/btrbk
```

### 8.2 Set permissions

```bash
# Create backup user if needed (or use your user)
# Replace 'kuba' with your username
chown -R kuba:kuba /mnt/btrbk/laptop
chmod 750 /mnt/btrbk/laptop
```

### 8.3 Configure SSH access for btrbk

On the Zima board:

```bash
# Ensure SSH is running
systemctl status sshd
systemctl enable sshd

# Create .ssh directory for your user
mkdir -p /home/kuba/.ssh
chmod 700 /home/kuba/.ssh
```

On your laptop, add SSH key:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519

# Copy public key to Zima
ssh-copy-id kuba@<zima-ip>

# Test SSH connection
ssh kuba@<zima-ip> "echo SSH works"
```

### 8.4 Example btrbk configuration for laptop

On your laptop, edit `/etc/btrbk/btrbk.conf`:

```
# Snapshot source
snapshot_dir .snapshots
snapshot_preserve_min 2d
snapshot_preserve 7d 4w 3m

# Target on Zima board
target_preserve_min no
target_preserve 7d 4w 6m

volume /
  subvolume /
    target ssh://kuba@<zima-ip>/mnt/btrbk/laptop
```

Test btrbk:

```bash
# Dry run
sudo btrbk -v dryrun

# Actual backup
sudo btrbk run
```

---

## Step 9: Verification & Testing

### 9.1 Verify RAID array

```bash
# Check RAID status
cat /proc/mdstat
mdadm --detail /dev/md0

# Should show [U_] - one active, one missing
```

### 9.2 Verify LVM

```bash
# Check physical volume
pvs

# Check volume group
vgs

# Check logical volumes
lvs

# Full display
pvdisplay
vgdisplay
lvdisplay
```

### 9.3 Verify mounts

```bash
# Check all mounts
mount | grep backup
df -h | grep backup

# Verify fstab
cat /etc/fstab | grep backup

# Test remount
umount /mnt/pbs-datastore
umount /mnt/btrbk
mount -a
df -h | grep backup
```

### 9.4 Verify network bond

```bash
# Check bond status
cat /proc/net/bonding/bond0

# Should show:
# - Bonding Mode: fault-tolerance (active-backup) or IEEE 802.3ad
# - MII Status: up
# - Both slave interfaces listed

# Test bandwidth (optional)
iperf3 -s  # On another machine
iperf3 -c <other-machine-ip>  # On Zima
```

### 9.5 Test PBS datastore

```bash
# Check PBS datastore status
proxmox-backup-manager datastore list

# Check disk usage
proxmox-backup-manager datastore status zima-backup
```

### 9.6 Test btrfs snapshots

```bash
# Create test snapshot
btrfs subvolume snapshot /mnt/btrbk/laptop /mnt/btrbk/laptop/.snapshots/test-snapshot

# List snapshots
btrfs subvolume list /mnt/btrbk

# Delete test snapshot
btrfs subvolume delete /mnt/btrbk/laptop/.snapshots/test-snapshot
```

---

## Step 10: Monitoring & Health Checks

### 10.1 RAID monitoring

```bash
# Check RAID health daily
cat /proc/mdstat

# Set up email alerts for RAID events
nano /etc/mdadm/mdadm.conf
# Add: MAILADDR your-email@example.com

# Test email notification
mdadm --monitor --scan --test --oneshot
```

### 10.2 LVM monitoring

```bash
# Check volume group health
vgs -o +lv_health_status

# Check logical volume health
lvs -o +lv_health_status
```

### 10.3 Filesystem health

```bash
# Check ext4 (PBS)
tune2fs -l /dev/vg-backup/pbs-datastore | grep -i error

# Check btrfs (btrbk)
btrfs device stats /mnt/btrbk
btrfs filesystem usage /mnt/btrbk
```

---

## Future: Adding Second Drive for Full RAID 1

When you get your second 2TB drive:

```bash
# Identify second drive (e.g., /dev/sdb)
lsblk

# Add to RAID array
mdadm --add /dev/md0 /dev/sdb

# Monitor rebuild progress
watch cat /proc/mdstat

# After rebuild completes (takes hours), verify
mdadm --detail /dev/md0
# Should now show [UU] - both drives active!
```

**During rebuild:**
- Array remains fully functional
- Performance may be slightly reduced
- Do NOT interrupt the process

---

## Troubleshooting

### RAID array not assembling on boot

```bash
# Check mdadm config
cat /etc/mdadm/mdadm.conf

# Rescan and update
mdadm --detail --scan >> /etc/mdadm/mdadm.conf
update-initramfs -u

# Manually assemble
mdadm --assemble --scan
```

### LVM volumes not activating

```bash
# Scan for volume groups
vgscan

# Activate all volume groups
vgchange -ay

# Verify
lvs
```

### Mount fails on boot

```bash
# Check fstab syntax
mount -a

# Check filesystem
fsck /dev/vg-backup/pbs-datastore
btrfs check /dev/vg-backup/laptop-backups  # Use only if unmounted!
```

### Network bond not working

```bash
# Check bond status
cat /proc/net/bonding/bond0

# Restart networking
systemctl restart networking

# Or reload interfaces
ifdown bond0 && ifup bond0

# Check logs
journalctl -u networking
```

### PBS datastore issues

```bash
# Check datastore status
proxmox-backup-manager datastore list

# Verify disk space
df -h /mnt/pbs-datastore

# Check PBS logs
tail -f /var/log/proxmox-backup/api/access.log
tail -f /var/log/proxmox-backup/tasks/active
```

---

## Summary

**What you have:**
- ✅ Single 2TB SSD in degraded RAID 1 (ready for second drive)
- ✅ LVM with flexible partitioning
- ✅ PBS datastore (1.2TB ext4)
- ✅ btrbk backup volume (800GB btrfs)
- ✅ Bonded 2x2.5GbE network
- ✅ Auto-mounting on boot
- ✅ Ready for production backups

**Next steps (future):**
- Add second drive for full RAID 1 mirror
- Configure PBS sync to TrueNAS
- Configure btrbk sync to TrueNAS
- Set up remote replication
- Integrate with monitoring

**Key commands reference:**
```bash
# RAID status
cat /proc/mdstat
mdadm --detail /dev/md0

# LVM status
pvs; vgs; lvs

# Mounts
df -h | grep backup

# Bond status
cat /proc/net/bonding/bond0

# PBS status
proxmox-backup-manager datastore list
```

---

## Links

- Related: [[Zima Board Hardware Specs]]
- Related: [[btrbk Configuration Guide]]
- Related: [[PBS Remote Sync Configuration]] (future)
- Related: [[TrueNAS Replication Setup]] (future)