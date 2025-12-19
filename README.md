# Synapse

**Synapse** is a security-focused, production-oriented backend system designed to demonstrate **correctness, data integrity, and least-privilege architecture** in a modern async environment.

While the current implementation includes a Retrieval-Augmented Generation (RAG) workflow, AI is intentionally treated as a **replaceable workload** rather than the core product. The primary goal of this project is to showcase how a backend should be structured when security boundaries, transactional integrity, and failure modes actually matter.

---

## What This Project Is (and Isn’t)

**Synapse is:**
- A realistic backend foundation built with production constraints in mind
- A demonstration of secure secret handling and explicit trust boundaries
- A system where AI features sit *on top* of a hardened core

**Synapse is not:**
- A demo-only AI application
- A frontend-driven product
- A collection of loosely coupled features

---

## Core Design Principles

### Security by Default
Secrets are never hard-coded and are not stored long-term in environment files.

- HashiCorp Vault is used for **runtime secret access**
- AppRole authentication with explicit, minimal policies
- KV v2 for versioned secrets
- Transit engine for asymmetric JWT signing
- Secrets are fetched only when needed and cached in memory for limited lifetimes

---

### Strong Data Integrity
The system is designed to prevent partial or inconsistent state, especially across async and AI-driven workflows.

- ACID-compliant PostgreSQL transactions
- Explicit commit boundaries
- Clear separation between read-only and mutating operations
- Fail-fast behavior when invariants are violated

---

### Explicit System Boundaries
Each subsystem is treated as an **independent concern** with clear ownership of state.

- PostgreSQL is the authoritative source of truth
- Qdrant is treated as a **derived vector index**, not a primary database
- Real database identifiers are **never sent to the vector database**
- An abstraction layer maps internal UUIDs to vector-safe identifiers

This prevents identifier leakage and keeps vector storage replaceable without impacting core data models.

---

## Architecture Overview

- **API**: Async FastAPI
- **Database**: PostgreSQL (async SQLAlchemy)
- **Migrations**: Alembic (intentionally excluded from version control)
- **Secrets Management**: HashiCorp Vault (KV v2, AppRole, Transit)
- **Vector Store**: Qdrant (isolated identifier layer)
- **LLM Integration**: Google Gemini
- **Runtime**: Docker-based local development

---

## Current Capabilities

- Secure authentication using HTTP-only JWT cookies
- Password hashing with Argon2id
- Vault-managed runtime secrets with least exposure
- Document ingestion and preprocessing pipeline
- Chunking and vector indexing for retrieval workflows
- Clean API error responses with no internal state leakage
- LLM interaction built on top of a stable backend core

---

## RAG as a Replaceable Layer

Retrieval and LLM components are intentionally **non-core modules**.

- The backend remains useful without AI features
- Vector storage can be swapped or removed entirely
- LLM providers are not coupled to business logic
- Failures in AI workflows do not corrupt primary state

This reflects how AI is typically integrated in real systems: as a capability, not a dependency.

---

## Running the Project (High Level)

1. Configure HashiCorp Vault (KV v2 + AppRole)
2. Start dependencies using Docker Compose
3. Run the FastAPI service

Detailed production deployment and scaling concerns are intentionally out of scope for this repository.

---

## Project Status

This repository represents a **complete and stable backend slice** intended to showcase:

- backend engineering depth
- security-first design
- transactional correctness
- clear system boundaries

Additional features will be added incrementally without changing the core architecture.

---

## License

This project is provided for educational and portfolio purposes.
