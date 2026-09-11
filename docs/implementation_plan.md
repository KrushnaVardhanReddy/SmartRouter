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

### Phase 1: Core Setup & Contract Definition
1. Initialize a Python `uv` or `poetry` project (or just `requirements.txt`).
2. Create the Pydantic data models for the OpenAI `ChatCompletionRequest` and `ChatCompletionResponse`.
3. Set up the FastAPI server in `main.py` serving these endpoints.

### Phase 2: Passthrough Router (No ML yet)
1. Implement the async `httpx` clients for Groq and OpenAI.
2. Build a simple passthrough that blindly forwards the incoming payload to Groq and returns the response.
3. Validate that a standard OpenAI SDK client can connect to `http://localhost:8080/v1` and get a response.

### Phase 3: Classifier Integration
1. Adapt the `train_classifier.py` script from the `Local_AI_Assistant` project to generate a `complexity_classifier.pkl`.
2. Implement the `classifier/engine.py` to load the embeddings model and the `.pkl` file.
3. Hook the classifier into the request lifecycle to generate a `0.0 - 1.0` score before routing.

### Phase 4: Dynamic Routing Logic
1. Implement threshold logic (`ROUTER_LOW_THRESHOLD`, `ROUTER_HIGH_THRESHOLD`).
2. Route low-score requests to Groq (Llama-3), mid-score to OpenAI (GPT-4o-mini), and high-score to Anthropic/OpenAI (Claude 3.5 / GPT-4o).

### Phase 5: Distribution (PyInstaller & Docker)
1. Create a multi-stage `Dockerfile`.
2. Write a `build.sh` script using **PyInstaller** to compile the entire Python app (including the FastAPI server and ML models) into a single executable binary.

---

> [!IMPORTANT]  
> **PyInstaller Limitations with ML:** PyInstaller works great for FastAPI, but packaging heavy ML libraries (like `torch` and `sentence-transformers`) can result in a massive binary (1GB+). Are you okay with a large file size for the single-binary executable, or should we prioritize the Docker container as the primary distribution method?

## Verification Plan
- We will test the router using standard OpenAI Python/Node SDK clients configured with `base_url="http://localhost:8080/v1"`.
- We will assert that trivial prompts (e.g., "Say hi") route to Groq and return in < 500ms.
- We will assert that complex prompts (e.g., "Write a compiler in Rust") route to the smart model.
