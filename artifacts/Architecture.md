## Architecture Overview

This application is a lightweight AI-enabled talent & project management demo built with FastAPI, a modular LLM provider abstraction, and a SQLite persistence layer. It serves both HTML pages (Jinja2 templates) and JSON APIs for CRUD + AI augmentation.

### Core Layers
1. Presentation
	- FastAPI routes in `src/main.py` expose:
	  - UI pages: `/` (home), `/models` (model catalog)
	  - REST APIs: `/api/status`, `/api/models`, CRUD under `/api/project-managers` & `/api/employees`, utility endpoints (e.g. database reset)
	- Templates: `src/templates/` (Jinja2) for simple server‑rendered views.
2. Application / Service Logic
	- Request parsing & normalization (skills lists, metrics coercion) in route handlers.
	- Orchestration helpers in `utils/` (e.g. `helpers.py`, `artifacts.py`, `image_gen.py`).
3. AI Abstraction
	- `utils/llm.py` orchestrates model/client setup and provides unified functions: `get_completion`, `get_vision_completion`, `get_image_generation_completion` (+ async variants & compat wrappers).
	- Provider interface: `utils/providers/base.py` (Protocol) + concrete adapters (`openai.py`, `google.py`, `anthropic.py`, `huggingface.py`). Selection is driven by `RECOMMENDED_MODELS` mapping in `utils/models.py` and environment variables (API keys) loaded via `utils/settings.py`.
4. Data / Persistence
	- SQLite database file in `artifacts/` (lightweight, file‑based).
	- Access layer in `utils/database.py` handles initialization, seed data, serialization, and CRUD for project managers & employees, including related normalized tables (skills, metrics, required skills) when present.
5. Cross‑Cutting Concerns
	- Logging: `utils/logging.py` standardizes structured logs.
	- Error normalization: `utils/errors.py` (custom exceptions like provider failures).
	- Rate limiting / safety hooks (placeholder): `utils/rate_limit.py` (if extended).
	- Artifact persistence & PlantUML generation helpers: `utils/artifacts.py`, `utils/plantuml.py`.

### Typical Request Flow (CRUD Example)
Browser / Client -> FastAPI route (`/api/employees`) -> Input normalization (skills, metrics) -> `utils/database.py` insert/select -> Serialize row(s) -> JSONResponse.

### AI Invocation Flow
Prompt (internal helper or future endpoint) -> `utils.llm.setup_llm_client()` (once at startup via lifespan) -> `get_completion(...)` -> Provider adapter (selected from mapping) -> External Model API -> Unified response -> (Optional) post‑processing (JSON extraction / cleaning) -> Returned to caller.

### Key Use Cases
- View available LLM models & provider status.
- Maintain project manager and employee records (skills, metrics, summaries).
- Reset / seed database for demo consistency.
- (Extensible) Generate structured data or content via LLM (helper `_llm_generate_json` in `main.py`).
- (Extensible) Vision & image generation through provider abstraction.

### Deployment & Runtime
- Runs a single FastAPI process (e.g. with Uvicorn) – stateless aside from SQLite file + JSON conversation log (`artifacts/conversations.json`).
- Environment-driven configuration (.env for API keys). Missing keys simply exclude those providers.

### Extensibility Points
- Add new model/provider: implement adapter in `utils/providers/`, register in `PROVIDERS`, extend `RECOMMENDED_MODELS`.
- Add new domain entity: create table + CRUD functions in `utils/database.py`, expose routes.
- Add new AI modality: extend Provider Protocol and implement in adapters; expose new helper in `llm.py`.

### Data Model (Condensed)
- project_managers(id, name, role, dept, contact, experience, focus, active_project, project_summary, created_at)
- manager_required_skills(manager_id, skill)
- employees(id, name, title, experience, education, location, summary, created_at)
- employee_skills(employee_id, skill)
- employee_metrics(employee_id, velocity, quality_score, projects_delivered, skill_alignment_score)

### Non-Goals / Simplifications
- No authentication / authorization (demo scope).
- No background task queue – all calls synchronous except optional async LLM wrappers.
- No complex caching layer (provider responses not persisted beyond ad hoc artifacts).

### High-Level Diagram (Logical)
User -> FastAPI Routes -> (Business Logic + Normalization) -> DB Access Layer <-> SQLite
											  \
												-> LLM Abstraction -> Provider Adapter -> External API

---
Keep this file concise; expand in ADRs or PRD for deeper rationale.
