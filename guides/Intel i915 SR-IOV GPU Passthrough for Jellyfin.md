---
title: Intel i915 SR-IOV GPU Passthrough for Jellyfin
type: note
permalink: guides/intel-i915-sr-iov-gpu-passthrough-for-jellyfin
---

# Intel i915 SR-IOV GPU Passthrough for Jellyfin

## Overview

Complete guide for passing Intel integrated GPU to a VM using SR-IOV (Single Root I/O Virtualization) and configuring Jellyfin hardware transcoding with Intel Quick Sync Video (QSV).

## Infrastructure

- **Proxmox Host**: px-nas.lan (Intel i5-12600H - Alder Lake, 12th gen)
- **Guest VM**: media.lan (Ubuntu 25.04, VM ID 202)
- **GPU**: Intel Iris Xe Graphics (PCI 00:02.0)
- **SR-IOV**: 7 Virtual Functions (VFs) created, VF 00:02.1 passed to media-vm
- **Kernel**: Host 6.14.0 (Proxmox), Guest 6.18.0 (Ubuntu Mainline)
- **i915-sriov-dkms**: Version 2025.11.10

## SR-IOV Configuration Summary

### Host (px-nas.lan)

**Kernel Modules:**
```bash
# Check SR-IOV is loaded
lsmod | grep i915
# i915_sriov_pf loaded with 7 VFs

# Verify VF creation
ls /sys/class/drm/
# card0-7 visible (PF + 7 VFs)
```

**GPU Device Tree:**
```
00:02.0 - Physical Function (PF) - Host GPU
00:02.1 - Virtual Function 1 - Passed to media-vm ✅
00:02.2 - Virtual Function 2
00:02.3 - Virtual Function 3
00:02.4 - Virtual Function 4
00:02.5 - Virtual Function 5
00:02.6 - Virtual Function 6
00:02.7 - Virtual Function 7
```

### Guest (media.lan)

**VM Configuration** (`/etc/pve/qemu-server/202.conf`):
```
vga: std                          # Standard VGA (not Virtio)
hostpci0: 0000:00:02.1,pcie=1    # SR-IOV VF passthrough
```

**DRI Devices:**
```bash
ls -la /dev/dri/
# card0 - QEMU Standard VGA (display)
# card1 - Intel Iris Xe (SR-IOV VF)
# renderD128 - Intel Iris Xe render node ✅

# Verify mapping
ls -la /dev/dri/by-path/
# pci-0000:01:00.0-render -> ../renderD128 ✅
```

**Kernel Module:**
```bash
lsmod | grep i915
# i915 module loaded with SR-IOV support
```

**VA-API Verification:**
```bash
vainfo
# Driver: Intel iHD driver 25.1.2
# Device: Intel Iris Xe (Alder Lake)
# Profiles: H264, HEVC (8/10-bit), VP9 (8/10-bit), AV1 decode
```

## Jellyfin Configuration

### Container Setup

**Docker Compose** (`jellyfin.yml`):
```yaml
services:
  jellyfin:
    image: lscr.io/linuxserver/jellyfin:latest
    container_name: jellyfin
    environment:
      - JELLYFIN_PublishedServerUrl=https://jellyfin.nobasura.org
      - DOCKER_MODS=linuxserver/mods:jellyfin-opencl-intel
    devices:
      - /dev/dri:/dev/dri  # Pass all DRI devices
    volumes:
      - ${APP_DATA}/jellyfin:/config
      - ${DATA_DIR}/media:/data/media
      - /dev/shm:/data/transcode  # RAM-based transcoding ✅
```

**Installed Libraries in Container:**
```
intel-opencl-icd 25.40.35563.4-0
libvpl.so.2.15 (oneVPL)
libmfxhw64.so.1.35 (Intel Media SDK)
libmfx-gen.so.1.2.15 (Gen runtime)
intel-igc-opencl (Graphics Compiler)
intel-level-zero-gpu (oneAPI Level Zero)
```

### Hardware Acceleration Settings

**Dashboard → Playback → Hardware Acceleration:**

1. **Hardware Acceleration**: Intel Quick Sync Video (QSV) ✅
2. **Hardware Decoding** (Enable all supported by 12th gen):
   - ✅ H264
   - ✅ HEVC
   - ✅ HEVC 10bit
   - ✅ VP9
   - ✅ VP9 10bit
   - ✅ AV1
   - ✅ MPEG2
   - ✅ VC1
   - ✅ VP8

