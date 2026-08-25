# Tech Stack

## Backend
- Language: Python
- Framework: FastAPI
- Agent/RAG framework: LangChain

## Frontend
- Language: JavaScript/TypeScript: TBD
- Framework: React
- Version: TBD

## LLM
- Provider: Groq
- Model: Qwen, 27B model as specified for this project
- Exact API model identifier: TBD

## Retrieval
- RAG architecture: Yes
- Vector database: ChromaDB
- Embeddings model: TBD

## Database
- Supabase
- Intended usage:
  - Conversation history
  - Session data
  - User IDs
  - User roles
  - Access-control-related data

## Testing
- Test framework: TBD
- Test file location: TBD
- Test naming convention: TBD
- Test command: TBD

## Linting and Formatting
- Linter: TBD
- Formatter: TBD
- Lint command: TBD
- Format command: TBD

## Package Management
- Python package manager: TBD
- Frontend package manager: TBD

## Commands

### Backend
- Development command: TBD
- Build command: TBD
- Run command: TBD

### Frontend
- Development command: TBD
- Build command: TBD
- Run command: TBD

### Testing
- Test command: TBD

### Code Quality
- Lint command: TBD
- Format command: TBD

## Environment Variables

All secrets, credentials, API keys, and service configuration must be stored in `.env` files and must never be hardcoded.

Expected values include:
- Groq API key
- Supabase URL
- Supabase credentials/keys
- Any other future service credentials

Do not commit `.env` files to version control.