# SmartRouter Task Tracker

This document tracks the execution phases of the SmartRouter project.
Tasks assigned to Jules (Tier 2) are marked with `(Jules)`.

## Phase 1: Core Setup & Contract Definition

- [x] Initialize Python project using `uv`
- [x] Define `contracts/openapi.yaml` (OpenAI proxy schema)
- [x] Define `contracts/config_schema.json` (Configuration schema)
- [ ] (Jules) Generate Pydantic models in `smartrouter/api/models.py` (P1-T1)
- [ ] (Jules) Implement basic FastAPI setup in `smartrouter/main.py` (P1-T2)
- [ ] (Jules) Set up test skeleton in `tests/test_api/test_routes.py` (P1-T3)

## Phase 2: Passthrough Router (No ML yet)

- [ ] Add `base_provider.py` abstract interface
- [ ] Implement OpenRouter client wrapper
- [ ] Connect FastAPI routes to passthrough client

## Phase 3: Classifier Integration

- [ ] Set up `train_classifier.py`
- [ ] Add scikit-learn and sentence-transformers dependencies
- [ ] Create `classifier/engine.py` for scoring prompts

## Phase 4: Dynamic Routing Logic

- [ ] Read thresholds from `smartrouter.yaml` config
- [ ] Route low scores to cheap tier, high scores to smart tier

## Phase 5: Distribution (PyInstaller & Docker)

- [ ] Create multi-stage `Dockerfile`
- [ ] Prepare distribution scripts