3. **Hardware Encoding**:
   - ✅ Enable Intel Low-Power H.264 hardware encoder
   - ✅ Enable Intel Low-Power HEVC hardware encoder
   - ❌ AV1 encode (requires 14th gen+)

4. **Tone Mapping**:
   - ✅ Enable VPP Tone mapping
   - ✅ Enable Tone mapping (OpenCL)

5. **Performance Settings**:
   - ✅ Throttle transcodes
   - ✅ Delete segments
   - Transcode path: `/data/transcode` (mapped to /dev/shm - RAM)

6. **Hardware Device**: `/dev/dri/renderD128`

### Why QSV Over VA-API?

**QSV (Intel Quick Sync Video)** is the recommended choice because:
- ✅ Confirmed GPU hardware utilization (VCS/VECS engines 60-70% active)
- ✅ Lower CPU overhead (142-173% vs 291% for VA-API)
- ✅ Better performance with HDR tone mapping
- ✅ Official Jellyfin recommendation for mainstream Intel GPUs
- ✅ Properly utilizes Intel 12th gen hardware encoders

**VA-API** observations with SR-IOV:
- ⚠️ No visible GPU activity in monitoring (`intel_gpu_top -d sriov`)
- ⚠️ Higher CPU usage (291% spikes)
- ⚠️ Possible CPU fallback or inefficient path with SR-IOV VFs
- ℹ️ VA-API is the backend for QSV on Linux, but QSV provides better abstraction

## Intel 12th Gen Alder Lake Codec Support

**Hardware Decode Support:**
- H.264 (AVC) - 8-bit
- HEVC (H.265) - 8-bit, 10-bit
- VP9 - 8-bit, 10-bit
- AV1 - 8-bit, 10-bit ✅
- MPEG-2
- VC1
- VP8

**Hardware Encode Support:**
- H.264 (AVC) - 8-bit
- HEVC (H.265) - 8-bit, 10-bit
- VP9 - 8-bit, 10-bit
- ❌ AV1 encode (requires 14th gen Arc Alchemist or newer)

**Low-Power Encoding:**
- Required for Gen 12+ (Alder Lake onwards)
- Uses VDEnc fixed-function encoder
- Requires HuC firmware (confirmed: PRELOADED ✅)
- Mandatory mode on 12th gen (exclusive, not optional)

## Performance Testing Results

### Test Configuration
- **File**: The Godfather Part II (4K HEVC 10-bit Dolby Vision/HDR10, 27GB)
- **Transcode**: 4K→480p with HDR→SDR tone mapping
- **Monitoring**: `intel_gpu_top -d sriov` on px-nas.lan

### QSV Performance ✅

**GPU Utilization (Active Transcoding):**
```
RCS (Render):          33-41%   # Compute for tone mapping
VCS (Video):           64-67%   # Video encode/decode ✅
VECS (Enhancement):    25-30%   # Scaling, tone mapping
GPU Frequency:         1296-1303 MHz (max active)
GPU Power:             4.93-5.19W
```

**CPU Usage:**
- Active transcoding: 142-173%
- Idle (buffered): 1.65-2.64%

**FFmpeg Command:**
```bash
/usr/lib/jellyfin-ffmpeg/ffmpeg \
  -init_hw_device vaapi=va:/dev/dri/renderD128,driver=iHD \
  -init_hw_device qsv=qs@va \
  -init_hw_device opencl=ocl@va \
  -filter_hw_device qs \
  -hwaccel vaapi \
  -codec:v:0 hevc_qsv \
  -low_power 1 \
  -preset veryfast \
  -vf tonemap_vaapi=format=nv12:p=bt709:t=bt709:m=bt709
```

### VA-API Performance ⚠️

**GPU Utilization:**
```
All engines: 0%
GPU Frequency: 0-966 MHz (idle)
GPU Power: 0.05-0.07W
RC6 Power Saving: 73-81% (active)
```

**CPU Usage:**
- Active transcoding: 130-291% (high spikes)
- Idle (buffered): 1.47%

**Note:** SR-IOV VF activity not visible in monitoring, high CPU suggests possible fallback.

