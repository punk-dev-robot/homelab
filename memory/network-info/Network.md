# Network Architecture

## WAN

- 1 Gbps uplink, 1 Gbps downlink
- rj45 wall socket
- provided by local ISP (Hyproptic), static IP

## VLANS

- 1 - LAN (default), should be unused
- 10 - LAB, for homelab services
- 11 - UNUSED
- 40 - USER, for user devices
- 60 - IOT, for IOT devices
- 101 - MGMT, for management interfaces
- 102 - CARP, for OpnSense CARP interfaces
- 666- WAN, for external access, should be available only on flex mini and blocked on main switch

## Ubiquiti Flex Mini - used for high availability Internet access for Opnsense, 1 Gbps, poe in

- port 1 - poe in/mgmt, VLAN 101
- port 2 - wan
- port 3 - px-net (enp2s0)
- port 4 - px-nas (enp88s0)

## Zyxel XMG-1920 - main switch

- 8x 2.5Gbps ports, poe out
- 2x 10Gbps SFP+ ports
- Full config: ./config_XMG1915_250629_043538.log

## px-net - firewall appliance mini-pc, main network services

- running proxmox
- intel N355, 8 cores
- 32 GB DDR4 RAM
- 2x 2.5Gbps ethernet ports, 2x 10Gpps SFP+ ports
- 500GB boot nvme ssd
- 1TB services nvme ssd
- network config: ./px-net_network_config.txt
- main opnsense vm config: ./config-opn1.lan-20250629050844.xml

## px-nas - NAS mini-pc, storage services, fallback for network services

- running proxmox
- 12th Gen Intel(R) Core(TM) i5-12600H (16 cores)
- 96 GB DDR5 RAM
- 2x 2.5Gbps ethernet ports, 2x 10Gpps SFP+ ports
- 1TB boot nvme ssd
- 1TB services nvme ssd
- SAS 2008 LSI Controller passed through to Truenas VM, connected to 2x 16TB HDDs in ZFS mirror
- network config: ./px-nas_network_config.txt
- secondary opnsense vm config - synced with main opnsense config

## Hardware Expansion plans

### Now

- px-cpu - new mini-pc, to be added (see below for details)

### Short term (next 2 months)

- new mini-pc, intel N100, 4 cores, 16 GB DDR4 RAM, 2x2.5Gbps eth ports, will be used as main proxmox-backup-server

### Medium term (next 6 months)

- possibly new switch, 8x 10Gbps eth ports, 8x 10Gpbs SFP+ ports
- possibly replacement of px-net with box identical to px-nas
- possibly external gpu card for px-cpu

## Next task

I have new mini-pc, px-cpu (i would appreciate proposal of aternative names) ready to add to the network:

- intel core i9, 13th gen, 24 cores
- 96 GB DDR5 RAM
- 1TB boot nvme ssd
- 2TB very fast nvme ssd

Goals:

- phase 1: document network architecture, including VLANs, devices, and their roles. Include network diagrams if possible, maybe multiple using c4 model - this should be interactive session with user, where you ask clarifying questions
- phase 2: plan with user best way to integrate px-cpu into the network, considering its hardware capabilities and potential roles - this also should be interactive session with user, where you ask clarifying questions
