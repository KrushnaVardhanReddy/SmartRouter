# 🧠 SmartRouter — Brainstorming Session

This is a living scratch pad. Nothing here is final. Add, remove, and challenge anything freely.

---

## 💡 The Core Idea

A lightweight, open-source **proxy router** that sits between your app and LLM providers.
Instead of sending every prompt to an expensive frontier model, it **classifies the prompt's complexity** and routes it to the cheapest model capable of answering it well.

```
Your App  →  SmartRouter  →  Groq / OpenAI / Anthropic
                ↑
        (Complexity Classifier)
```

**Key Hook:** You only change one line of code — your `base_url`. Everything else stays identical.

---

## 📍 Product Positioning — Where Does SmartRouter Live?

> **The most important question to answer before building anything.**

### The Core Mental Model

SmartRouter is a **reverse proxy for LLM traffic** — exactly like Nginx is a reverse proxy for web traffic. It sits *between* your application and the LLM providers. It is NOT a cloud service you sign up for (initially). It is infrastructure YOU run on your own machine or server.

```
WITHOUT SmartRouter:
  Your App ─────────────────────────────────────────► OpenAI ($$$)

WITH SmartRouter (self-hosted):
  Your App ──► SmartRouter :8080 ──► Groq       (score < 0.4, ~$0.05/1M)
                                ──► OpenAI mini  (score 0.4–0.8, ~$0.15/1M)
                                ──► Anthropic    (score > 0.8, ~$3.00/1M)
```

**The one-line change to integrate:**
```python
# Before
client = OpenAI(api_key="sk-...")

# After — everything else in your code stays identical
client = OpenAI(api_key="sk-...", base_url="http://localhost:8080/v1")
```

### Deployment Mode 1: Self-Hosted Docker / Binary (v0.1 — Primary Target)

**Who:** Individual developers, small startups, privacy-conscious teams.

```bash
# Option A: Docker
docker run -v ./smartrouter.yaml:/config.yaml -p 8080:8080 smartrouter/smartrouter

# Option B: pip install
pip install smartrouter
smartrouter start --config smartrouter.yaml
```

**Where it lives:** On your own machine, VPS, or Kubernetes cluster. Your API keys never leave your infrastructure. Fully private. Fully auditable open-source code.

**Best for:** "I want to cut my OpenAI bill and I'm comfortable running a Docker container."

### Deployment Mode 2: Python Middleware / Library (v1.0)

**Who:** Python developers who already have a FastAPI/Flask backend and don't want a separate process.

```python
from smartrouter import SmartRouterMiddleware
app.add_middleware(SmartRouterMiddleware, config="smartrouter.yaml")
# Your existing endpoints now auto-route through SmartRouter
```

**Where it lives:** Inside your existing Python app. No separate server, no Docker container.

**Best for:** "I'm already running FastAPI. I want to drop in a middleware and have smart routing happen automatically."

### Deployment Mode 3: SmartRouter Cloud — api.smartrouter.dev (Paid SaaS, v1.0+)

**Who:** Teams who want zero infrastructure. Just a URL to point at.

```python
client = OpenAI(
    api_key="sk-smartrouter-YOUR_KEY",
    base_url="https://api.smartrouter.dev/v1"
)
# We handle routing. You get one unified invoice.
```

**Where it lives:** On our cloud. We manage uptime, billing aggregation across providers, and infrastructure.

**Best for:** "I don't want to manage infrastructure. Just make my AI costs cheaper."

### Summary

| Mode | Runs On | Data Privacy | Cost | Target Version |
|---|---|---|---|---|
| Self-hosted Docker | Your infra | 🔒 Fully private | Free (OSS) | v0.1 |
| Python Middleware | Your app | 🔒 Fully private | Free (OSS) | v1.0 |
| SmartRouter Cloud | Our servers | ⚠️ Routes through us | Paid SaaS | v1.0+ |

> **Playbook:** Start open-source to get trust + GitHub stars → launch cloud version for teams who don't want to manage infrastructure. This is the exact model used by Grafana, Supabase, and Posthog.

---

## ✅ Decisions Made