## Monitoring GPU Activity

### Host Monitoring (px-nas.lan)

**GPU Top (SR-IOV mode):**
```bash
# Monitor SR-IOV activity
intel_gpu_top -d sriov

# Sample output during QSV transcoding:
# VCS: 64-67% (Video engine active)
# VECS: 25-30% (Video enhancement active)
# RCS: 33-41% (Render for tone mapping)
```

**List GPU Devices:**
```bash
intel_gpu_top -L
# Shows all 7 VF cards + PF
```

### Guest Monitoring (media.lan)

**Container CPU:**
```bash
docker stats jellyfin --no-stream
```

**FFmpeg Process:**
```bash
docker exec jellyfin ps aux | grep ffmpeg
```

**VA-API Info:**
```bash
docker exec jellyfin /usr/lib/jellyfin-ffmpeg/vainfo
```

### Important Notes

- ⚠️ `intel_gpu_top` without `-d sriov` will fail: "Failed to detect engines!"
- ⚠️ PMU (Performance Monitoring Unit) not exposed on SR-IOV VFs
- ✅ GPU activity is bursty: 50-80% during encoding, 0% when buffered
- ✅ This is expected and efficient behavior
- ℹ️ Transcoding throttles based on playback buffer needs

## Troubleshooting

### GPU Not Visible in Container

**Check device mapping:**
```bash
docker exec jellyfin ls -la /dev/dri/
# Should show renderD128
```

**Verify VA-API:**
```bash
docker exec jellyfin /usr/lib/jellyfin-ffmpeg/vainfo
# Should show Intel iHD driver
```

### High CPU Usage

**Expected during:**
- Initial transcode startup (file analysis)
- HDR→SDR tone mapping setup
- Seeking (rebuilding buffer)

**Concerning if sustained at 200%+ with:**
- No GPU activity visible
- Slow playback/buffering
- Check Jellyfin logs for errors

### No GPU Activity in intel_gpu_top

**Must use SR-IOV mode:**
```bash
# ❌ Wrong (will fail with SR-IOV VF)
intel_gpu_top

# ✅ Correct
intel_gpu_top -d sriov
```

### Playback Buffering/Stuttering

1. Check transcode path is RAM: `/data/transcode` → `/dev/shm`
2. Enable "Throttle transcodes"
3. Enable "Delete segments"
4. Verify GPU is active during seeks
5. Check network bandwidth to client

## Key Learnings

1. **QSV > VA-API** for SR-IOV passthrough on Intel 12th gen
2. **GPU activity is bursty** - normal to see 0% when buffer full
3. **RAM transcoding** (/dev/shm) essential for responsiveness
4. **Throttling** prevents unnecessary transcoding
5. **HDR tone mapping** works but increases CPU overhead (30-40%)
6. **Seeking triggers GPU activity** - good way to verify HW acceleration
7. **intel_gpu_top -d sriov** required for SR-IOV monitoring
8. **VCS engine 60-70% = video encoding working** ✅

## Performance Characteristics

**Initial Playback:**
- CPU spike: 150-290% (1-3 seconds)
- GPU active: 50-80% (encoding initial segments)
- Settles to idle: <3% CPU when buffered

**Seeking:**
- CPU spike: 140-170% (brief)
- GPU burst: 60-70% VCS activity
- Quick recovery: <2 seconds to resume playback

**Sustained Playback:**
- CPU: 1.5-3% (idle monitoring)
- GPU: 0% (buffer full, efficient)
- Periodic bursts as needed

## Related Documentation

- [[SR-IOV Setup Guide]] - Initial SR-IOV configuration
- [[Jellyfin Container Configuration]] - Full container setup
- [[Intel GPU Codec Support Matrix]] - Generation-specific codec support
- [[Hardware Transcoding Troubleshooting]] - Common issues and fixes

## References

