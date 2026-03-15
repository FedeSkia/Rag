# RAG App — LangChain + Ollama + pgvector

A Retrieval-Augmented Generation (RAG) application built with LangChain/LangGraph, Ollama (local LLMs), and pgvector for vector storage. It exposes a FastAPI service that lets authenticated users upload PDF documents, ask questions against them via a conversational agent, and manage chat history — all running locally via Docker Compose.

## Architecture

```
┌──────────────┐       ┌──────────────┐       ┌──────────────────┐
│   Frontend   │──────▶│  FastAPI App  │──────▶│  Ollama (LLM)    │
│  (port 3000) │       │  (port 8000)  │       │  (port 11434)    │
└──────────────┘       └──────┬───────┘       └──────────────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼                         ▼
        ┌────────────────┐       ┌──────────────────┐
        │  PostgreSQL +  │       │  Supabase Auth   │
        │  pgvector      │       │  (GoTrue)        │
        │  (port 5433)   │       │  (port 9999)     │
        └────────────────┘       └──────────────────┘
                                          │
                                 ┌────────┴────────┐
                                 │  Supabase DB     │
                                 │  (port 5435)     │
                                 └─────────────────┘
```

## Services

| Service | Image | Port | Purpose |
|---|---|---|---|
| `rag-app` | Custom (Dockerfile) | 8000 | FastAPI application |
| `ollama` | Custom (ollama/ollama) | 11434 | Local LLM inference (qwen3:0.6b + nomic-embed-text) |
| `postgres` | pgvector/pgvector:0.8.0-pg17 | 5433 | Vector store + LangGraph checkpointer |
| `supabase-db` | supabase/postgres:15.8.1.060 | 5435 | Supabase auth backend DB |
| `supabase-auth` | supabase/gotrue:v2.177.0 | 9999 | JWT-based user authentication |

## Tech Stack

- **Python 3.11** / Poetry
- **LangChain + LangGraph** — agent orchestration, tool-calling RAG graph
- **Ollama** — local LLM serving (chat: `qwen3:0.6b`, embeddings: `nomic-embed-text`)
- **pgvector** — vector similarity search on PostgreSQL
- **FastAPI + Uvicorn** — REST API
- **Supabase GoTrue** — JWT authentication (signup, login)
- **Unstructured** — PDF parsing with OCR support (Tesseract, Ghostscript, Camelot)
- **CrossEncoder (ms-marco-MiniLM-L-6-v2)** — re-ranking retrieved documents

## Project Structure

```
src/rag_app/
├── main.py                    # Entrypoint
├── config.py                  # Env-based configuration (AppConfig dataclass)
├── logging_setup.py           # JSON structured logging + request context
├── llm_singleton.py           # ChatOllama factory
├── db.py                      # Vector store helpers
├── db_memory.py               # LangGraph checkpointer & store (PostgresSaver/PostgresStore)
├── agent/
│   ├── graph.py               # LangGraph RAG agent (query → retrieve → generate)
│   ├── agent_state.py         # Graph state definition
│   └── graph_configuration.py # Thread/user config for graph runs
├── ingestion/
│   ├── pdf_store.py           # PDF upload → parse → chunk → embed → pgvector
│   ├── coalesce.py            # Element coalescing (merge short fragments)
│   └── constants.py           # Metadata key constants
├── retrieval/
│   └── pdf_retriever.py       # Similarity search + cross-encoder re-ranking
├── document/
│   └── user_document_handler.py  # List/delete user documents (raw SQL)
└── web_api/
    ├── endpoints.py           # FastAPI app setup, routers
    ├── chat_history_web.py    # Chat invoke (SSE streaming), history, thread management
    ├── documents.py           # PDF upload/list/delete endpoints
    ├── admin.py               # Admin user create/delete via GoTrue
    └── jwt_resolver.py        # JWT bearer token validation
```

## API Endpoints

All endpoints are prefixed with `/api`.

### Chat (`/api/chat`) — requires JWT

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat/invoke` | Send a message; returns SSE stream. Pass `X-Thread-Id` header for conversation continuity |
| `GET` | `/chat/get_user_conversation_history` | List all conversation threads for the user |
| `GET` | `/chat/get_user_conversation_thread` | Get messages for a specific thread (`X-Thread-Id` header) |
| `DELETE` | `/chat/{thread_id}` | Delete a conversation thread |

### Documents (`/api/document`) — requires JWT

| Method | Path | Description |
|---|---|---|
| `POST` | `/document/upload` | Upload a PDF (multipart form, `application/pdf` only) |
| `GET` | `/document/retrieve_documents` | List uploaded documents for the user |
| `DELETE` | `/document/{document_id}` | Delete a document and all its chunks |

### Admin (`/api/admin`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/admin/create_user` | Create a user via GoTrue signup |
| `DELETE` | `/admin/delete_user` | Delete a user via GoTrue admin API |

## RAG Pipeline

