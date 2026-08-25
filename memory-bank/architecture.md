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
│   │   │   ├── access_control/
│   │   │   ├── conversation/
│   │   │   └── llm/
│   │   ├── models/
│   │   ├── database/
│   │   ├── vectorstore/
│   │   ├── utils/
│   │   └── config/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   └── package.json
│
├── documents/
│   └── generated_test_documents/
│
├── .clinerules/
│
├── .env.example
├── tech-stack.md
├── architecture.md
├── projectBrief.md
├── AGENTS.md
└── ROADMAP.md