- Jellyfin Docs: [Intel Hardware Acceleration](https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/intel/)
- Intel Media Driver: [iHD VA-API Driver](https://github.com/intel/media-driver)
- Intel Media SDK: [oneVPL](https://github.com/oneapi-src/oneVPL)
- SR-IOV Driver: [i915-sriov-dkms](https://github.com/strongtz/i915-sriov-dkms)

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-12-06
**Validated**: Intel i5-12600H (Alder Lake) with Jellyfin 10.11.1, Ubuntu 25.04 guest with kernel 6.18


## Boot Persistence Configuration

**Issue:** After reboot, i915 module doesn't load automatically and VFs are not created, causing VMs with SR-IOV passthrough to fail to start.

### Prerequisites

The following components must all be configured correctly for SR-IOV to work at boot:

1. **Kernel Parameters** - Tell the kernel to enable IOMMU and configure i915
2. **Module Loading** - Ensure i915 loads at boot (not blacklisted)
3. **VF Creation** - Use sysfsutils to create VFs after i915 loads

### Step 1: GRUB Kernel Parameters

Edit `/etc/default/grub` on px-nas and add to `GRUB_CMDLINE_LINUX_DEFAULT`:

```
intel_iommu=on i915.enable_guc=3 i915.max_vfs=7 module_blacklist=xe
```

**Parameters:**
- `intel_iommu=on` - Enable IOMMU for device isolation
- `i915.enable_guc=3` - Enable GuC/HuC firmware (required for SR-IOV)
- `i915.max_vfs=7` - Create up to 7 Virtual Functions at module load
- `module_blacklist=xe` - Prevent xe driver from conflicting with i915

### Step 2: Ensure i915 Module Loads at Boot

**Check for blacklist** (common issue):
```bash
grep -r 'i915' /etc/modprobe.d/
```

If you see `blacklist i915`, remove it:
```bash
sed -i '/^blacklist i915$/d' /etc/modprobe.d/blacklist.conf
```

**Add i915 to modules-load.d**:
```bash
echo "i915" > /etc/modules-load.d/i915.conf
```

### Step 3: Enable VFs at Boot (sysfsutils)

```bash
apt install sysfsutils
echo "devices/pci0000:00/0000:00:02.0/sriov_numvfs = 7" > /etc/sysfs.conf
```

### Step 4: Apply Changes

```bash
update-grub
update-initramfs -u -k all
reboot
```

### Boot Sequence

After correct configuration, the boot sequence is:
1. Kernel loads with i915 params
2. systemd-modules-load loads i915 via `/etc/modules-load.d/i915.conf`
3. i915-sriov-dkms initializes, creates sysfs path
4. sysfsutils reads `/etc/sysfs.conf` and sets `sriov_numvfs = 7`
5. VFs 00:02.1-7 are created

### Verify After Reboot

```bash
lsmod | grep i915                                         # Should show i915 loaded
ls /sys/class/drm/                                        # Should show card0-card7
cat /sys/devices/pci0000:00/0000:00:02.0/sriov_numvfs    # Should show 7
lspci | grep VGA                                          # Should show 8 devices
```

### Troubleshooting Boot Issues

**Check boot timing:**
```bash
journalctl -b | grep -E 'modules-load|i915.*Found|sysfsutils' | head -10
```

**If you see "Module 'i915' is deny-listed":**
- i915 is blacklisted somewhere - check `/etc/modprobe.d/` and remove the blacklist entry

**If sysfsutils runs before i915 loads:**
- Add i915 to `/etc/modules-load.d/i915.conf`
- Rebuild initramfs: `update-initramfs -u -k all`

### Manual Recovery (if VFs not created)

If after reboot the VFs are missing:
```bash
modprobe i915
echo 7 > /sys/devices/pci0000:00/0000:00:02.0/sriov_numvfs
# Then start the VM from Proxmox
```

---

**Updated**: 2025-12-20 - Added module loading requirements and blacklist troubleshooting


## Ubuntu 25.04 Kernel Compatibility (Guest VM)

**Issue:** The i915-sriov-dkms module fails to load in Ubuntu 25.04 VMs with kernel 6.14.x due to missing DRM symbols.

### Symptoms

```bash
modprobe i915
# modprobe: ERROR: could not insert 'i915': Unknown symbol in module

dmesg | grep intel_sriov
# intel_sriov_compat: Unknown symbol drm_dp_dpcd_read (err -2)
# intel_sriov_compat: Unknown symbol drm_gpuva_find_first (err -2)
# intel_sriov_compat: Unknown symbol drm_gpuva_ops_free (err -2)
# intel_sriov_compat: Unknown symbol drm_gpuvm_range_valid (err -2)
# intel_sriov_compat: Unknown symbol drm_dp_dpcd_write (err -2)
```

### Root Cause

Ubuntu 25.04's kernel 6.14.x doesn't export the DRM symbols that i915-sriov-dkms 2025.10.10+ requires. The newer DKMS versions target kernel 6.17/6.18's DRM API which has different symbol exports.

### Compatibility Matrix

| i915-sriov-dkms Version | Compatible Kernels | Notes |
|-------------------------|-------------------|-------|
| 2025.07.22 | 6.8 - 6.14 | Works with Ubuntu 25.04 stock kernel |
| 2025.10.10+ | 6.17+ | Requires mainline kernel upgrade |
| 2025.11.10 | 6.17+ | Requires mainline kernel upgrade |

### Solution A: Upgrade VM Kernel to 6.18 (Recommended)

**Step 1: Download kernel packages from Ubuntu Mainline**

```bash
cd /tmp

# Get available filenames (version numbers change)
curl -s https://kernel.ubuntu.com/mainline/v6.18/amd64/ | grep -oP 'href="\Klinux[^"]+\.deb'

# Download required packages (adjust version suffix as needed)
wget https://kernel.ubuntu.com/mainline/v6.18/amd64/linux-headers-6.18.0-061800-generic_6.18.0-061800.202511302339_amd64.deb
wget https://kernel.ubuntu.com/mainline/v6.18/amd64/linux-headers-6.18.0-061800_6.18.0-061800.202511302339_all.deb
wget https://kernel.ubuntu.com/mainline/v6.18/amd64/linux-image-unsigned-6.18.0-061800-generic_6.18.0-061800.202511302339_amd64.deb
wget https://kernel.ubuntu.com/mainline/v6.18/amd64/linux-modules-6.18.0-061800-generic_6.18.0-061800.202511302339_amd64.deb
```

**Step 2: Install kernel packages**

```bash
sudo dpkg -i linux-*.deb
sudo reboot
```

**Step 3: Verify new kernel**

```bash
uname -r
# Should show 6.18.0-061800-generic
```

**Step 4: Install gcc-15 (required for kernel 6.18)**

Kernel 6.18 is built with gcc-15, which is required for DKMS module compilation:

```bash
sudo apt install gcc-15
```

**Step 5: Rebuild DKMS module**

```bash
# Remove old builds
sudo dkms remove i915-sriov-dkms/2025.11.10 --all 2>/dev/null

# Reinstall to rebuild for new kernel
sudo dpkg-reconfigure i915-sriov-dkms
# Or: sudo dpkg -i /path/to/i915-sriov-dkms_2025.11.10_amd64.deb

# Verify build
dkms status
# Should show: i915-sriov-dkms/2025.11.10, 6.18.0-061800-generic, x86_64: installed
```

**Step 6: Update initramfs and reboot**

```bash
sudo update-initramfs -u -k all
sudo reboot
```

**Step 7: Verify i915 module**

```bash
lsmod | grep i915
# Should show i915 module loaded

ls -la /dev/dri/
# Should show card0, card1, renderD128

vainfo
# Should show Intel iHD driver with codec support
```

### Solution B: Downgrade DKMS (Alternative)

If kernel upgrade causes issues, use i915-sriov-dkms 2025.07.22 which is compatible with kernel 6.14:

```bash
# Download older version
wget https://github.com/strongtz/i915-sriov-dkms/releases/download/2025.07.22/i915-sriov-dkms_2025.07.22_amd64.deb

# Remove current version
sudo dkms remove i915-sriov-dkms/2025.11.10 --all
sudo apt remove i915-sriov-dkms

# Install older version
sudo dpkg -i i915-sriov-dkms_2025.07.22_amd64.deb
sudo update-initramfs -u
sudo reboot
```

### Cleanup: Remove Old Kernel Headers

After successful kernel upgrade, remove old headers to prevent DKMS from building for unused kernels:

```bash
# List installed kernels
dpkg -l | grep linux-image

# Remove old kernel headers (adjust versions)
sudo apt remove linux-headers-6.14.0-* linux-headers-6.8.0-*
sudo apt autoremove
```

---

**Added**: 2025-12-06 - Ubuntu 25.04 kernel compatibility fix (kernel 6.18 + gcc-15)