| Decision | Choice | Why |
|---|---|---|
| Language | Python | Network-bound, not CPU-bound. ML ecosystem is Python-native. Fastest v1. |
| Web Framework | FastAPI | Async, OpenAPI docs auto-generated, production-grade. |
| ML Classifier | Scikit-Learn Logistic Regression | Fast, lightweight, already have working script in Local_AI_Assistant. |
| Embeddings | `sentence-transformers` | Best-in-class for semantic text embeddings in Python. |
| Config | `pydantic-settings` | Reads from `.env.local`, type-safe. |
| Dev Approach | Spec-First (Antigravity Planning Mode) | Prevents vibe coding and architectural drift. |
| AI Delegation | Antigravity + Jules + OpenCode | Three-tier delegation model reused from BusTracking/Local_AI_Assistant. |
| Contract Method | OpenAI-compatible OpenAPI spec | `ChatCompletionRequest` Pydantic models mirror OpenAI's exact schema. |

---

## ❓ Open / Unsettled Questions

These need answers before we start writing code:

### 1. Distribution Strategy
- **Docker** — The obvious choice for self-hosting. Simple `docker run` command.
- **PyInstaller** — Single binary (`smartrouter.exe` / `smartrouter`). Very user-friendly, but could be 1GB+ due to ML libraries.
- **pip install smartrouter** — Developers run `pip install smartrouter` and then `smartrouter start`. Clean, familiar developer experience.
- **Which do we prioritize first?**

### 2. The Classifier — What Exactly Are We Scoring?
- Current approach: A binary/continuous "complexity" score from 0.0 to 1.0.
- But what does "complexity" mean? Is it:
  - **Length?** (short = simple, long = complex) — Too naive.
  - **Semantic complexity?** (sentence-transformers embedding → logistic regression) — Our current plan.
  - **Intent?** (coding task, creative writing, factual lookup) — More nuanced, harder to label.
- How do we **label the training data**? Manually? Synthetically?

### 3. Training Data — Where Does It Come From?
- **Synthetic:** Use GPT-4 to generate 1000 "simple" and 1000 "complex" prompt examples. Label them.
- **Community-sourced:** After launch, let users flag bad routes ("this was too complex for the cheap model!"). Use feedback to retrain.
- **Pre-labeled datasets:** ShareGPT, LMSYS Chatbot Arena data.

### 4. Fallback & Quality Guarantee Strategy
- What happens if the cheap model gives a bad answer?
  - Option A: **User manually flags it** → reroutes to smart model → logs for retraining.
  - Option B: **Auto-judge:** Run a tiny LLM judge on the cheap model's response; if confidence is low, retry with smart model (but this doubles cost/latency).
  - Option C: **No fallback for v1.** Keep it simple.

### 5. Streaming Support
- OpenAI supports `"stream": true` for real-time token streaming.
- Do we need to support this in v1? It adds complexity (Server-Sent Events proxy).
- Most real apps use streaming — without it, adoption might be limited.

### 6. Monetization — Which Model First?
- **SaaS Cloud Version** (Managed hosting, `base_url = https://api.smartrouter.dev/v1`)
- **Open Core** (Free self-hosted + paid enterprise features)
- **Unified Billing Gateway** (We pay OpenAI/Groq, you pay us one invoice)
- **Which monetization path do we build toward from day 1?** (affects architecture decisions)

### 7. Name: SmartRouter vs OpenRouter-Lite vs DynamicLlmRouting?
- `OpenRouter` is already a well-known existing service. Risk of confusion?
- `SmartRouter` is clean and descriptive.
- `DynamicLlmRouting` is the GitHub repo name. Too verbose for branding?

---

## ⚙️ Configurable Provider System (Big Design Decision)

> **The idea:** SmartRouter should be fully provider-agnostic. Every tier is just an `(base_url, model, api_key)` tuple. Mix and match cloud + local freely.

### The Core Concept

A "tier" is not tied to any specific provider. Since almost every LLM provider (Groq, OpenAI, Anthropic, Together AI, Fireworks, Cloudflare Workers AI, Ollama, LM Studio) exposes an OpenAI-compatible `/v1/chat/completions` endpoint, SmartRouter can route to **any of them interchangeably**.

```
Tier Cheap  =  any base_url  +  any model name
Tier Mid    =  any base_url  +  any model name
Tier Smart  =  any base_url  +  any model name
```

### Proposed Configuration File (`smartrouter.yaml`)

