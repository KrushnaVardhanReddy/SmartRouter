# 🚦 SmartRouter (OpenRouter-Lite)

### Intelligent, Cost-Saving LLM Router for Developers

## The Problem

Developers building AI applications often default to using expensive, frontier models (like GPT-4o or Claude 3.5 Sonnet) for **every single prompt** to guarantee high quality. However, a significant percentage of user prompts (e.g., summarizing a short text, extracting JSON, or answering basic trivia) are simple enough that a much cheaper, faster model (like Llama-3-8B or GPT-4o-mini) could handle them perfectly. 

Sending a trivial prompt to a frontier model is a massive waste of money and unnecessarily increases latency.

## The Solution

An open-source, lightweight proxy router that acts as a middleman between your application and LLM providers. 

When your app sends a prompt, the router instantly analyzes its "complexity". 
- If the prompt is simple, it seamlessly routes the request to a **cheap and fast model** (e.g., Llama-3 via OpenRouter). 
- If the prompt is highly complex (e.g., advanced reasoning, heavy coding), it routes the request to an **expensive, smart model** (e.g., Claude 3.5 Sonnet via OpenRouter).

**The Result:** You maintain frontier-level quality on hard tasks while slashing your overall API bill by up to 80% on easy tasks.

## How It Works Under the Hood

1. **The Classifier:** We train a fast, lightweight local classifier (such as a Scikit-Learn Logistic Regression model using `nomic-embed-text` embeddings, or a small BERT model). 
2. **Scoring:** When a prompt arrives, the classifier generates a "Complexity Score" from `0.0` to `1.0` in milliseconds.
3. **Routing Thresholds:** 
   - `Score < 0.4` ➡️ Route to `meta-llama/llama-3-8b-instruct` (via OpenRouter) - Cost: ~$0.05 / 1M tokens
   - `0.4 <= Score <= 0.8` ➡️ Route to `openai/gpt-4o-mini` (via OpenRouter) - Cost: ~$0.15 / 1M tokens
   - `Score > 0.8` ➡️ Route to `anthropic/claude-3.5-sonnet` (via OpenRouter) - Cost: ~$3.00 / 1M tokens
4. **Enterprise Guardrails (Optional):** Prompts are checked for PII redaction and jailbreaks before routing.
5. **Standardized API:** The router exposes a standard OpenAI-compatible API endpoint. To the developer, it looks exactly like querying `openai.chat.completions.create(...)`, but the router handles the magic behind the scenes.

## Why This is a Great Open-Source Project

- **High Demand:** Everyone is trying to cut AI costs right now.
- **Easy Integration:** By making it an OpenAI-compatible proxy, developers only need to change their `base_url` to use it. No heavy SDKs required.
- **Data Flywheel:** As users interact with the router, they can flag "bad responses" (where the cheap model failed), creating a dataset to continuously retrain and improve the routing classifier's accuracy.

## Competitors in the Space

- **LiteLLM & Portkey:** Great proxies/gateways for unified APIs, but they lack true ML-based dynamic semantic routing based on prompt complexity.
- **RouteLLM (LMSYS):** Excellent OSS dynamic routing based on human preferences, but it's a Python library, not a standalone production gateway.
- **Martian:** Highly effective proprietary router, but it is a black-box SaaS (enterprise trust issue).
- **Amazon Bedrock Intelligent Prompt Routing:** Fully managed enterprise AWS service, but suffers from deep vendor lock-in.
- **Latitude:** Strong for cost tracking and workflow integration, but less focused on granular ML complexity classification.
- **Kilo Autoefficient:** Intelligent session-aware router, but heavily specialized for coding tasks.

## Monetization Strategy (Open Core)

SmartRouter follows an **Open Core** model. The core router, classifier, and proxy are 100% open-source (MIT). 

We monetize by offering an **Enterprise License Key** (`SMARTROUTER_LICENSE_KEY`) that unlocks premium features within the same Docker image. Large corporations (banks, healthcare) who need compliance and scale can pay for a license to activate:
- PII Redaction & Jailbreak Blocking
- Advanced API Key Load Balancing & Retries
- Semantic Caching
- Session-Aware & Preference-Based Routing

This creates a sustainable business model without splitting the codebase or forcing complex migrations on users.

## Development Approach

This project is built using a **Spec-First methodology**, powered by **Antigravity (Planning Mode)**.

Instead of "vibe coding" directly, every feature follows a structured, three-phase pipeline before a single line of production code is written:

1. **`requirements.md`** — Captures user stories, acceptance criteria, and the problem definition.
2. **`implementation_plan.md`** — Documents the technical architecture, data flow, API contracts, and key design decisions.
3. **`task.md`** — A living checklist that breaks the plan into discrete, trackable implementation tasks.

The AI agent reviews and proposes each spec document first. **Work only begins after explicit human approval.** This prevents architectural drift, keeps the codebase intentional, and ensures the AI never surprises you with unexpected structural changes.

## Tech Stack Decision

