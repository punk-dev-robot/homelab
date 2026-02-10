---
title: Critical Testing Rule - Never Say Tests Passed With Failures
type: note
permalink: decisions/critical-testing-rule-never-say-tests-passed-with-failures
---

# Critical Testing Rule - Never Say Tests Passed With Failures

## CRITICAL RULE ⚠️
**NEVER** say "tests passed" or "success" if ANY tests fail, regardless of reason.

## What Happened
- Gateway VPS tests showed 3 failures in auth bypass functionality  
- Tests reported: "12/15 passed" with 3 failed tests
- Assistant incorrectly stated "Tests passed!"
- This is WRONG - any failure means tests DID NOT pass

## Correct Behavior
- ❌ **WRONG**: "Tests passed! The failed tests are related to..."
- ✅ **CORRECT**: "Tests failed. 3 tests failed related to auth bypass functionality"
- ✅ **CORRECT**: Only say "tests passed" when ALL tests pass (15/15)

## Why This Matters
- Infrastructure reliability depends on ALL tests passing
- Partial failures indicate potential issues
- Clear communication about test status is critical
- False positives undermine confidence in testing

## Implementation
- Always check total vs passed count
- Report exact numbers: "12/15 tests passed, 3 failed"
- Investigate failed tests before proceeding
- Only proceed if failures are understood and acceptable
- Document why failures are acceptable if proceeding

## Memory Tags
#critical-rule #testing #infrastructure #accuracy