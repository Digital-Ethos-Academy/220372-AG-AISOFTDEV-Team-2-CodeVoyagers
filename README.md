# Performance Evaluation Dashboard

## Overview
This project is a lightweight Performance Evaluation Dashboard that helps a Project Manager generate structured evaluation discussions for employees. It combines a FastAPI backend, a simple HTML frontend (Jinja2 templates), a SQLite database for persistence, and optional Large Language Model (LLM) providers (OpenAI, Anthropic, Google, Hugging Face) to assist with generating conversation prompts and discussion summaries.

## Core Goals
* Central place to manage employees and project managers
* View employee profiles and related discussion history
* Generate AI-assisted discussion points to aid performance reviews
* Customize basic dashboard layout and content
* Keep implementation small, transparent, and easy to extend

## Key Features
* Employee & Manager CRUD via REST endpoints
* Conversation engine that stores generated dialogue in JSON history
* Pluggable LLM provider abstraction (`utils/providers/*`) for future expansion
* Simple rate limiting & error handling helpers
* PlantUML architecture & use case artifacts for clarity

## High-Level Use Cases
```
Actors:
  [Project Manager]  [Employee]  [AI System]

 System Boundary: Performance Dashboard
  +---------------------------------------------------------------+
  | (Manage Dashboard)   (Add Employee)  (View Employee Profile) |
  | (Generate Discussion)              (Customize Layout)        |
  +---------------------------------------------------------------+

Relationships:
  Project Manager -> Manage Dashboard
  Project Manager -> Add Employee
  Project Manager -> View Employee Profile
  Project Manager -> Customize Layout
  Project Manager -> Generate Discussion <- AI System
  Employee -> View Employee Profile
```

## Component Architecture
```
		  +-------------------------+
		  |        User (PM/Emp)    |
		  +------------+------------+
				 |
				 v
			+---------------+
			|  Dashboard UI |  (HTML/Jinja)
			+-------+-------+
				 | contains
	 +--------------------+--------------------+
	 |                                         |
  +-----------+                          +----------------+
  | Modal     |                          | Profile Display|
  | Forms     |                          +----------------+
  +-----------+
				 |
				 v  HTTP (REST /api/*)
			  +---------------+
			  |  FastAPI App  |
			  +-------+-------+
				   | uses
		 +----------------+------------------+
		 |                                   |
	 +-------------+                     +--------------------+
	 | AI Generator|                     | Conversation Engine|
	 +------+------+                     +------+-------------+
		 | API calls                        | API calls
		 v                                   v
	 +------------------+               +------------------+
	 |   LLM Service    | (OpenAI/Anthropic/etc.)
	 +------------------+
		 ^                                   
		 |                                   
  +----------------------+          +--------------------------+
  |   SQLite Database    |          |      JSON Storage        |
  | (Employees/Managers) |          | (Conversation History)   |
  +----------------------+          +--------------------------+
		  ^                              ^
		  | Reads/Writes                 | Reads/Writes
		  +--------------+---------------+
				   |
			   FastAPI App (Data Layer interactions)
```

## Technology Stack
* Python 3 + FastAPI (`src/main.py`)
* SQLite (schema & seed in `artifacts/schema.sql`, `artifacts/seed_data.sql`)
* HTML/Jinja2 templates (`src/templates/`)
* LLM provider abstraction layer (`utils/providers/`)
* Supporting utilities: logging, rate limiting, error handling

## Directory Highlights
* `src/` – Application entrypoint and templates
* `utils/` – Helper modules, provider integrations, artifacts handling
* `artifacts/` – Architecture docs, UML diagrams, schema, PRD, ADRs
* `requirements.txt` – Python dependencies

## Quick Start (Local Development)
Prerequisite: Python 3.11+ recommended.

1. (Optional) Create and activate a virtual environment.
2. Install dependencies.
3. Run the development server.

```
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Then open: http://127.0.0.1:8000

## API Sketch
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/employees | GET/POST | List or create employees |
| /api/project-managers | GET/POST | Manage project managers |
| /api/conversation | POST | Generate or extend discussion |

## Extending
* Add new LLM providers by implementing `BaseProvider` in `utils/providers/base.py`.
* Modify data models and migrations via `schema.sql`.
* Introduce auth (e.g., JWT) by adding middleware in `src/main.py`.

## Vision
Start simple: accurate data capture + aided discussions. Grow toward richer performance metrics, sentiment analysis, and scheduled review workflows while keeping transparency and human oversight central.

## License
Add a LICENSE file (not yet included) if needed for distribution.