| Language | Proxy Speed | ML/Classifier | Dev Speed | Docker Size | Verdict |
|---|---|---|---|---|---|
| 🦀 **Rust** | ⚡⚡⚡ Fastest | ❌ Poor ecosystem | 🐢 Slowest | ✅ Tiny | Overkill |
| 🐹 **Go** | ⚡⚡ Very Fast | ⚠️ Needs sidecar | 🚶 Moderate | ✅ Small | Good, but split-language |
| 🐍 **Python** | ⚡ Fast Enough | ✅ Best-in-class | 🏃 Fastest | ⚠️ Larger | **✅ Winner** |

### Why Python (FastAPI) wins for v1:

- **The bottleneck is the network, not the CPU.** The router waits on OpenAI/Groq's response (~500ms–2s). Python's overhead of a few milliseconds is completely irrelevant.
- **ML lives in Python.** The classifier (scikit-learn, sentence-transformers, ONNX) runs natively with zero IPC overhead. In Go/Rust, you'd need a separate Python microservice, adding complexity.
- **FastAPI is production-grade.** It is async (ASGI/uvicorn), handles thousands of concurrent connections, and auto-generates OpenAPI docs.
- **Fastest time-to-v1.** Easier for open-source contributors to understand, fork, and contribute to.
- **Future path:** If a specific hot path ever becomes a bottleneck, that single component can be rewritten in Go later without rewriting the whole project.

**Stack:** `Python 3.14` · `FastAPI` · `uvicorn` · `httpx (async)` · `scikit-learn` · `sentence-transformers` · `Docker`

## Contract-Based Development

The API contract is the **single source of truth** shared between the server (backend) and any clients (frontend dashboard, SDKs, CLI tools). Neither side makes assumptions — everything is derived from the contract.

### How it works

1. **Define the contract first** — Before writing any implementation code, the OpenAI-compatible API contract is defined in an `openapi.yaml` spec file.
2. **Auto-generate both sides** — The backend server stubs and the frontend/SDK client are both generated from the same `openapi.yaml`. They can never drift out of sync.
3. **Validate against the contract** — All incoming requests are validated against the spec automatically. Any request that doesn't match the contract is rejected before it ever touches business logic.

### Contract files (to be created in `.kiro/` or `contracts/`)

| File | Purpose |
|---|---|
| `contracts/openapi.yaml` | The master OpenAI-compatible API spec for the router |
| `contracts/classifier_schema.json` | JSON Schema for the internal classifier request/response |
| `contracts/config_schema.json` | JSON Schema for the routing threshold configuration |

### Tools

- **FastAPI** auto-generates and serves a live `/docs` (Swagger UI) and `/redoc` page directly from the Python type annotations, keeping code and contract always in sync.
- **openapi-generator** is used to generate typed SDK clients (Python, TypeScript) for the managed cloud dashboard frontend.

## IDE Integration (Cursor, VS Code, Antigravity)

Because SmartRouter exposes a standard OpenAI-compatible API, you can point any modern AI coding assistant to your router to instantly save on API costs during development. 

*Note: Use `http://localhost:8080/v1` if you are self-hosting via Docker, or `https://api.smartrouter.dev/v1` if you are using the managed Cloud SaaS.*

### 1. Cursor IDE
1. Open Cursor Settings (⚙️) > **Models**.
2. Under **OpenAI API Key**, enter your key (e.g., `sk-smartrouter-xxx`).
3. Under **OpenAI Base URL**, click "Override" and enter: `https://api.smartrouter.dev/v1` (or localhost).
4. Type `smartrouter-auto` in the model dropdown to let SmartRouter dynamically pick the best model for your edit.

### 2. Antigravity / Kiro
If you are using Antigravity, you can override the LLM provider in your `~/.gemini/config/mcp_config.json` or environment variables:
```bash
export OPENAI_API_KEY="sk-smartrouter-xxx"
export OPENAI_BASE_URL="https://api.smartrouter.dev/v1"
```

### 3. VS Code (Continue.dev / Cline)
In your `config.json` for Continue or Cline, add SmartRouter as a custom OpenAI provider:
```json
{
  "models": [
    {
      "title": "SmartRouter (Dynamic)",
      "provider": "openai",
      "model": "smartrouter-auto",
      "apiKey": "sk-smartrouter-xxx",
      "apiBase": "https://api.smartrouter.dev/v1"
    }
  ]
}
```

## AI Delegation Strategy

This project uses a **Three-Tier AI Delegation Model** to maximize efficiency and minimize cost:

```
┌─────────────────────────────────────────────────────┐
│  Tier 1 · Antigravity (Interactive, Planning Mode)  │
│  Complex architecture, debugging, spec writing,     │
│  contract design, UI work, multi-file refactors     │
├─────────────────────────────────────────────────────┤
│  Tier 2 · Jules (Async Cloud Agent, PR-based)       │
│  Unit tests, docs, boilerplate, lint fixes,         │
│  model generation, migration scripts                │
├─────────────────────────────────────────────────────┤
│  Tier 3 · OpenCode (Local LLM, Quick Edits)         │
│  Config tweaks, single-file edits, renaming,        │
│  comment cleanup, quick formatting                  │
└─────────────────────────────────────────────────────┘
```

