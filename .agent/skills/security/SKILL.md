---
name: security
description: Enforces user ID identification, role-based access control, and privacy protections in the shared RAG system.
---

# Security & Access Control Skill

## When to use this skill
- Use this when working on RAG pipelines, API endpoints, authentication, user data ingestion, retrieval logic, or database/vector-store interactions.
- Use this to verify security compliance before commits or deployments.

## Security & Privacy Guidelines

### 1. User & Session Isolation (Core Invariant)
- **Identify the current user** by their user ID (`X-User-ID` header or verified session token) and apply role-based access controls (RBAC) on every relevant request.
- **Do not automatically reuse retrieved chunks** for another user's follow-up or query in a shared session. Retrieve and verify fresh content for the specific user asking the question.
- If requested information or document is not accessible to the current user's role or access level, return a security-based decline response (e.g. `ACCESS_DENIED_ANSWER` or `NOT_FOUND_ANSWER`). **Never expose any source content, filenames, or metadata snippets in the decline.**

### 2. Environment Variables & Secrets
- **NEVER hardcode API keys, passwords, connection strings, or access tokens** in files.
- Always load credentials dynamically from `.env` using standard configuration managers (e.g., pydantic-settings).
- Ensure credentials and local environment files (`.env`, `.env.local`, etc.) are git-ignored.
- Scan diffs before committing to catch any accidental secret leakage.

### 3. Input Validation & Dependency Checks
- Validate and sanitize all external/user input on any path that touches a database query, shell command, or file path.
- Enforce permissions filtering inside vector-store queries (e.g., matching user access tier directly in ChromaDB `where` metadata filters).
- When introducing a new package, verify its authenticity to prevent typo-squatting risks.
