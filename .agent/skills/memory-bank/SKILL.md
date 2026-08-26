---
name: memory-bank
description: Guides the agent on how to read, maintain, and update the repository's Memory Bank.
---

# Memory Bank Workflow Skill

## When to use this skill
- **At the start of every session**: Read the entire memory bank to build full context and understand current state.
- **During development**: Check `tech-stack.md` and `systemPatterns.md` to ensure your implementations follow project guidelines.
- **At the end of a session**: Update the memory bank files to keep them in sync with changes made and leave a clear handoff for the next session.

## Memory Bank Structure and Role of Files

### 1. `projectBrief.md`
- **Purpose**: High-level definition of the project, target users, v1 success criteria, security requirements, scope, and out-of-scope items.
- **Usage**: Reference this to align on the core security posture and core goals of the system.

### 2. `activeContext.md`
- **Purpose**: Represents the current focus of the active branch, recent design and architecture decisions, current blockers/open questions, and the single immediate next step.
- **Usage**: Must be updated at the end of every session. Keep it highly focused on the immediate state of the repository.

### 3. `systemPatterns.md`
- **Purpose**: Architectural patterns, file naming conventions, code layout, dependency injection styles, security postures (e.g., RBAC inside query filters), and things to avoid.
- **Usage**: Read this before writing any new code. If you introduce a new pattern or construct, document it here.

### 4. `tech-stack.md`
- **Purpose**: Lists languages, libraries, tool setups (FastAPI, React, Groq, ChromaDB, Supabase), and exact dev, run, test, lint, and format commands.
- **Usage**: Consult this to verify execution environments and tooling constraints before running tests or checking code quality.

### 5. `progress.md`
- **Purpose**: Running log of work status (completed features/fixes under "Done" and active tasks under "In progress").
- **Usage**: Append new progress details (newest on top) with dates, branch names, and status updates. Never rewrite history.

## Memory Bank Update Conventions
- **Accuracy**: Ensure the memory bank always matches the actual state of the codebase. Do not let documentation drift.
- **Commit Gate**: Document updates to memory bank files alongside code changes in the same commit workflow. Do not leave documentation updates uncommitted.