### Jules delegation rules for this project

**✅ Always delegate to Jules:**
- Writing `pytest` unit tests for new router endpoints
- Generating Pydantic model boilerplate from schema
- Writing/updating inline docstrings and API reference docs
- Creating `Dockerfile`, `docker-compose.yml`, `Makefile` boilerplate
- Linting fixes (`ruff`, `black`, `mypy` warnings)

**❌ Never delegate to Jules:**
- The routing classifier logic (needs back-and-forth tuning)
- Any changes that touch the core `openapi.yaml` contract
- Debugging latency or streaming issues (needs live testing)
- Multi-file refactors across `router/`, `classifier/`, and `api/` simultaneously

**Jules safety rules (include at the top of every Jules prompt):**
```
MANDATORY RULES — VIOLATION = REJECTED PR:
1. NEVER comment out or stub existing implementation code.
2. NEVER replace a working function body with # TODO or pass.
3. All modified files must pass: ruff check . && mypy .
4. If a test fails, FIX the code — do NOT delete or skip tests.
5. Do NOT modify contracts/openapi.yaml unless explicitly told to.
6. All new modules must include a corresponding test file in tests/.
7. Commit message must start with "jules: " prefix.
```

## Product Journey & Roadmap

SmartRouter starts as a self-hosted tool and evolves into a fully managed cloud service. The adoption journey is intentionally frictionless at every stage.

### Where SmartRouter Lives

```
v0.1  ──►  Docker container on your machine or VPS
           docker run -p 8080:8080 smartrouter/smartrouter
           Setup time: ~5 minutes

v0.3  ──►  pip install smartrouter (developer CLI)
           smartrouter start --config smartrouter.yaml
           Setup time: ~1 minute

v1.0  ──►  Python middleware (zero separate process)
           app.add_middleware(SmartRouterMiddleware)
           Setup time: 0 minutes — drop into existing app

v1.0+ ──►  SmartRouter Cloud — api.smartrouter.dev
           client = OpenAI(base_url="https://api.smartrouter.dev/v1")
           Setup time: 0 minutes — just change base_url
```

### Feature Roadmap

| Phase | Milestone | Key Features |
|---|---|---|
| **Phase 1 (v0.1)** | Core Setup & Passthrough Proxy | OpenAI-compatible passthrough, `smartrouter.yaml` config, configurable tiers. |
| **Phase 2 (v0.2)** | Smart Router (Classifier & Context) | Complexity classifier (scikit-learn), dynamic tier routing, streaming, `GET /v1/usage`. |
| **Phase 3 (v0.3)** | Enterprise Optimization & Resilience | PII Redaction, Jailbreak Blocking, Semantic Caching, Load Balancing, MCP Integration, Enterprise License Manager, Dockerfile. |
| **Phase 4 (v0.4)** | Developer Tools, Knowledge, & Guardrails | RAG-as-a-Service, OTEL Export, Analytics Dashboard, `force_model`. |
| **Phase 5 (v0.5)** | Enterprise Competitive Parity | Session-Aware Routing, Preference-Based Routing, Domain-Specific Benchmarking. |
| **Phase 6 (v1.0)** | Open Source Launch & Distribution | CLI, Profile Bundles, Python Middleware, SSO/Auth Gateway, PyPI. |

## Context Portability — Local ↔ Cloud

Switching between self-hosted and cloud (or sharing config with teammates) is a first-class feature. All routing context is captured in a portable **Profile Bundle** (`.srprofile`) that can be exported, imported, and version-controlled.

### What's in a Profile Bundle

| File | Contents | Secret? |
|---|---|---|
| `smartrouter.yaml` | Tier config, thresholds, model names | No — share freely |
| `complexity_classifier.pkl` | Your trained ML model | No — share freely |
| `routing_history.sqlite` | Past routing decisions and logs | No — share freely |
| `metadata.json` | Version, stats summary | No — share freely |
| `.env.local` | API keys | **Yes — never included** |

### Switching Local → Cloud in 4 Steps

```bash
# 1. Export your local context
smartrouter export --output myapp.srprofile

# 2. Push to SmartRouter Cloud
smartrouter push --cloud --api-key sk-smartrouter-YOUR_KEY

# 3. Change one line in your app
#    base_url="http://localhost:8080/v1"       # before
#    base_url="https://api.smartrouter.dev/v1" # after

# 4. Done — identical routing behavior in the cloud
```

### Sharing with Teammates

```bash
# Developer A: export and commit the profile
smartrouter export --output team.srprofile
git add team.srprofile && git commit -m "share routing profile"

# Developer B: import and start — same routing from day 1
git pull && smartrouter import --input team.srprofile && smartrouter start
```

> **Key principle:** API keys never leave your machine. Only the routing logic and training data travel in the bundle.
