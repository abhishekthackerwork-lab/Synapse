**Synapse** 
is a production-oriented async backend system designed to demonstrate transactional integrity, strict system boundaries, and least-privilege security. AI-features such as RAG and tool-calling are implemented as modular extensions over an ACID-compliant PostgreSQL core.
---

### Demo video available on linkedIn (Link in profile)

---

## Core Architecture

- Async FastAPI with SQLAlchemy 2.0 and explicit transaction boundaries.


- LLM tool execution wrapped in nested SAVEPOINT transactions to prevent partial state corruption.


- PostgreSQL as authoritative source of truth.


- Server-side conversation reconstruction using conversation_id to prevent client tampering.


- Strict row-level user isolation enforced via user_id scoping.

---

### Security Model
Built with the principle of least exposure, leveraging **HashiCorp Vault** for all sensitive operations.


- Vault AppRole-based dynamic database credentials (short-lived leases).

- Asymmetric JWT signing via Vault Transit (private keys never stored in application memory).

- Argon2id password hashing.
---

### AI Integration 
- Deterministic tool-calling with strict Pydantic schema validation to prevent invalid state mutations.
- Tool executions wrapped in retry logic with reasoning-state stripping to ensure clean re-execution.
- Retrieval-Augmented Generation (RAG) pipeline backed by Qdrant, with PostgreSQL as the authoritative source of truth.
- sensitive identifiers are never exposed to the LLM.


---



### Tech Stack

Backend:
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 + Alembic
- HashiCorp Vault
- Qdrant

AI:
- Google Gemini 2.5/3.0
- Google GenAI Python SDK

Frontend:
- React 19
- TypeScript
- Vite 7
- Tailwind CSS 4

Runtime:
- Docker
---
## License
MIT LICENSE