```yaml
# SmartRouter Configuration — define your own tiers, any provider, any model

router:
  low_threshold: 0.35    # Score below this → Tier "cheap"
  high_threshold: 0.75   # Score above this → Tier "smart"
  # Scores in between → Tier "mid"

tiers:
  cheap:
    base_url: "http://localhost:11434/v1"   # Ollama running locally — FREE
    model: "llama3.2:3b"
    api_key: ""                              # No key needed for local
    timeout_seconds: 10

  mid:
    base_url: "https://api.groq.com/openai/v1"  # Groq Cloud — ultra-fast
    model: "llama-3.1-8b-instant"
    api_key: "${GROQ_API_KEY}"               # Reads from .env.local
    timeout_seconds: 30

  smart:
    base_url: "https://api.openai.com/v1"   # OpenAI — most capable
    model: "gpt-4o"
    api_key: "${OPENAI_API_KEY}"
    timeout_seconds: 60
```

### Real-World Config Examples

**Example 1: Pure Local (zero cost, fully private)**
```yaml
tiers:
  cheap:  { base_url: "http://localhost:11434/v1", model: "qwen2.5:0.5b" }
  mid:    { base_url: "http://localhost:11434/v1", model: "llama3.2:3b" }
  smart:  { base_url: "http://localhost:11434/v1", model: "llama3.1:70b" }
```

**Example 2: Cost-optimized cloud mix**
```yaml
tiers:
  cheap:  { base_url: "https://api.cloudflare.com/.../ai/v1", model: "@cf/meta/llama-3.1-8b-fast-v2" }
  mid:    { base_url: "https://api.groq.com/openai/v1",       model: "llama-3.1-8b-instant" }
  smart:  { base_url: "https://api.anthropic.com/v1",         model: "claude-3-5-sonnet" }
```

**Example 3: Enterprise (self-hosted + cloud fallback)**
```yaml
tiers:
  cheap:  { base_url: "http://internal-llm.company.com/v1", model: "company-finetuned-3b" }
  mid:    { base_url: "http://internal-llm.company.com/v1", model: "company-finetuned-13b" }
  smart:  { base_url: "https://api.openai.com/v1",          model: "gpt-4o" }  # only for truly hard tasks
```

### Why This is a Strategic Moat

| Benefit | Detail |
|---|---|
| **Provider Portability** | Switch from OpenAI to Groq to Together AI by editing one YAML line |
| **Local + Cloud Hybrid** | Run cheap requests on Ollama (free, private), expensive on cloud |
| **Zero Vendor Lock-in** | The router works identically regardless of who is providing the models |
| **Enterprise Ready** | Companies with on-prem LLMs can plug them in as the "cheap" tier immediately |
| **Future Proof** | When a new, cheaper provider launches, you just update the config — no code changes |

### One Open Question

> Should we support **more than 3 tiers**? For example, 5 tiers with finer-grained thresholds?
> 
> Possible config extension:
> ```yaml
> tiers:
>   - { name: "nano",   threshold_max: 0.2,  base_url: "...", model: "..." }
>   - { name: "micro",  threshold_max: 0.4,  base_url: "...", model: "..." }
>   - { name: "medium", threshold_max: 0.65, base_url: "...", model: "..." }
>   - { name: "large",  threshold_max: 0.85, base_url: "...", model: "..." }
>   - { name: "max",    threshold_max: 1.0,  base_url: "...", model: "..." }
> ```
> This would make SmartRouter extremely flexible but adds complexity to the classifier calibration.

---

## 🗺️ Rough Roadmap (Strawman)

```
v0.1  →  Passthrough proxy (FastAPI, no ML)
          Just proves the OpenAI-compatible API works end-to-end.

v0.2  →  Add the classifier (complexity score 0.0 - 1.0)
          Route to Groq (cheap) or GPT-4o-mini (mid).

v0.3  →  Add 3rd tier (Claude 3.5 Sonnet for hard tasks)
          Add streaming support.
          Add a `/v1/usage` endpoint showing cost savings.

v0.4  →  Analytics dashboard (simple web UI)
          Show per-request routing decisions, cost saved, model used.

v1.0  →  Stable release. Docker image on DockerHub. pip install.
          Community-sourced retraining pipeline.
```

---

## 🔥 Hot Takes & Provocative Ideas

