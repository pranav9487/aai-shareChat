---
name: new-feature
description: Guides the agent on requirements alignment, development, testing, and documentation for new features.
---

# New Feature Development Skill

## When to use this skill
- Use this when tasked with designing, implementing, and integrating a new feature end-to-end.

## New Feature Guidelines

### 1. Requirements Alignment
- Confirm you fully understand the requirements.
- Restate the acceptance criteria in your response (expected inputs/outputs, edge cases, what "done" looks like) before writing code.
- If requirements are vague, ask the user for clarification first.

### 2. Architecture & Tech Stack Check
- Read `memory-bank/architecture.md`, `memory-bank/systemPatterns.md`, and `memory-bank/tech-stack.md` to follow current naming, layering, and DI patterns.
- Check `ROADMAP.md` to align the feature scope with what is planned.

### 3. Development Workflow
- Create a new feature branch (`git checkout -b feature/short-name`).
- Implement the feature using minimal, clean, targeted changes.
- Avoid modifying files or refactoring code unrelated to the feature.

### 4. Testing & Code Quality
- Check if tests exist for the changed areas. Write robust unit and integration tests covering happy paths, boundaries, invalid inputs, and adversarial conditions.
- Run the full test suite to guarantee zero regressions.
- Run formatters and linters (`ruff`, `black`, `eslint`) and resolve all warnings.
- Perform a self-review of the diff before committing.

### 5. Documentation Updates
- Commit changes using Conventional Commits.
- Update `memory-bank/progress.md` and `memory-bank/activeContext.md`.
- Update `ROADMAP.md` to transition the task status.
- Summarize changes in plain English for the user and request review (do not push or merge without approval).
