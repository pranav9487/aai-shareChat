---
name: debug
description: Guides the agent on reproducing, isolating, fixing, and verifying bugs.
---

# Debug Workflow Skill

## When to use this skill
- Use this when diagnosing, troubleshooting, or fixing a bug or failing behavior in the system.

## Debugging Guidelines

### 1. Reproduce First
- Before changing any code, reproduce the failure locally. Run tests or run the application and ensure you can observe the issue.

### 2. Isolate and Trace
- Do not guess-patch or write quick fixes for symptoms.
- Trace the root cause through error tracebacks, console/application logs, database states, or step-through debugging.
- Identify exactly why the failure happens.
- **Before implementing the fix, explicitly state the root cause in one or two sentences in the chat.**

### 3. Implement Targeted Fix
- Keep edits highly scoped.
- Fix only the root cause; do not bundle unrelated refactoring, styling changes, or feature updates with a bug fix.

### 4. Write Regression Test
- Write a regression test covering the edge case or condition that triggered the bug so that future changes cannot reintroduce it.
- Follow testing conventions in `tech-stack.md` (e.g., pytest for backend, vitest for frontend).

### 5. Verification & Commit
- Run the full test suite (not just the new test) to make sure there are no regressions.
- Format and lint code.
- Commit the fix following Conventional Commits format (`fix: ...`) and document the fix in `memory-bank/progress.md`.
