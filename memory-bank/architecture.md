# Architecture

## System Overview

The project is a secure RAG-based conversational system for employees.

It uses:
- React for the frontend
- FastAPI for the backend
- LangChain for RAG and agent-related logic
- Groq with the specified Qwen 27B model for LLM responses
- ChromaDB for document retrieval
- Supabase for storing conversation and session-related data

The system must safely handle follow-up questions in a shared session. A user must not receive information retrieved for another user if that information is outside their access permissions.

## Intended Folder Structure

```text
project-root/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── schemas/
│   │   ├── services/
│   │   │   ├── rag/
│   │   │   ├── access_control/  (item 2 — implemented: models, directory)
│   │   │   ├── session/         (item 3 — implemented: store, visibility)
│   │   │   ├── conversation/     (future)
│   │   │   └── llm/
│   │   ├── models/               (future)
│   │   ├── database/             (future — Supabase)
│   │   ├── vectorstore/
│   │   ├── utils/                (future)
│   │   └── config/
│   └── tests/
│
├── frontend/                     (future)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   └── package.json
│
├── documents/
│   ├── generate_test_documents.py
│   └── generated_test_documents/
│
├── .clinerules/
│
# NOTE (ADR-0003): requirements.txt and pyproject.toml live at the REPO ROOT,
# not under backend/, because CI commands run from the workspace root.
├── requirements.txt
├── pyproject.toml
├── .env.example
├── tech-stack.md
├── architecture.md
├── projectBrief.md
├── AGENTS.md
└── ROADMAP.md
```