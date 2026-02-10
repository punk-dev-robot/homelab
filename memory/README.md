# Homelab Memory System

Local knowledge base for homelab infrastructure documentation.

## Directory Structure

```
memory/
├── architecture/     # System design, network topology, service architecture
├── archive/          # Historical context, completed sessions, resolved issues
├── decisions/        # ADRs, critical findings, infrastructure rules
├── guides/           # Step-by-step procedures, troubleshooting, setup guides
├── network-info/     # Network-specific architecture and implementation plans
├── patterns/         # Reusable implementation patterns and quick references
└── research/         # Investigations, evaluations, and future planning
```

## Directories

### architecture/
System-level design documentation: network topology, service architecture overview, container service relationships. Documents that describe *how the infrastructure is structured* rather than how to operate it.

### archive/
Historical context from completed work sessions, resolved issues, and past investigations. Session progress files, completion reports, and deployment issue records live here. Useful for understanding past decisions and troubleshooting recurring problems.

### decisions/
Architectural Decision Records (ADRs), critical findings, infrastructure rules, and philosophy documents. These capture *why* things are the way they are -- root cause analyses, implementation decisions with lasting impact, and operational rules.

### guides/
Step-by-step operational procedures: troubleshooting workflows, setup guides, restore instructions, and integration plans. Anything someone would follow as a runbook.

### network-info/
Network-specific architecture details and implementation plans. VLAN configurations, cross-network discovery strategies, and network integration documentation.

### patterns/
Reusable implementation patterns and quick reference material: container standardization templates, Ansible command cheatsheets, and common service configuration patterns.

### research/
Investigations into future capabilities, technology evaluations, and planning documents for work not yet started. SSO research, new service evaluations, and architecture proposals.

## Naming Conventions

New files use **kebab-case** naming (e.g., `vps-recovery-complete-june-2025.md`). Older files may still use Title Case from the Basic Memory MCP migration (June 2025). Both conventions coexist; new files should always use kebab-case.

## Migration History

This knowledge base was migrated from Basic Memory MCP to local Markdown files in June 2025. The migration moved to direct file access for better performance, full git integration, and offline availability.

## Known Issues

CLAUDE.md contains `memory://` URLs from the Basic Memory MCP system that no longer resolve. These are flagged for cleanup in a future phase.
