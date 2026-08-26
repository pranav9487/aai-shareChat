---
name: commit
description: Guides the agent on how to review and commit changes in this repository using Conventional Commits.
---

# Commit Workflow Skill

## When to use this skill
- Use this when completing a task, feature, or bug fix, and you are ready to commit changes to Git.
- Use this on demand to commit any code updates.

## Commit Guidelines

### 1. Pre-Commit Verification
- Run `git status` and `git diff` to review all modified files.
- Stage only relevant files with `git add` (never stage blindly).
- Confirm that tests pass. Do not commit code that breaks tests.
- Run the linter (`ruff check .`) and formatter (`black .` for backend, `npm run lint` for frontend) and fix all warnings.
- Perform a self-review of the diff (check for unhandled errors, debug logging, dead code, or hardcoded secrets).

### 2. Commit Message Structure
Write commit messages following the Conventional Commits style:
- Format: `type(scope): short summary` (imperative mood, under 50 chars).
- Common types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `style`.
- Add a brief body (1-3 lines) explaining **WHY** the changes were made.
- Example:
  ```
  fix(auth): handle expired token edge case in refresh flow
  
  Added checks to detect token expiry in cookies before sending request
  and trigger redirect to login page.
  ```

### 3. Merging & Pushing
- Never commit directly to `main` or `master`.
- Work on a branch named `feature/short-name` or `fix/short-name`.
- Do NOT run `git push` or merge branches automatically. Always wait for explicit user confirmation.

### 4. Changelog Update
- Do not hand-edit `CHANGELOG.md`.
- Regenerate it from commit history using the appropriate workspace tool/command if applicable.
