---
name: handoff
description: Guides the agent on updating project documentation and memory banks at the end of a session.
---

# Session Handoff Skill

## When to use this skill
- Use this at the end of a work session, or after completing 1-2 features/fixes, to leave the project in a clean, documented, and resumable state.

## Handoff Guidelines

### 1. Update the Memory Bank
Review and update all memory bank files inside the `memory-bank/` directory:
- **`progress.md`**: Move completed tasks from "In progress" to "Done" with a brief note and date.
- **`activeContext.md`**: Record the current focus, decisions made during the session, any blockers/open questions, and the single next step for the next session.
- **`systemPatterns.md`**: Document any new patterns, architectural patterns, schemas, or coding conventions established during the session.

### 2. Update Roadmap and Changelog
- **`ROADMAP.md`**: Move any completed features/tasks out of "Now" or "Next" and adjust project priorities if needed.
- **`CHANGELOG.md`**: Regenerate/update the changelog based on the commit history (do not hand-write changelog entries).

### 3. Commit Documentation Updates
- Run the commit workflow to ensure memory-bank updates, `ROADMAP.md`, and `CHANGELOG.md` are committed to git. Do not leave documentation uncommitted alongside code.
- Do NOT push to remote repositories or delete branches without explicit user confirmation.
- Suggest to the user to start a fresh chat session to clear the context window before picking up the next task.
