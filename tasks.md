# SmartRouter Task Tracker

This document tracks the execution phases of the SmartRouter project, aligned with our v0.1 to v1.0 release roadmap.
Tasks assigned to Jules (Tier 2) are marked with `(Jules)`.

## Phase 1 (v0.1): Core Setup & Passthrough Proxy
*Goal: Prove the OpenAI-compatible API works end-to-end with configurable tiers (no ML).*

- [x] Initialize Python project using `uv`
- [x] Define `contracts/openapi.yaml` (OpenAI proxy schema)
- [x] Define `contracts/config_schema.json` (Configuration schema)
- [x] (Jules) Generate Pydantic models in `smartrouter/api/models.py` (P1-T1)
- [/] (Jules) Implement `base_provider.py` and OpenRouter Client (P1-T2)
- [ ] (Jules) Connect FastAPI routes to passthrough client for E2E (P1-T3)
- [ ] (Jules) Set up E2E Pytest suite (P1-T4)

## Phase 2 (v0.2): The Smart Router (Classifier & Context)
*Goal: Add the complexity classifier, context guarding, and streaming.*

- [x] (Jules) Implement type-safe YAML config loader (P2-T1)
- [x] (Jules) Set up `train_classifier.py` and ML dependencies (P2-T2)
- [x] (Jules) Create `classifier/engine.py` to embed and score prompts (P2-T2)
- [/] (Jules) Implement Context Window Guard utility in `router/context_guard.py` (P2-T3)
- [ ] (Jules) Implement Dynamic Routing Logic in `router/dispatcher.py` (P2-T4)
- [ ] Add Streaming Support (`stream: true` SSE proxying)
- [ ] Inject custom response headers (`X-SmartRouter-Model`, `X-SmartRouter-Score`)
- [ ] Add `GET /v1/usage` (cost savings report endpoint)
- [ ] **E2E Testing:** Verify classifier and dynamic routing end-to-end (no mocking)

## Phase 3 (v0.3): Enterprise Optimization & Resilience
*Goal: Make it stable for production environments and maximize cost savings.*

- [ ] **Shadow Mode (Monitor Only):** Track hypothetical savings without intercepting requests
- [ ] **Context Compression:** Auto-summarize older chat history for lower-tier models
- [ ] Semantic Caching (`faiss`/`hnswlib`) to return cached responses for duplicate prompts
- [ ] Budget Circuit Breaker (hard cost limits and auto-downshifting tiers)
- [ ] Fallback Chain (auto-retry next tier on 429/503 HTTP errors)
- [ ] MCP Server (`/.well-known/mcp/`) for native agent tool integration
- [ ] Create multi-stage `Dockerfile` (optimized for ML dependencies)
- [ ] **E2E Testing:** Verify fallback chains and circuit breakers under load (no mocking)

## Phase 4 (v0.4): Developer Tools
*Goal: Add visibility and debugging tools for developers.*

- [ ] Analytics Web Dashboard (simple UI to view routing decisions and cost savings)
- [ ] `GET /v1/explain` endpoint (returns the chosen model and why)
- [ ] `force_model` override (via custom headers or prompt injection for testing)
- [ ] Persistent System Prompt Injection (append/prepend from config)
- [ ] **E2E Testing:** Verify system prompt injection and dashboard analytics end-to-end

## Phase 5 (v1.0): Open Source Launch & Distribution
*Goal: Frictionless adoption for the community.*

- [ ] `smartrouter` CLI (commands: `start`, `export`, `import`)
- [ ] Profile Bundles (`.srprofile` context portability and sharing)
- [ ] Python Middleware implementation (drop into existing FastAPI apps)
- [ ] Documentation, Quickstart Guide, and PyPI distribution
- [ ] SSO / Auth Gateway integration (API keys mapping to users)
- [ ] **E2E Testing:** Verify CLI and Docker deployments operate successfully in a clean environment
