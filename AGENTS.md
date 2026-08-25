# AGENTS.md

Secure RAG system for employees with safe follow-up handling in shared sessions.
The project prevents unauthorized information leakage by applying user ID and role-based access control.

Tech: Python, FastAPI, React, LangChain, Groq Qwen 27B, ChromaDB, Supabase.

Setup: TBD
Run backend: TBD
Run frontend: TBD
Test: TBD
Lint: TBD

- Identify the current user by user ID and apply role-based access on every relevant request.
- Do not automatically reuse retrieved chunks for another user's follow-up in a shared session.
- Return a security-based decline when requested information is not accessible.
- Never hardcode API keys or credentials; use `.env`.

See `.clinerules/` for detailed project rules.