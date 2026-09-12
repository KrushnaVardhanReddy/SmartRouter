# SmartRouter Task Tracker

This document tracks the execution phases of the SmartRouter project, aligned with our v0.1 to v1.0 release roadmap.
Tasks assigned to Jules (Tier 2) are marked with `(Jules)`.

## Phase 1 (v0.1): Core Setup & Passthrough Proxy
*Goal: Prove the OpenAI-compatible API works end-to-end with configurable tiers (no ML).*

- [x] Initialize Python project using `uv`
- [x] Define `contracts/openapi.yaml` (OpenAI proxy schema)
- [x] Define `contracts/config_schema.json` (Configuration schema)
- [x] (Jules) Generate Pydantic models in `smartrouter/api/models.py` (P1-T1)
- [x] (Jules) Define `base_provider.py` and implement `OpenRouterClient` (P1-T2)
- [x] (Jules) Implement FastAPI entrypoint with OpenRouter E2E passthrough (P1-T3)
- [x] (Jules) Set up E2E Pytest suite (P1-T4)

## Phase 2 (v0.2): The Smart Router (Classifier & Context)
*Goal: Add the complexity classifier, context guarding, and streaming.*

- [x] (Jules) Implement type-safe YAML config loader (P2-T1)
- [x] (Jules) Set up `train_classifier.py` and ML dependencies (P2-T2)
- [x] (Jules) Create `classifier/engine.py` to embed and score prompts (P2-T2)
- [x] (Jules) Implement Context Window Guard utility in `router/context_guard.py` (P2-T3)
- [x] (Jules) Implement Dynamic Routing Logic in `router/dispatcher.py` (P2-T4)
- [ ] Add Streaming Support (`stream: true` SSE proxying)
- [x] Inject custom response headers (`X-SmartRouter-Model`, `X-SmartRouter-Score`)
- [x] Add `GET /v1/usage` (cost savings report endpoint)
- [x] **Golden Dataset Eval:** Script (`eval_classifier.py`) to measure precision, recall, and false positive rates
- [x] **Seed Training Data:** Script (`seed_training_data.py`) to fetch HuggingFace Chatbot Arena preference data for initial training
- [ ] (Jules) **LLM-as-a-Judge Labeling:** Rewrite seed data script to use `gpt-4o-mini` to score prompt complexity for perfectly clean training labels (P2-T10)
- [ ] (Jules) **Async Pipeline Refactor:** Convert seed script to use asyncio/Semaphore and generate 10,000 JSONL rows (P2-T11)
- [x] **E2E Testing:** Verify classifier and dynamic routing end-to-end (no mocking)

## Phase 3 (v0.3): Enterprise Optimization & Resilience
*Goal: Make it stable for production environments and maximize cost savings.*

- [x] **Shadow Mode (Monitor Only):** Track hypothetical savings without intercepting requests
- [x] **Context Compression:** Auto-summarize older chat history for lower-tier models
- [x] **Rolling Window Summarization:** Upgrade naive message trimming to call a cheap LLM to summarize dropped messages and inject a `[Context Summary]` message, preserving conversation awareness
- [x] **PII Redaction:** Use `presidio-analyzer` & `presidio-anonymizer` to mask sensitive data
- [x] **Jailbreak/Prompt Injection Blocking:** Reject malicious prompts before routing
- [x] **JSON Mode Enforcement:** Guarantee JSON capability when `response_format` is requested
- [x] Semantic Caching (`faiss`/`hnswlib`) to return cached responses for duplicate prompts
- [x] Budget Circuit Breaker (hard cost limits and auto-downshifting tiers)
- [x] **Context-Aware Capacity Routing:** Use token count as a primary routing signal alongside complexity score — probe each tier's token limit locally before dispatching, and cascade through tiers until one can handle the request
- [ ] **Summary-Based Complexity Scoring:** Update the ML dispatcher to embed `[Chat Summary] + [Final Prompt]` rather than just the final prompt, giving the ML classifier true context-awareness (P3-T14)
- [ ] (Jules) **Dispatcher Architecture Refactor:** Modularize `dispatcher.py` and fix the streaming usage tracking bug and hardcoded cost maps (P3-T15)
- [ ] **`routing_preference` Flag (Force Frontier / Economy):** Per-request field (`frontier_only` | `economy` | `auto`) to pin routing to a specific tier class, bypassing the ML classifier entirely
- [x] **API Key Load Balancing:** Round-robin across multiple API keys for the same provider
- [x] **Advanced Retries:** Exponential backoff for transient 429/5xx errors before failing over
- [x] **Pattern-Based Routing:** User-configurable regex/keywords (e.g., "git", "bash") to force-route to local nano models
- [x] Fallback Chain (auto-retry next tier if the current tier completely fails)
- [x] **MCP Integration (official `mcp` SDK):** Migrate from custom REST client to official Anthropic MCP Python SDK with `@modelcontextprotocol/server-git`
- [x] Create multi-stage `Dockerfile` (optimized for ML dependencies)
- [x] **Batteries-Included Config:** Ship annotated `smartrouter.yaml` with default regex patterns to simplify UX
- [x] **Enterprise License Manager:** Implement `LicenseManager` to gate Phase 3 and Phase 5 features via `SMARTROUTER_LICENSE_KEY`
- [ ] **E2E Testing:** Verify retries, load balancing, fallback chains, and circuit breakers (no mocking)

