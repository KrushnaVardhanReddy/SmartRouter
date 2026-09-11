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
- **What if we built a VS Code extension?** It intercepts GitHub Copilot requests and runs them through SmartRouter first. Saves money on AI-assisted coding bills.

---

## 🚧 Known Risks

| Risk | Mitigation |
|---|---|
| Classifier misroutes a hard task to a cheap model | User feedback loop + conservative thresholds |
| `sentence-transformers` adds 500ms+ to each request | Cache embeddings for identical prompts; use a lighter model |
| PyInstaller binary is too large (1GB+) | Prioritize Docker; offer `pip install` as primary distribution |
| OpenRouter (existing service) brand confusion | Brand clearly as "SmartRouter" — different positioning (self-hosted, open source) |
