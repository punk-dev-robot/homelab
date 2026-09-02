# KUB-43 — Proxmox capacity headroom + Talos VM sizing

**Date:** 2026-09-02 (data captured live from the running cluster)
**Scope:** read-only fact gathering on `proxmox` inventory group (10.10.101.11-13). No changes made.
**Cluster:** `pve-manager/9.1.2`, kernel `6.17.4-1-pve` (verified on px-cpu via `pveversion`).

---

## Question

Per Proxmox node: what is total vs. allocated vs. actually-used CPU/RAM and free storage,
which guests live where, and what spec should three new Talos VMs (one per node, combined
control-plane + worker) get?

## Answer (short)

There is comfortable room on **px-cpu** and **px-nas** and effectively **no room on px-net**
without freeing something first. Recommended: **px-cpu 6 vCPU / 12 GiB**, **px-nas 6 vCPU / 12 GiB**,
**px-net 4 vCPU / 8 GiB — but only after capping `zfs_arc_max` there and shrinking OPNsense VM 101
from 16 GiB / 6 cores to 8 GiB / 4 cores**, which is *proposed, not yet justified*: in-guest OPNsense
demand was not measured and it is the primary firewall. If that shrink proves unsafe, run px-net at
6 GiB tainted control-plane-only instead. Capping `zfs_arc_max` on **both px-net and px-nas is a hard
prerequisite** — both currently have no cap at all (30 GiB and 93 GiB ceilings), and the inventory
value intended for px-net is applied on px-cpu instead. All three VMs get a **100 GiB raw OS disk on
`app-storage` plus a separate 100 GiB disk for future CSI** (the pool is `sparse: 0`, so that is
200 GiB reserved per node up front), ballooning **disabled**, `q35` + `ovmf` + 4 MB EFI disk,
`VirtIO SCSI` (not "Single"), `cache=none`, `virtio` NIC, CPU type `host`.

---

## 1. Per-node capacity

### Cluster totals (source: `pvesh get /nodes` on px-cpu, live)

| Node | CPU model | Threads | RAM total | RAM in use (host) | Node disk (root fs) |
|---|---|---|---|---|---|
| px-cpu (10.10.101.11) | 13th Gen Intel Core i9-13900H | 20 | 94.03 GiB (100965904384 B) | 52.6 GiB | 237 G, 228 G free |
| px-net (10.10.101.12) | Intel Core 3 N355 | 8 | 31.08 GiB (33378496512 B) | 24.6 GiB | 465 G, 452 G free |
| px-nas (10.10.101.13) | 12th Gen Intel Core i5-12600H | 16 | 93.92 GiB (100845531136 B) | 65.7 GiB | 931 G, 874 G free |

Cluster CPU load at capture time was trivial: `cpu` 0.068 / 0.022 / 0.009 (px-cpu / px-net / px-nas)
from `pvesh get /cluster/resources`. **CPU is not the binding constraint anywhere except px-net's
core count.** RAM and (on px-net) core oversubscription are.

### px-cpu — 20 threads, 94.03 GiB RAM

| Guest | Type | Cores | RAM max | Balloon floor | Disk (volsize) | Notes |
|---|---|---|---|---|---|---|
| 102 `opnsense2` | VM | 4 | 8196 MB | 4098 MB | 64 G scsi0 | `onboot:1`, cpu `host` |
| 201 `docker-obs` | VM | 4 | 16382 MB | 8192 MB | 128 G virtio0 | obs stack |
| 203 `docker-apps` | VM | 4 | 16384 MB | 8192 MB | 256 G virtio0 | apps stack |
| **Allocated** | | **12 / 20** | **40.00 GiB** | 20.00 GiB | 448 G | |

- ZFS ARC: `c_max` 9.40 GiB, current `size` 9.37 GiB (pinned by `/etc/modprobe.d/*zfs*`:
  `options zfs zfs_arc_max=10096738304`).