1. **Ingestion** — PDF uploaded → parsed by Unstructured (with OCR) → elements coalesced → chunked with `RecursiveCharacterTextSplitter` (1100 chars, 200 overlap) → embedded via `nomic-embed-text` → stored in pgvector with user/document metadata
2. **Retrieval** — User query → vector similarity search (k=20, filtered by user_id) → cross-encoder re-ranking (top 6) → context passed to LLM
3. **Generation** — LangGraph agent decides whether to call the `retrieve_documents` tool or respond directly → streams response via SSE

## Getting Started

### Prerequisites

- Docker & Docker Compose
- ~4 GB disk space for Ollama models

### Quick Start

```bash
cd docker/rag_app

# Build and start all services
docker compose build --no-cache
docker compose up
```

The Ollama entrypoint automatically pulls `qwen3:0.6b` and `nomic-embed-text` on first start.

### Local Development

```bash
# Start infrastructure (Ollama, Postgres, Supabase) via Docker
cd docker/rag_app
docker compose up ollama postgres supabase-db supabase-auth

# Run the app locally with Poetry
cd ../..
poetry install
poetry run env APP_ENV=.env.local app
```

### Environment Configuration

Copy `.env.example` to `.env.local` and configure:

| Variable | Description | Default |
|---|---|---|
| `DB_HOST` | PostgreSQL host | `postgres-rag-app` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` / `DB_PWD` | DB credentials | `langgraph` |
| `CHAT_MODEL` | Ollama chat model | `qwen3:0.6b` |
| `EMBEDDING_MODEL` | Ollama embedding model | `nomic-embed-text` |
| `LLM_HOST` | Ollama base URL | `http://ollama-rag-app:11434` |
| `CHUNK_SIZE` | Text chunk size | `1100` |
| `CHUNK_OVERLAP` | Chunk overlap | `200` |
| `RERANKER_MODEL_NAME` | Cross-encoder model | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `RERANKER_TOP_N_RETRIEVED_DOCS` | Docs after re-ranking | `6` |
| `JWT_SECRET` | Shared JWT secret (must match GoTrue) | — |
| `JWT_ALG` | JWT algorithm | `HS256` |
| `GOTRUE_URL` | GoTrue auth service URL | `http://supabase-auth:9999` |

## Authentication Flow

1. Create a user via `POST /api/admin/create_user` (email + password)
2. Obtain a JWT from Supabase GoTrue (`POST http://localhost:9999/token?grant_type=password`)
3. Pass the JWT as `Authorization: Bearer <token>` on all `/api/chat` and `/api/document` endpoints

## AWS Deployment (ECS + ECR)

The project includes three shell scripts to build, push, and deploy Docker images to AWS ECR and trigger ECS redeployments. All scripts live in the project root and share the same ECR repository (`rag-app`) with different image tags.

### Prerequisites

- AWS CLI configured with credentials that have ECR and ECS permissions
- Docker running locally
- An existing ECS cluster and service already provisioned

### Deployment Scripts

| Script | Image Built | ECR Tag | ECS Service Updated |
|---|---|---|---|
| `push-rag-image.sh` | FastAPI RAG app (`docker/rag_app/Dockerfile`) | `rag-langchain-app-latest` | `rag-app-task` |
| `push-ollama-image.sh` | Ollama LLM server (`docker/ollama/Dockerfile`) | `rag-langchain-ollama-latest` | `rag-app-task` |
| `push-vllm-image.sh` | vLLM server (`docker/VLLM/Dockerfile`) | `rag-langchain-vllm-latest` | `rag-app-task` |

Each script performs the same workflow:
1. Build the Docker image for `linux/amd64`
2. Authenticate to AWS ECR via `aws ecr get-login-password`
3. Delete the existing image tag in ECR (if present)
4. Tag and push the new image to ECR
5. Force a new deployment on the ECS service

### Environment Variables

All scripts accept overrides via environment variables:

| Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | `eu-west-1` | AWS region for ECR and ECS |
| `AWS_ACCOUNT_ID` | *(required)* | Your AWS account ID |
| `ECR_REPOSITORY` | `rag-app` | ECR repository name (shared across all images) |
| `CLUSTER_NAME` | `my-rag-app-cluster` | ECS cluster name |
| `SERVICE_NAME` | `rag-app-task` | ECS service name to redeploy |

### Usage

```bash
# Deploy the RAG app
AWS_ACCOUNT_ID=<your-account-id> ./push-rag-image.sh

# Deploy Ollama
AWS_ACCOUNT_ID=<your-account-id> ./push-ollama-image.sh

# Deploy vLLM (alternative to Ollama, GPU-based)
AWS_ACCOUNT_ID=<your-account-id> ./push-vllm-image.sh
```

### vLLM vs Ollama

The project supports two LLM backends:
- **Ollama** — lightweight, CPU-friendly, auto-pulls models on startup (`qwen3:0.6b`, `nomic-embed-text`)
- **vLLM** — GPU-optimized OpenAI-compatible server, uses `Qwen/Qwen2.5-3B-Instruct` by default, requires a HuggingFace token at build time (`--secret id=hf_token`)

## Testing

```bash
poetry run pytest -v
```

Tests cover configuration parsing, document coalescing logic, PDF store helpers, graph configuration, JWT validation, admin JWT minting, retriever data models, and Pydantic model validation. No running infrastructure required.

## License

Private project.