- **What if the router exposed a `/explain` endpoint?** It returns not just the answer, but which model was chosen and why (complexity score, threshold, estimated cost saved). This would be a viral developer feature.
- **What if we supported a `force_model` override?** `{"model": "smart-auto", "x-smartrouter-force": "groq/llama-3"}` — lets developers hard-pin specific routes for testing.

---

## 🤖 MCP & Agent-to-Agent Integration (Big Idea)

> **The question:** Can existing IDEs and AI agents use SmartRouter without any code changes?
> **The answer: Yes — through three integration surfaces.**

### Surface 1: OpenAI-Compatible API (Already Planned — Zero Friction)

Because SmartRouter exposes a `/v1/chat/completions` endpoint, **every major AI IDE already works with it out of the box** by just changing `base_url`:

| IDE / Tool | Where to Change | Setting |
|---|---|---|
| **Cursor** | Settings → Models → Base URL | `http://localhost:8080/v1` |
| **Windsurf / Codeium** | Settings → Custom Endpoint | `http://localhost:8080/v1` |
| **Continue.dev** | `~/.continue/config.json` → `openai.baseURL` | `http://localhost:8080/v1` |
| **Antigravity** | MCP config / model settings | `http://localhost:8080/v1` |
| **LangChain / LlamaIndex** | `ChatOpenAI(base_url=...)` | `http://localhost:8080/v1` |
| **OpenAI Python SDK** | `OpenAI(base_url=...)` | `http://localhost:8080/v1` |

**Zero code changes in those tools. This alone is a massive adoption driver.**

---

### Surface 2: MCP Server (Native Agent Tool Integration)

SmartRouter can also expose itself as an **MCP (Model Context Protocol) server**.
This lets MCP-aware agents (Claude Desktop, Cursor Agent, Antigravity, etc.) call SmartRouter as a **tool**, not just a raw HTTP endpoint.

**Proposed MCP tools:**

```json
{
  "tools": [
    {
      "name": "route_prompt",
      "description": "Route a prompt to the cheapest capable LLM. Returns the model response.",
      "inputs": ["prompt", "system_message", "max_tokens"]
    },
    {
      "name": "estimate_cost",
      "description": "Predict which model would be chosen for a prompt and estimate the cost.",
      "inputs": ["prompt"]
    },
    {
      "name": "get_savings_report",
      "description": "Return a summary of cost savings across all routed requests.",
      "inputs": []
    }
  ]
}
```

**Why this matters:** When an AI agent calls `route_prompt` via MCP, it can offload all cost-optimization logic to SmartRouter entirely. Multi-step agentic pipelines (LangGraph, CrewAI) that make hundreds of LLM calls become dramatically cheaper.

---

### Surface 3: Agent-to-Agent (A2A by Google — Future)

Google's **A2A protocol** lets agents register themselves as callable agents in a broader multi-agent ecosystem. SmartRouter could register itself as a "Router Agent":

```yaml
# .well-known/agent.json
name: SmartRouter
description: Cost-optimizing LLM routing agent. Routes prompts to the cheapest capable model.
capabilities:
  - llm_routing
  - cost_estimation
  - usage_reporting
```

This would allow **AutoGen, CrewAI, LangGraph, and Google ADK** pipelines to automatically discover and delegate to SmartRouter as a cost-optimization layer in their agent networks.

---

### Integration Strategy (Phased)

| Phase | Integration | Effort | Impact |
|---|---|---|---|
| v0.1 | OpenAI-compatible REST API | ✅ Already in plan | 🔥🔥🔥 Immediate IDE compatibility |
| v0.3 | MCP Server | Medium | 🔥🔥🔥 Native agent tool support |
| v1.0+ | A2A Agent Registration | Low (mostly JSON config) | 🔥 Future multi-agent ecosystems |

**Key insight:** The OpenAI-compatible API gets us IDE adoption for free. MCP gets us deep agentic adoption. A2A future-proofs us for the agent-to-agent web. All three can coexist in the same server.
- **What if we built a VS Code extension?** It intercepts GitHub Copilot requests and runs them through SmartRouter first. Saves money on AI-assisted coding bills.

---

## 🚧 Known Risks

