---
phase: 03-content-cleanup
plan: 01
subsystem: infra
tags: [git, cleanup, gitignore, file-organization]

requires:
  - phase: 02-pii-discussion
    provides: PII remediation complete, content now safe for relocation
provides:
  - Clean repository root with no stale files
  - Proper memory/ and guides/ file organization with kebab-case naming
  - Minimal .gitignore with only relevant entries
  - Neutral HOMELAB_SERVICES.md title
affects: [05-documentation]

tech-stack:
  added: []
  patterns: [kebab-case filenames in memory/ and guides/]

key-files:
  created:
    - guides/karakeep-sso-setup.md
    - memory/archive/authentik-implementation-state.md
    - memory/archive/crowdsec-deployment-fix-session.md
    - memory/archive/tunnel-infrastructure-automation-resolution.md
    - memory/research/linux-bonding-mac-address-management.md
    - memory/research/va-api-vs-qsv-performance-comparison.md
  modified:
    - .gitignore
    - HOMELAB_SERVICES.md

key-decisions:
  - "Kebab-case for all relocated filenames to match existing memory/ conventions"

patterns-established:
  - "Kebab-case naming: all files in memory/ and guides/ use lowercase-kebab-case"

duration: 3min
completed: 2026-02-10
---

# Phase 3 Plan 1: Content Cleanup Summary

**Relocated 6 stale root-level files to memory/archive/, memory/research/, and guides/ with kebab-case naming; cleaned .gitignore of 5 phantom entries; neutralized HOMELAB_SERVICES.md title**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-10T00:58:32Z
- **Completed:** 2026-02-10T01:01:26Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Relocated AUTHENTIK_IMPLEMENTATION_STATE.md, KARAKEEP_SSO_SETUP.md, and 4 files from archive/ and research/ to their proper memory/ or guides/ locations
- Removed stale .gitignore entries for 5 nonexistent directories (infra, qnap, media, obs, apps)
- Changed HOMELAB_SERVICES.md title from "Kuba's Homelab Infrastructure" to "Homelab Infrastructure"
- All 6 CONT requirements verified passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Relocate stale root-level files and directories** - `541f083` (feat)
2. **Task 2: Update .gitignore and polish HOMELAB_SERVICES.md** - `36f6c6c` (chore)

**Plan metadata:** `4ad7593` (docs: complete plan)

## Files Created/Modified
- `memory/archive/authentik-implementation-state.md` - Authentik implementation state (relocated from root)
- `memory/archive/crowdsec-deployment-fix-session.md` - CrowdSec session notes (relocated from archive/)
- `memory/archive/tunnel-infrastructure-automation-resolution.md` - Tunnel automation notes (relocated from archive/)
- `memory/research/linux-bonding-mac-address-management.md` - Linux bonding research (relocated from research/)
- `memory/research/va-api-vs-qsv-performance-comparison.md` - VA-API vs QSV comparison (relocated from research/)
- `guides/karakeep-sso-setup.md` - Karakeep SSO setup guide (relocated from root)
- `.gitignore` - Removed 5 stale directory entries
- `HOMELAB_SERVICES.md` - Neutralized title and subtitle

## Decisions Made
- Used kebab-case for all relocated filenames to match existing memory/ naming conventions (e.g., completed-tasks-history.md)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Repository root is clean and publication-ready
- Ready for Phase 4 (Ansible/Docker cleanup) or Phase 5 (Documentation)

## Self-Check: PASSED

- All 8 files verified present on disk
- Commits 541f083 and 36f6c6c verified in git log

---
*Phase: 03-content-cleanup*
*Completed: 2026-02-10*
