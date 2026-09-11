# SmartRouter Implementation Plan (Python / FastAPI)

This document outlines the technical design, module structure, and execution phases for building the SmartRouter in Python.

## 1. Project Architecture

The application is built using a **Spec-First methodology** and acts as an OpenAI-compatible API proxy.

**Tech Stack:**
- **Web Framework:** FastAPI (ASGI) + Uvicorn
- **HTTP Client:** `httpx` (async, for proxying to Groq/OpenAI)
- **Machine Learning:** `scikit-learn`, `sentence-transformers`
- **Config Management:** `pydantic-settings`
- **Distribution:** Docker & PyInstaller (standalone binary)

## 2. API Contract & Code Generation

Before writing any Python routing logic, we will define the API contract.
We will pull the official OpenAI `openapi.yaml` (focusing on the `/v1/chat/completions` endpoint).
FastAPI naturally enforces this contract via Pydantic models. We will define a `ChatCompletionRequest` Pydantic model that mirrors OpenAI's exact schema, ensuring the router accepts standard SDK requests.

## 3. Module Structure

```text
smartrouter/
├── api/
│   └── routes.py         # FastAPI endpoints (POST /v1/chat/completions)
├── classifier/
│   ├── engine.py         # Loads the .pkl model & sentence-transformers
│   └── text_utils.py     # Prompt extraction from the request payload
├── router/
│   ├── dispatcher.py     # Uses the complexity score to pick a provider
│   └── clients.py        # Async httpx wrappers for Groq, OpenAI, Anthropic
├── core/
│   ├── config.py         # Pydantic settings loading from .env.local
│   └── logging.py        # Structured JSON logging
└── main.py               # App entry point
```

## 4. Implementation Phases

The execution plan has been broken down into nested phases:

- [Phase 1: Core Setup & Contract Definition](phases/phase_1_core_setup/README.md)
- [Phase 2: Passthrough Router (No ML yet)](phases/phase_2_passthrough_router/README.md)
- [Phase 3: Classifier Integration](phases/phase_3_classifier_integration/README.md)
- [Phase 4: Dynamic Routing Logic](phases/phase_4_dynamic_routing/README.md)
- [Phase 5: Distribution (PyInstaller & Docker)](phases/phase_5_distribution/README.md)

---

> [!IMPORTANT]  
> **PyInstaller Limitations with ML:** PyInstaller works great for FastAPI, but packaging heavy ML libraries (like `torch` and `sentence-transformers`) can result in a massive binary (1GB+). Are you okay with a large file size for the single-binary executable, or should we prioritize the Docker container as the primary distribution method?

## Verification Plan
- We will test the router using standard OpenAI Python/Node SDK clients configured with `base_url="http://localhost:8080/v1"`.
- We will assert that trivial prompts (e.g., "Say hi") route to Groq and return in < 500ms.
- We will assert that complex prompts (e.g., "Write a compiler in Rust") route to the smart model.
