---
title: Modern CLI Tools Analysis - User Preferences
type: note
permalink: research/modern-cli-tools-analysis-user-preferences
---

# Modern CLI Tools Analysis - User Preferences

## Discovered User Toolkit (Arch Laptop)

Comprehensive analysis of Kuba's existing modern CLI tools for informed hypervisor tool selection.

### File Operations & Navigation
- **eza** - Modern ls replacement (aliased as `ls`)
- **fd** - Better find
- **dust** - Modern du replacement
- **yazi** - File manager TUI
- **zoxide** - Smart cd replacement
- **choose** - Alternative to cut/awk

### Text Processing & Analysis
- **ripgrep (rg)** - Fast grep replacement (aliased for piping: `G`)
- **bat** - Better cat with syntax highlighting
- **sd** - Modern sed replacement
- **fzf** - Fuzzy finder for files/history

### System Monitoring & Performance
- **bottom** - Modern htop replacement (preferred over htop)
- **procs** - Modern ps replacement  
- **bandwhich** - Network usage by process
- **btop** - Alternative system monitor
- **stress-ng** - System stress testing

### Network & Connectivity
- **gping** - Ping with graphs
- **trippy** - Modern traceroute with TUI
- **duf** - Modern df replacement

### Development & Git
- **neovim** - Modern vim
- **lazygit** - Git TUI
- **git-delta** - Better git diffs
- **tokei** - Code statistics

### Shell & Productivity
- **atuin** - Shell history sync
- **starship** - Cross-shell prompt
- **tealdeer** - Fast tldr implementation
- **hyperfine** - Benchmarking tool

### Utilities
- **lazydocker** - Docker management TUI
- **ncdu** - Interactive disk usage

## Key Insights for Hypervisor Selection

### User Preferences Identified
1. **bottom over htop** - Clearly prefers bottom for system monitoring
2. **Comprehensive Rust ecosystem** - Heavy investment in modern Rust tools
3. **TUI applications** - Prefers terminal UIs (lazygit, yazi, bottom)
4. **Productivity focused** - Tools that enhance workflow efficiency
5. **Network monitoring** - Strong toolkit for network analysis (gping, bandwhich, trippy)

### Hypervisor Relevance Assessment

#### Essential for Hypervisor
- **bottom** - Perfect for VM resource monitoring
- **bandwhich** - Critical for tracking VM network usage
- **dust** - Essential for VM storage monitoring
- **procs** - Better process monitoring for VMs
- **ripgrep** - Log analysis when troubleshooting
- **gping/trippy** - Network connectivity debugging

#### Nice-to-Have for Hypervisor
- **bat** - Better config file reading
- **fd** - Finding VM configs quickly
- **fzf** - Fuzzy finding in logs/configs
- **jq** - Proxmox API interaction

#### Skip for Hypervisor (VM-Appropriate)
- **lazygit/lazydocker** - Development tools
- **tokei** - Code analysis
- **hyperfine** - Benchmarking
- **yazi** - File manager (tmux + cli tools sufficient)

## Configuration Strategy

### Respect User Preferences
- Use **bottom** instead of htop in configurations
- Include tools user already knows and loves
- Match naming conventions and usage patterns

### Hypervisor-Specific Additions
New tools that complement existing toolkit:
- **glances** - Web-based monitoring for remote access
- **sampler** - Custom dashboard creation
- **oha** - HTTP load testing for VM services

### Installation Methods Alignment
- **Cargo tools** - User already has Rust ecosystem
- **eget** - User already configured (.eget.toml in dotfiles)
- **Package managers** - Standard Debian repos where possible

## Implementation Notes

### Tool Overlap Resolution
- Some tools available via multiple methods (ripgrep: apt vs cargo)
- Prefer package manager for stability on hypervisor
- Use cargo/eget for tools not in Debian repos

### Configuration Consistency
- Maintain similar tool selection across hypervisor nodes
- Document rationale for hypervisor-specific choices
- Prepare expansion path for full toolkit when needed