| Risk | Mitigation |
|---|---|
| Classifier misroutes a hard task to a cheap model | User feedback loop + conservative thresholds |
| `sentence-transformers` adds 500ms+ to each request | Semantic cache for repeated prompts; use lighter model |
| PyInstaller binary is too large (1GB+) | Prioritize Docker; offer `pip install` as primary distribution |
| OpenRouter (existing service) brand confusion | Brand clearly as "SmartRouter" — different positioning (self-hosted, open source) |

---

## 💡 New Ideas (Round 2)

### Idea 1: Semantic Cache
Before running the classifier or hitting any LLM, check if this prompt is **nearly identical** to a recent one (cosine similarity > 0.95 against a local vector cache). Return the cached response instantly.

```yaml
cache:
  enabled: true
  similarity_threshold: 0.95  # 0.0 = exact match only, 1.0 = cache everything
  ttl_seconds: 3600           # How long to keep cached responses
  max_entries: 1000
```

**Why this matters:**
- Zero API cost for repeated/similar prompts
- Near-instant response (< 1ms)
- Perfect for apps that repeat system prompts or FAQs
- Works **on top of** the routing layer — even cheaper than routing to Groq

**Effort:** Medium (need a small in-memory vector store like `faiss` or `hnswlib`)

---

### Idea 2: Budget Circuit Breaker
Users set a monthly cost budget. SmartRouter tracks spend in real-time and automatically **downshifts tiers** as the budget is consumed.

```yaml
budget:
  monthly_usd: 50.00
  warning_at_percent: 80    # Log a warning at 80% budget
  downshift_at_percent: 90  # At 90%, all "mid" requests → "cheap"
  lockdown_at_percent: 100  # At 100%, ALL requests → "cheap"
```

**Why this matters:**
- Eliminates the #1 fear for indie hackers: surprise cloud bills
- Completely transparent — users see exactly what is being spent
- Sellable as a feature: "Never overspend on AI again"

**Effort:** Low (just track token counts × price per token per provider)

---

### Idea 3: Fallback Chain (Resilience)
If the selected tier is rate-limited (HTTP 429) or unreachable (timeout), SmartRouter automatically retries with the next tier up, rather than returning an error.

```yaml
tiers:
  cheap:
    base_url: "https://api.groq.com/openai/v1"
    model: "llama-3.1-8b-instant"
    fallback_to: "mid"   # If Groq is down/rate-limited → try mid tier
  mid:
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o-mini"
    fallback_to: "smart"
  smart:
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o"
    fallback_to: null    # No fallback — return error
```

**Why this matters:**
- Makes SmartRouter production-grade from day one
- Groq and other free-tier providers are frequently rate-limited
- Users never see a 429 error — it's handled silently

**Effort:** Low (just catch HTTP 429/503 and retry with next tier's client)

---

## ✅ Final MVP Verdict — What to Actually Build First

After all the brainstorming, here is the recommended v0.1 → v1.0 scope:

### v0.1 — The Proof of Concept (Build this first, ~2-3 days)
> Goal: Prove the OpenAI-compatible proxy works end-to-end with configurable tiers.

- [ ] FastAPI server with `POST /v1/chat/completions`
- [ ] `smartrouter.yaml` config file with 3 configurable tiers (any `base_url` + model)
- [ ] Simple **round-robin / hardcoded** routing (no ML yet — always use "mid")
- [ ] Validate with `openai` Python SDK and Cursor IDE

### v0.2 — The Smart Router (~1 week)
> Goal: Add the complexity classifier.

- [ ] Classifier training script (adapt from `Local_AI_Assistant`)
- [ ] Embed prompt → score → route to correct tier
- [ ] Streaming support (`stream: true` SSE proxy)
- [ ] `GET /v1/usage` — cost savings report endpoint
- [ ] `X-SmartRouter-Model` and `X-SmartRouter-Score` response headers

### v0.3 — Production Ready (~2 weeks)
> Goal: Make it something people actually want to run in prod.

- [ ] Semantic cache (faiss/hnswlib)
- [ ] Budget circuit breaker
- [ ] Fallback chain on 429/503
- [ ] MCP server (`/.well-known/mcp/`)
- [ ] Docker image on DockerHub

### v1.0 — Open Source Launch
> Goal: Make it easy for the community to adopt and contribute.

- [ ] `pip install smartrouter` + `smartrouter start`
- [ ] Web dashboard (cost analytics, routing decisions)
- [ ] Community classifier retraining from user feedback
- [ ] Full documentation + quickstart guide