## Phase 4 (v0.4): Developer Tools, Knowledge, & Guardrails
*Goal: Add visibility, RAG capabilities, safety guardrails, and debugging tools.*

- [ ] **Toxicity & Guardrails:** Use local model (e.g., Llama-Guard) to block toxic inputs/outputs
- [ ] **Auto-Few-Shot Prompting:** Dynamically inject similar successful past queries as examples
- [ ] **RAG-as-a-Service:** Inject context from uploaded documents into the prompt
- [ ] **OpenTelemetry (OTEL) Export:** Emit traces to Datadog, Langfuse, or Phoenix
- [ ] Analytics Web Dashboard (simple UI to view routing decisions and cost savings)
- [ ] `GET /v1/explain` endpoint (returns the chosen model and why)
- [ ] `force_model` override (via custom headers or prompt injection for testing)
- [ ] **Per-Client Routing Policy:** Set default `routing_preference` at the API key level (e.g., enterprise clients always get `frontier_only`) rather than requiring per-request overrides
- [ ] Persistent System Prompt Injection (append/prepend from config)
- [ ] **Data Flywheel (Self-Healing Router):** 
  - `POST /v1/feedback`: Endpoint to flag bad routing decisions from the frontend UI
  - `scripts/retrain_nightly.py`: CRON script to pass flagged mistakes through the LLM-as-a-judge, append to `training_seed.jsonl`, retrain the classifier, and hot-reload the `.pkl` model. **Must call `GuardrailsManager.redact_pii()` on prompts before sending to OpenAI to prevent data leakage.**
- [ ] **E2E Testing:** Verify guardrails, RAG injection, and OTEL traces end-to-end

## Phase 5 (v0.5): Enterprise Competitive Parity
*Goal: Close feature gaps with enterprise competitors (Kilo, RouteLLM, Latitude).*

- [ ] **Session-Aware Routing:** Track context across multi-turn conversational sessions to make better holistic routing decisions (Gap vs. Kilo)
- [ ] **Preference-Based Routing Engine:** Use Chatbot Arena Elo ratings / human preference data rather than naive complexity scoring (Gap vs. RouteLLM)
- [ ] **Domain-Specific Benchmarking:** Create specialized routing profiles/benchmarks for coding and structured tasks (Gap vs. Kilo)

## Phase 6 (v1.0): Open Source Launch & Distribution
*Goal: Frictionless adoption for the community.*

- [ ] `smartrouter` CLI (commands: `start`, `export`, `import`)
- [ ] Profile Bundles (`.srprofile` context portability and sharing)
- [ ] Python Middleware implementation (drop into existing FastAPI apps)
- [ ] Documentation, Quickstart Guide, and PyPI distribution
- [ ] SSO / Auth Gateway integration (API keys mapping to users)
- [ ] **`smartrouter explain` CLI:** Subcommand to debug routing decisions transparently against a prompt
- [ ] **Community Classifier Registry:** Hub to upload and download domain-optimized `.pkl` classifier models
- [ ] **Shared Savings Billing Engine:** Calculate "Hypothetical vs Actual" costs to automatically bill clients 10% of the money saved in BYOK mode
- [ ] **E2E Testing:** Verify CLI and Docker deployments operate successfully in a clean environment