- `free -m`: total 96288, used 53903, **available 42384 MiB (41.4 GiB)**.
- Accounting checks out: 40.0 (VM max) + 9.4 (ARC) + ~2.5 (PVE/host) ≈ 51.9 vs 52.6 GiB used.
- Storage `app-storage` (zfspool): pool 928 G, ALLOC 195 G, FREE 733 G; **dataset AVAIL 443 G**.
- No swap. KSM: `run=0`, `pages_sharing=0` (KSM off).
- **Headroom: ~42 GiB RAM, 8 spare threads, 443 G pool. Roomy.**

### px-net — 8 threads, 31.08 GiB RAM  ← the tight node

| Guest | Type | Cores | RAM max | Balloon floor | Disk | Notes |
|---|---|---|---|---|---|---|
| 101 `opnsense` | VM | 6 | 16382 MB | *no `balloon:` key* → fixed 16 GiB | 64 G scsi0 | primary firewall, `onboot:1` |
| 121 `unifi` | LXC | 2 | 2048 MB | — | 8 G | |
| 122 `px-datacenter-manager` | LXC | 2 | 2048 MB | — | 10 G | |
| 153 `pihole` | LXC | 2 | 2048 MB | — | 2 G | HA-managed (`hastate: started`) |
| **Allocated** | | **12 / 8 (1.5× oversubscribed)** | **22.00 GiB** | | 84 G | |

- ZFS ARC: `c_max` **30.08 GiB** (no `/etc/modprobe.d` zfs entry found), current `size` 5.01 GiB.
- `free -m`: total 31832, used 25206, **available only 6625 MiB (6.5 GiB)**.
- Storage `app-storage`: pool 928 G, ALLOC 27.4 G, FREE 901 G; **dataset AVAIL 827 G**.
- No swap. KSM `run=0` but `pages_sharing=75949` (~297 MB residual from an earlier run).
- **Headroom: ~6.5 GiB RAM (and ARC is free to grow toward 30 GiB), zero spare threads,
  827 G pool. Storage is fine; RAM and cores are not.**

### px-nas — 16 threads, 93.92 GiB RAM

| Guest | Type | Cores | RAM max | Balloon floor | Disk (volsize) | Notes |
|---|---|---|---|---|---|---|
| 200 `truenas-scale` | VM | 4 | 32768 MB | `balloon: 0` → fixed 32 GiB | 32 G scsi0 | `numa:0`, tags nas/nfs/storage |
| 202 `docker-media` | VM | 4 | 16384 MB | 8192 MB | 256 G virtio0 | media stack |
| **Allocated** | | **8 / 16** | **48.00 GiB** | | 288 G | |

- ZFS ARC: `c_max` **92.92 GiB** (kernel default, no modprobe override), current `size` 14.49 GiB
  and still climbing (node uptime only 21.5 days vs 87 days on the others).
- `free -m`: total 96173, used 67309, **available 28863 MiB (28.2 GiB)**.
- Storage `app-storage`: pool 928 G, ALLOC 52.6 G, FREE 875 G; **dataset AVAIL 607 G**.
- Swap: 32 G swapfile, 0 B used.
- **Headroom: ~28 GiB RAM today, 8 spare threads, 607 G pool — but ARC has no ceiling,
  so "available" will shrink over time.**

### Storage pools (source: `pvesh get /storage`)

| Storage | Type | Nodes | Content | Note |
|---|---|---|---|---|
| `app-storage` | zfspool, pool `app-storage`, mount `/app-storage` | px-net, px-nas, px-cpu | images, rootdir | **`sparse: 0` → thick provisioned.** A 100 GiB volume takes a 100 GiB refreservation immediately. Not shared — each node has its own local pool of the same name. |
| `local-btrfs` | btrfs `/var/lib/pve/local-btrfs` | all | iso, vztmpl | Where the Talos ISO must be uploaded. |
| `local` | dir `/var/lib/vz` | all | vztmpl, backup, iso | **`disable: 1`** — not usable. |
| `pbs-zima` | pbs, server `10.10.10.34`, datastore `pbs-local`, user `backup@pbs` | all (shared) | backup | `prune-backups: keep-all=1`. Reported `status: "unknown"` in `/cluster/resources` at capture time. |

