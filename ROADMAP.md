# Roadmap

## Now

### 1. Build the RAG Pipeline
- Build the core RAG pipeline.
- Use generated company-style internal documents for testing.
- Store and retrieve documents through ChromaDB.
- Generate responses using LangChain and the specified Groq Qwen 27B model.

### 2. Implement Access Control
- Support user identification through user ID.
- Apply role-based access control.
- Ensure users only receive information they are permitted to access.

### 3. Implement Shared-Session Safety
- Support multiple users in a shared session.
- Track user identity for each relevant request.
- Prevent information retrieved for one user from automatically being exposed to another user.

### 4. Implement Safe Follow-Up Handling
- Detect follow-up questions.
- Rewrite follow-up questions into standalone questions when required.
- Perform retrieval according to the current user's access permissions.
- Return a security-based response when information cannot be answered due to access restrictions.

## Next

To be decided later.

No priorities should be assumed until they are explicitly defined.

## Later / Ideas

No later features have been defined yet.

## Explicitly Not Planned

- Voice input
- File uploads
- Multi-agent algorithms
- Admin dashboard
- Mobile application
- Production deployment