PBS is an **external host** at `10.10.10.34`, not a VM on any of the three nodes.

### Networking (relevant to VM placement)

All three nodes expose `vmbr0`–`vmbr3`, VLAN-aware (`bridge-vids 2-4094`), with
`vmbr2.101` carrying the 10.10.101.x management network and `vmbr3.102`/`vmbr3.103` as
further tagged interfaces. Talos VMs would most plausibly attach to `vmbr2` with VLAN tag
101 — see UNVERIFIED below.

---

## 2. Talos requirements (primary sources)

Sidero Labs documentation, **identical numbers across v1.11, v1.12 and v1.13** (v1.13 is the
current stable per the docs site's own version banner):

| Role | Memory | Cores | System Disk |
|---|---|---|---|
| Control Plane (minimum) | 2 GiB | 2 | 10 GiB |
| Worker (minimum) | 1 GiB | 1 | 10 GiB |
| Control Plane (recommended) | 4 GiB | 4 | 100 GiB |
| Worker (recommended) | 2 GiB | 2 | 100 GiB |

- v1.11: <https://www.talos.dev/v1.11/introduction/system-requirements/>
- v1.12: <https://docs.siderolabs.com/talos/v1.12/getting-started/system-requirements>
- v1.13: <https://docs.siderolabs.com/talos/v1.13/getting-started/system-requirements>

> "Talos Linux itself only requires less than 100 MB of disk space, but the EPHEMERAL partition
> is used to store pulled images, container work directories, and so on. Thus a minimum of
> 10 GiB of disk space is required. 100 GiB is recommended." — v1.11 system-requirements

> "For production, it is often more efficient to dedicate a smaller disk for the Talos
> installation itself, and use additional disks for workload storage." — same page

**This confirms the 4 GiB floor in the task brief** (that is the *recommended* CP figure; the hard
minimum is 2 GiB). For a combined CP+worker node the roles stack, so recommended-CP (4 GiB / 4
cores) + recommended-worker (2 GiB / 2 cores) ≈ **6 GiB / 6 cores as the realistic "comfortable"
floor before any actual workload**, which is why 8–16 GiB is the sane operating band.

### Talos-on-Proxmox baseline (Sidero official guide, v1.11)

<https://www.talos.dev/v1.11/talos-guides/install/virtualized-platforms/proxmox/>

| Setting | Recommended value | Reason given |
|---|---|---|
| BIOS | `ovmf` (UEFI) | modern firmware, Secure Boot |
| Machine | `q35` | PCIe machine type |
| CPU type | `host` | best performance; **prevents live migration** |
| CPU cores | 2+ control plane, 4+ workers | minimum 2 |
| Memory | **4 GB+ control plane, 8 GB+ workers**; minimum 2 GB | |
| Disk controller | **`VirtIO SCSI` — NOT "VirtIO SCSI Single"** | "Single" can cause bootstrap hang / disk-discovery failure (siderolabs/talos#11173) |
| Disk format | Raw (perf) or QCOW2 (snapshots) | raw preferred |
| Disk cache | Write Through (or None in clustered envs) | |
| Network model | `virtio` | |
| EFI disk | 4 MB | required for OVMF |
| **Ballooning** | **Disabled** | "Talos doesn't support memory hotplug" / can break memory detection |
| RNG | VirtIO RNG (optional) | entropy |

**Two deviations from common Proxmox practice are deliberate, and both are contested:**

- *`VirtIO SCSI` rather than `VirtIO SCSI Single`.* Proxmox's own default for new VMs is
  `virtio-scsi-single` (+ iothread), which is normally the faster choice with two disks per VM.
  The Talos guide explicitly overrides this because "Single" has been observed to hang bootstrap
  or prevent disk discovery (siderolabs/talos#11173). **Follow the Talos guide** — correctness
  before throughput — but revisit once that issue is confirmed fixed in the version deployed.
- *`cache=Write Through`.* The Talos guide's "safe default", but `cache=none` is the more common
  recommendation on ZFS zvols and writethrough can add write latency — which matters for etcd.
  The guide itself offers `None` "for clustered environments", which this is. **Suggest
  `cache=none` here** and treat the guide's writethrough as the conservative fallback.
  *(UNVERIFIED: not benchmarked on this hardware.)*

The guide also notes the QEMU guest agent is **not** in the stock image — a custom Image Factory
build with the `siderolabs/qemu-guest-agent` extension is needed for graceful guest shutdown.

---

## 3. Recommended Talos VM specs

Ballooning **must be off**, so every GiB assigned is a GiB actually consumed. Budget accordingly.

| | px-cpu | px-nas | px-net |
|---|---|---|---|
| vCPU (cores, 1 socket) | **6** | **6** | **4** |
| RAM (balloon disabled) | **12 GiB** | **12 GiB** | **8 GiB** *(6 GiB if 101 is not shrunk — see below)* |
| OS disk | **100 GiB** raw, `app-storage`, VirtIO SCSI controller, `cache=none`, discard+ssd on | same | same |
| Extra CSI disk | **100 GiB** raw, `app-storage`, second disk on the same VirtIO SCSI controller | same | same |
| Firmware / machine | `ovmf` + 4 MB EFI disk, `q35`, cpu `host`, numa 0 | same | same |
| NIC | `virtio` on `vmbr2`, VLAN tag 101 | same | same |
| `onboot` | 1 | 1 | 1 |

Total per node: 200 GiB thick-provisioned on `app-storage`.

**Intended role split:** all three are combined control-plane + worker, but the sizing is
deliberately asymmetric. px-cpu and px-nas at 12 GiB are expected to carry the real workload;
px-net at 8 GiB is sized for control-plane duty plus light workloads only. If px-net ends up at
6 GiB (OPNsense not shrunk), taint it control-plane-only so the scheduler does not place
workloads there.

### Post-deployment headroom

| Node | vCPU after | RAM committed after | Pool AVAIL after (thick) | Verdict |
|---|---|---|---|---|
| px-cpu | 18 / 20 threads | 40.0 (VMs) + 12.0 (Talos) + 9.4 (ARC cap) + ~2.5 host = **63.9 of 94.0 GiB** → ~30 GiB spare | 443 G → **~243 G** | Comfortable |
| px-nas | 14 / 16 threads | 48.0 + 12.0 + ARC + ~2.5 host = **62.5 + ARC of 93.9 GiB** → ~31 GiB spare *only if ARC is capped* | 607 G → **~407 G** | Comfortable once `zfs_arc_max` is set |
| px-net | 14 / 8 threads (1.75×) | 8.0 (shrunk 101) + 6.0 (CTs) + 8.0 (Talos) + 4.0 (ARC cap) + ~2.0 host = **28.0 of 31.1 GiB** → ~3 GiB spare | 827 G → **~627 G** | Tight but workable |

### Prerequisites on px-net (in order)

**1. Cap `zfs_arc_max` on px-net to ~4 GiB — this is a hard prerequisite, not just drift.**
`c_max` is currently 30.08 GiB on a 31.08 GiB node. Even after every other change below,
allocations reach ~22 GiB and leave ~9 GiB for host + ARC; an uncapped ARC will expand into
exactly the memory the Talos VM needs, and the two new thick 100 GiB zvols will generate the
I/O that makes it do so. Set the cap and reboot **before** the Talos VM is placed here.

**2. Shrink VM 101 `opnsense`: 16382 MB → 8192 MB, cores 6 → 4. — PROPOSED, NOT YET JUSTIFIED.**
It is a firewall on an 8-thread N355 host holding half the node's RAM and 75% of its threads,
and it has no `balloon:` key so all 16 GiB is pinned. That makes it the obvious donor. But
**actual demand inside the guest was not measured** — Suricata, ZenArmor, large state tables
and pf fragment queues are real consumers, and this task was read-only against Proxmox only.
Before committing:
- inspect OPNsense's own memory/CPU usage (dashboard, `top`, `pfctl -si` state count) under
  normal and peak load;
- confirm which IDS/IPS packages are enabled;
- schedule a maintenance window — VM 101 is the primary firewall with `onboot: 1` and the whole
  network depends on it; a memory/core change requires a full VM reboot.
If 8 GiB turns out to be too small, do **not** proceed with 8 GiB for the Talos VM on this node;
fall back to the control-plane-only option below.

**3. Accept the CPU trade-off — oversubscription gets worse, not better.**
Post-change px-net runs 4 (opnsense) + 6 (LXCs) + 4 (Talos) = **14 vCPU on 8 threads, 1.75×**,
up from the current 1.5×. LXC `cores` are limits rather than reservations and the containers are
near-idle, so this is probably tolerable — but etcd is latency-sensitive and would be sharing
threads with OPNsense packet processing, and etcd fsync latency on this storage was not
benchmarked (see Risks). If scheduling jitter appears, pin OPNsense to dedicated cores or drop
the Talos node here to 2 vCPU control-plane-only.

**4. Optional:** `pihole` / `unifi` / `px-datacenter-manager` are LXCs at 2 GiB each — LXC memory
is a ceiling not a reservation, so they are cheaper than they look; leave them unless pressed.

If shrinking OPNsense proves unsafe, the fallback is **px-net at 2–4 vCPU / 6 GiB, tainted
control-plane-only** (Talos CP recommended is 4 GiB, so 6 GiB gives etcd + kubelet real room),
with all workload scheduling weight on px-cpu and px-nas. Do **not** go below 4 GiB on a node
that also runs etcd.

### Also fix before deploying (px-nas)

**Cap `zfs_arc_max` on px-nas — also a prerequisite, not optional.** Current ceiling is 92.92 GiB (kernel default) with ARC already at
14.49 GiB after only 21 days uptime. Without a cap, the 28 GiB of "available" RAM will be eaten by
ARC and the Talos VM will end up competing with it.

---

## 4. Contradictions / drift found

**ZFS ARC settings in `ansible/inventory.yml` do not match the live hosts.**

| Host | Inventory `pve_zfs_options` | Actual `/etc/modprobe.d/*zfs*` | Actual runtime `c_max` |
|---|---|---|---|
| px-cpu | *(none set)* | `options zfs zfs_arc_max=10096738304` (9.40 GiB) | 9.40 GiB |
| px-net | `zfs_arc_max=10095689728` (9.40 GiB) | *(no arc entry)* | 30.08 GiB |
| px-nas | `zfs_arc_max=3338665984` (3.11 GiB) | *(no arc entry)* | 92.92 GiB |

The value the inventory assigns to **px-net** is applied on **px-cpu** instead (off by 1048576
bytes, i.e. the same intent), and neither px-net nor px-nas has any ARC cap at all. This is the
single most consequential finding for Talos sizing on px-net and px-nas.

No other contradictions surfaced. Talos requirement numbers were consistent across all three
documentation versions checked (v1.11 / v1.12 / v1.13).

---

## 5. Risks

- **Thick provisioning.** `app-storage` is `sparse: 0`, so a 100 GiB Talos disk reserves 100 GiB
  the moment it is created — there is no "it'll only use what it needs". px-cpu's pool is the
  most consumed (AVAIL 443 G against 928 G raw); two 100 GiB volumes there leave ~243 G.
- **etcd on ZFS.** All three Talos nodes would run etcd, which is fsync-latency sensitive. The
  pools are NVMe-backed (`/dev/nvme1n1p3`, `/dev/nvme2n1p3`), which should be adequate, but
  etcd write latency on ZFS-on-NVMe under Proxmox was **not measured** here.
- **Quorum.** Three combined CP+worker nodes means losing any one node is survivable, losing two
  is not. px-net is both the weakest node and an etcd voter — a memory-pressure OOM there costs
  a third of the quorum.
- **px-net CPU oversubscription** goes to 1.75× (14 vCPU on 8 threads). The LXCs are near-idle so
  this is likely fine, but Talos node under load will contend with OPNsense packet processing on
  the same threads. OPNsense is latency-sensitive — consider CPU pinning if jitter appears.
- **`cpu: host` blocks live migration.** Already true for every existing VM in this cluster;
  the Talos guide recommends it anyway. Accept, or plan cold migrations only.
- **No KSM, no swap on px-cpu/px-net.** No memory-overcommit safety net; the allocation numbers
  above are hard. px-nas has a 32 G swapfile (unused).
- **`local` storage is disabled** cluster-wide, so the Talos ISO must go to `local-btrfs`
  (`iso,vztmpl` content) — the official Proxmox guide's "select the local storage" step does not
  apply as written here.
- **Backups.** `pbs-zima` reported `status: "unknown"` at capture time. Talos VMs also lack a
  guest agent unless a custom Image Factory image with `siderolabs/qemu-guest-agent` is used,
  so PBS snapshots would be crash-consistent. For Talos the durable state is etcd, so plan
  `talosctl etcd snapshot` regardless of PBS.

---

## 6. UNVERIFIED

- **Network attachment for the Talos VMs.** `vmbr2` + VLAN tag 101 is inferred from the presence
  of `vmbr2.101` carrying the 10.10.101.x management addresses and from all bridges being
  VLAN-aware. The full `/etc/network/interfaces` was not dumped and no existing VM's `netN:`
  line was read to confirm which bridge/tag the docker VMs actually use. **Confirm before
  building.**
- **How `pve_zfs_options` is consumed** by the Proxmox role in this repo — the role source was
  not read (task is read-only, scoped to fact gathering). The drift in §4 is established from the
  live hosts, but whether it is an un-run playbook, a role bug, or an intentional manual override
  is unknown.
- **`pbs-zima` reachability.** `status: "unknown"` may simply mean the shared PBS storage was not
  polled at that instant rather than that it is down. Not probed (10.10.10.34 is outside the
  allowed read-only host list for this task).
- **etcd/ZFS fsync latency.** Not benchmarked.
- **Actual guest-internal memory pressure** in the docker VMs. `memhost` from `/cluster/resources`
  shows 201/202/203 each sitting at ~16 GiB host-side despite 8 GiB balloon floors, i.e. the
  balloon is not currently reclaiming. Whether these VMs genuinely need 16 GiB or are merely
  page-cache-fat was not determined — if they are fat, there is more reclaimable headroom on
  px-cpu and px-nas than this brief assumes.
- **Whether a CSI driver choice** (Longhorn / OpenEBS local-path / democratic-csi against the
  existing TrueNAS VM 200) has been made. The 100 GiB extra disk recommendation assumes a
  replicated block CSI; a TrueNAS-backed NFS/iSCSI CSI would make the extra disk unnecessary.
- **Talos version to deploy.** Docs banner indicates v1.13 is current stable; no decision recorded.

---

## Commands used (all read-only)

```
ssh root@10.10.101.{11,12,13}
pveversion
pvesh get /nodes --output-format json
pvesh get /cluster/resources --output-format json
pvesh get /storage --output-format json
qm list ; qm config <id>
pct list ; pct config <id>
zpool list ; zfs list -o name,used,avail,refer,volsize -d 1
free -m ; df -h / ; swapon --show ; lscpu
cat /proc/spl/kstat/zfs/arcstats ; cat /etc/modprobe.d/*zfs*
cat /sys/kernel/mm/ksm/{run,pages_sharing}
grep ... /etc/network/interfaces
```
