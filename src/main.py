import sys
import os
import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add the project's root directory to the Python path to ensure 'utils' can be imported.
try:
    # Get the directory containing this script (src/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory (project root)
    project_root = os.path.dirname(script_dir)
except Exception:
    project_root = os.path.abspath(os.path.join(os.getcwd()))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import setup_llm_client, get_completion, save_artifact, load_environment, RECOMMENDED_MODELS
from utils.database import init_db, fetch_project_managers, fetch_employees, fetch_project_manager, fetch_employee, insert_project_manager, insert_employee
import threading

CONVERSATION_FILE = os.path.join(project_root, 'artifacts', 'conversations.json')
_conv_lock = threading.Lock()

def _load_conversations():
    if not os.path.exists(CONVERSATION_FILE):
        os.makedirs(os.path.dirname(CONVERSATION_FILE), exist_ok=True)
        with open(CONVERSATION_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    with open(CONVERSATION_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _save_conversations(data: dict):
    with _conv_lock:
        with open(CONVERSATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# Global variables for LLM client
client = None
model_name = None
api_provider = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global client, model_name, api_provider
    try:
        # Initialize database (idempotent)
        init_db(force=False)
        # Try to use gemini-2.5-pro if available, otherwise use the first available model
        if "gemini-2.5-pro" in RECOMMENDED_MODELS:
            default_model = "gemini-2.5-pro"
        else:
            default_model = list(RECOMMENDED_MODELS.keys())[0]  # First model as fallback
        
        client, model_name, api_provider = setup_llm_client(model_name=default_model)
    except Exception:
        client, model_name, api_provider = None, None, None
    
    yield
    
    # Shutdown (nothing to cleanup for now)


app = FastAPI(title="AI Utils Demo", lifespan=lifespan)

# Serve templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), 'templates'))


class ModelTestRequest(BaseModel):
    model: str


class SetDefaultModelRequest(BaseModel):
    model: str


def get_available_providers():
    """Get available providers based on configured API keys."""
    load_environment()
    available_providers = []
    
    if os.getenv('OPENAI_API_KEY'):
        available_providers.append('openai')
    if os.getenv('GOOGLE_API_KEY'):
        available_providers.append('google')
    if os.getenv('ANTHROPIC_API_KEY'):
        available_providers.append('anthropic')
    if os.getenv('HUGGINGFACE_API_KEY'):
        available_providers.append('huggingface')
    
    return available_providers


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request, 'active_page': 'index'})

@app.get("/models", response_class=HTMLResponse)
def models(request: Request):
    return templates.TemplateResponse('models.html', {'request': request, 'active_page': 'models'})

@app.get('/api/status')
def status():
    if client is None:
        return JSONResponse({
            'status': 'no-client', 
            'model': None, 
            'provider': None,
            'message': 'LLM client not initialized. Check API keys in .env file.'
        })
    else:
        return JSONResponse({
            'status': 'ready', 
            'model': model_name, 
            'provider': api_provider,
            'message': f'✅ Ready to use {model_name} via {api_provider}'
        })

@app.get('/api/models')
def get_models():
    """Return all configured models."""
    return JSONResponse({'models': RECOMMENDED_MODELS})

@app.post('/api/reset-database')
def reset_database():
    """Force reset the database to ensure proper schema and seed data."""
    try:
        init_db(force=True)
        return JSONResponse({'success': True, 'message': 'Database reset successfully with updated project manager data'})
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'Error resetting database: {str(e)}'}, status_code=500)

@app.get('/api/project-managers')
def get_project_managers():
    try:
        data = fetch_project_managers()
        return JSONResponse({'project_managers': data})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/project-managers/{mid}')
def get_project_manager_by_id(mid: int):
    pm = fetch_project_manager(mid)
    if pm:
        return JSONResponse({'project_manager': pm})
    return JSONResponse({'error': 'Project Manager not found'}, status_code=404)

@app.post('/api/project-managers')
async def create_project_manager(request: Request):
    """Create a project manager including optional project context fields."""
    try:
        payload = await request.json()
        # Normalize required_skills if provided as comma-separated string
        if isinstance(payload.get('required_skills'), str):
            payload['required_skills'] = [s.strip() for s in payload['required_skills'].split(',') if s.strip()]
        pm = insert_project_manager(payload)
        return JSONResponse({'project_manager': pm})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)

@app.get('/api/employees')
def get_employees():
    try:
        data = fetch_employees()
        return JSONResponse({'employees': data})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/employees/{eid}')
def get_employee_by_id(eid: int):
    emp = fetch_employee(eid)
    if emp:
        return JSONResponse({'employee': emp})
    return JSONResponse({'error': 'Employee not found'}, status_code=404)

@app.post('/api/employees')
async def create_employee(request: Request):
    try:
        payload = await request.json()
        if isinstance(payload.get('skills'), str):
            payload['skills'] = [s.strip() for s in payload['skills'].split(',') if s.strip()]
        # Normalize experience field name from form ('experience') to 'experience_years'
        if 'experience_years' not in payload and 'experience' in payload:
            try:
                payload['experience_years'] = int(payload.get('experience') or 0)
            except Exception:
                payload['experience_years'] = 0
        if payload.get('experience_years') is None:
            payload['experience_years'] = 0
        # Parse performance metrics from form inputs if provided
        metrics = payload.get('metrics') or {}
        # Allow flat numeric fields to be merged into metrics
        field_map = {
            'projects_delivered': 'Projects Delivered',
            'quality_score': 'Quality Score',
            'velocity': 'Velocity',
            'alignment_score': 'Skill Alignment Score'
        }
        for flat_key, metric_key in field_map.items():
            if flat_key in payload and payload[flat_key] is not None and payload[flat_key] != '':
                try:
                    metrics[metric_key] = int(payload[flat_key])
                except Exception:
                    pass
        # Coerce string metrics to int when possible
        for k,v in list(metrics.items()):
            if isinstance(v, str):
                try:
                    metrics[k] = int(''.join([c for c in v if c.isdigit()]))
                except Exception:
                    pass
        payload['metrics'] = metrics
        emp = insert_employee(payload)
        return JSONResponse({'employee': emp})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)

def _llm_generate_json(prompt: str, schema_description: str) -> Optional[dict]:
    """Helper to call LLM to get structured JSON-like data. Falls back to None on failure."""
    if client is None:
        print(f"DEBUG: LLM client is None, using fallback response")
        return None
    
    full_prompt = f"You are a data generator. {schema_description}\nPrompt: {prompt}\nReturn ONLY minified JSON.".strip()
    try:
        print(f"DEBUG: Calling LLM with model {model_name}, provider {api_provider}")
        raw = get_completion(full_prompt, client, model_name, api_provider)
        print(f"DEBUG: LLM raw response: {raw[:200]}...")
        
        # Attempt to locate JSON substring
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1 and end > start:
            import json as _json
            snippet = raw[start:end+1]
            result = _json.loads(snippet)
            print(f"DEBUG: Successfully parsed JSON: {type(result)}")
            return result
        else:
            print(f"DEBUG: No valid JSON found in response")
    except Exception as e:
        print(f"DEBUG: LLM call failed: {e}")
    return None

def _llm_generate_discussion_messages(pm: dict, emp: dict, pending_comment: Optional[str], history: list) -> Optional[list]:
    """Use LLM to generate continuation messages (PM + HR). Returns list of {role,speaker,text} or None."""
    if client is None:
        return None
    # Trim history to last 8 messages for brevity
    recent = history[-8:] if history else []
    history_str = '\n'.join([f"{m.get('speaker','Unknown')}: {m.get('text','')[:220]}" for m in recent])
    required = pm.get('required_skills', []) or []
    overlap_info = _skill_overlap(required, emp.get('skills', []) if emp else []) if required else {'overlap': [], 'gaps': []}
    schema_desc = "Return JSON array of exactly 2 objects: [{role:'manager'|'hr', speaker:string, text:string}]" 
    prompt = (
        f"You are facilitating a performance/project discussion.\n"
        f"Project: {pm.get('active_project')}\nProject Summary: {pm.get('project_summary')}\n"
        f"Required Skills: {', '.join(required)}\nEmployee: {emp.get('name')} ({emp.get('title')})\n"
        f"Employee Summary: {emp.get('summary')}\nSkills: {', '.join(emp.get('skills', []))}\n"
        f"Overlap: {', '.join(overlap_info['overlap']) or 'None'} | Gaps: {', '.join(overlap_info['gaps']) or 'None'}\n"
        f"Metrics: {json.dumps(emp.get('metrics', {}))}\n"
        f"History (most recent first):\n{history_str}\n"
        f"Team Lead Comment: {pending_comment or 'None'}\n"
        "Write two concise, distinct messages:\n"
        "1) Project Manager: address the comment if present, cite one metric and one gap or next step; be specific.\n"
        "2) HR Representative: contextualize development, recommend an actionable step (training, mentoring, exposure) and optionally morale/engagement angle.\n"
        "Avoid repeating earlier sentences verbatim. No prefacing like 'Answered:' unless necessary. Return only JSON."
    )
    result = _llm_generate_json(prompt, schema_desc)
    if isinstance(result, list):
        cleaned = []
        for msg in result[:2]:
            role = msg.get('role','manager').lower()
            role = 'manager' if role in ['manager','pm','project_manager'] else ('hr' if role in ['hr','human_resources','tech_lead','techlead','lead'] else 'manager')
            speaker = pm.get('name') if role=='manager' else 'HR Representative'
            text = (msg.get('text','') or '').strip()
            # Trim verbose overlap/alignment enumerations if answering a direct project question
            if pending_comment and _is_direct_project_question(pending_comment):
                # Keep only first sentence referencing project name or action
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                if sentences:
                    # Prefer sentence containing project name or 'project'
                    target = next((s for s in sentences if pm.get('active_project','').lower() in s.lower() or 'project' in s.lower()), sentences[0])
                    text = target[:220]
            text = text[:500]
            if text:
                cleaned.append({'role': role, 'speaker': speaker, 'text': text})
        if len(cleaned)==2:
            return cleaned
    return None

def _is_direct_project_question(comment: str) -> bool:
    c = comment.lower().strip()
    if not c:
        return False
    return c.startswith('what project') or 'currently leading' in c or ('leading' in c and 'project' in c)

@app.post('/api/generate/project-manager')
async def generate_project_manager(request: Request):
    """Generate project manager data optionally based on a user prompt."""
    data = await request.json() if request.headers.get('content-type','').startswith('application/json') else {}
    user_prompt = data.get('prompt', '').strip()
    base_prompt = user_prompt or "Generate a realistic senior software project manager profile overseeing engineering delivery."
    schema_desc = (
        "Return JSON with keys: name, role, department, email, experience_years (int), focus_area, "
        "active_project (short name), project_summary (one sentence), required_skills (list 4-8)."
    )
    result = _llm_generate_json(base_prompt, schema_desc)
    if result is None or not isinstance(result, dict):
        import random
        sample_names = ["Sarah Johnson", "Michael Chen", "Emma Rodriguez", "David Park", "Lisa Thompson"]
        sample_roles = ["Senior Project Manager", "Technical Project Manager", "Program Manager", "Delivery Lead", "Agile Coach"]
        sample_departments = ["Platform Engineering", "Data Science", "AI Initiatives", "Cloud Services", "Product Enablement"]
        projects = [
            ("Event Stream Platform", "Building low-latency ingestion & processing pipeline for analytics across 40 services.", ["React","Node.js","Kafka","Python","Kubernetes"]),
            ("Predictive Maintenance Suite", "Deploying anomaly detection models on manufacturing sensor data fleet-wide.", ["Python","Machine Learning","SQL","TensorFlow","API Design"]),
            ("Design Assistant", "Prototyping AI-driven UI design suggestion integration in internal workflow.", ["Figma","TypeScript","LLM Prompting","UX","Microservices"])
        ]
        name = random.choice(sample_names)
        role = random.choice(sample_roles)
        dept = random.choice(sample_departments)
        proj_name, proj_summary, req_skills = random.choice(projects)
        result = {
            'name': name,
            'role': role,
            'department': dept,
            'email': f"{name.lower().replace(' ', '.')}@example.com",
            'experience_years': random.randint(5,15),
            'focus_area': 'Delivery Optimization',
            'active_project': proj_name,
            'project_summary': proj_summary,
            'required_skills': req_skills
        }
    return JSONResponse({'project_manager': result})

@app.post('/api/generate/employee')
async def generate_employee(request: Request):
    """Generate employee data optionally based on a user prompt."""
    data = await request.json() if request.headers.get('content-type','').startswith('application/json') else {}
    user_prompt = data.get('prompt', '').strip()
    manager_id = data.get('manager_id')
    pm = fetch_project_manager(manager_id) if manager_id else None
    pm_context = ''
    if pm:
        pm_context = (
            f"Active Project: {pm.get('active_project')}\n"
            f"Project Summary: {pm.get('project_summary')}\n"
            f"Required Skills: {', '.join(pm.get('required_skills', []))}\n"
        )
    base_prompt = user_prompt or "Generate a realistic software engineer profile with current performance indicators and growth potential." 
    schema_desc = (
        "Return JSON with keys: name, title, experience_years (int), education, location, skills (list 5-8 mixing core & growth), metrics (object with exactly 4 numeric indicators: Velocity (int story points/sprint), Quality Score (int 0-100), Projects Delivered (int last 18 months), Skill Alignment Score (int 0-100 based on overlap with required skills if given)), summary (short paragraph referencing one metric)."
    )
    prompt = pm_context + base_prompt
    result = _llm_generate_json(prompt, schema_desc)
    if result is None:
        import random
        sample_names = ["Christopher Taylor", "Sarah Chang", "Marcus Johnson", "Elena Rodriguez", "David Kim"]
        sample_titles = ["Frontend Developer", "DevOps Engineer", "UX Designer", "Product Manager", "Software Architect"]
        sample_locations = ["Seattle, WA", "Austin, TX", "Denver, CO", "Portland, OR", "Chicago, IL"]
        sample_educations = ["BS Computer Science - UC Berkeley", "MS Software Engineering - Georgia Tech", "BS Information Systems - University of Texas", "MS Computer Science - Carnegie Mellon", "BS Engineering - Purdue University"]
        skill_sets = [
            ["React", "TypeScript", "Testing", "Accessibility"],
            ["Kubernetes", "Terraform", "Go", "Observability"],
            ["Figma", "Design Systems", "User Research", "Prototyping"],
            ["Roadmapping", "Agile", "Stakeholder Management", "Data Analysis"],
            ["Distributed Systems", "Architecture", "Python", "Microservices"]
        ]
        name = random.choice(sample_names)
        title = random.choice(sample_titles)
        location = random.choice(sample_locations)
        education = random.choice(sample_educations)
        skills = random.choice(skill_sets)
        experience_years = random.randint(1,12)
        velocity = random.randint(12,30)
        quality = random.randint(80,97)
        delivered = random.randint(5,40)
        if pm:
            required = set(pm.get('required_skills', []))
            overlap = len(required & set(skills))
            alignment = int((overlap / max(len(required),1)) * 100)
        else:
            alignment = random.randint(60,90)
        metrics = {"Projects Delivered": delivered, "Quality Score": quality, "Velocity": velocity, "Skill Alignment Score": alignment}
        summary = f"Consistent {title.lower()} with {experience_years} years experience; velocity {velocity} and quality {quality}/100. Overlap alignment {alignment}%. Strengths in {skills[0]} and {skills[1]}."
        result = {
            'name': name,
            'title': title,
            'experience_years': experience_years,
            'education': education,
            'location': location,
            'skills': skills,
            'metrics': metrics,
            'summary': summary
        }
    return JSONResponse({'employee': result})

def _conversation_key(manager_id: int, employee_id: int) -> str:
    return f"pm{manager_id}-emp{employee_id}"

def _skill_overlap(required: list, employee_skills: list) -> dict:
    required_set = set(required)
    emp_set = set(employee_skills)
    overlap = sorted(required_set & emp_set)
    gaps = sorted(required_set - emp_set)
    return { 'overlap': overlap, 'gaps': gaps }

def _compute_alignment(required: list, employee_skills: list) -> int:
    """Return alignment percentage (0-100) of required vs employee skills."""
    if not required:
        return 0
    required_set = set(required)
    overlap = len(required_set & set(employee_skills))
    return int((overlap / len(required_set)) * 100)

def _conversation_needs_reseed(manager: dict, employee: dict, messages: list) -> bool:
    """Diagnose whether an existing conversation appears to belong to a different employee
    or uses legacy roles (e.g., Tech Lead) and should be reseeded. This is diagnostic only
    for now (reseed occurs in a later step)."""
    if not manager or not employee or not messages:
        return False
    first = messages[0]
    expected_name = employee.get('name')
    if not expected_name:
        return False
    text = first.get('text', '')
    # Intro line should contain 'Reviewing <Employee Name>'
    if f"Reviewing {expected_name}" not in text:
        return True
    # Any legacy Tech Lead role/speaker indicates stale seed
    for m in messages:
        speaker = (m.get('speaker') or '').lower()
        if speaker.startswith('tech lead') or m.get('role') in ('lead', 'techlead'):
            return True
    return False

def _migrate_legacy_roles(messages: list) -> None:
    """In-place migrate any legacy Tech Lead messages to HR role for consistency."""
    if not messages:
        return
    for m in messages:
        speaker = (m.get('speaker') or '').lower()
        if speaker.startswith('tech lead') or m.get('role') in ('lead', 'techlead'):
            m['role'] = 'hr'
            m['speaker'] = 'HR Representative'

def _extract_employee_facts(employee: dict) -> dict:
    """Parse structured facts from employee summary for enhanced fallback replies.
    Currently extracts number of hobbies if phrased like 'exactly 13 hobbies' or '13 hobbies'."""
    summary = employee.get('summary', '') or ''
    hobbies_count = None
    import re
    text = summary.lower()
    # Support multiple phrasings: 'exactly 13 hobbies', '13 hobbies', 'has 13 hobbies', '13 personal interests', '13 different hobbies'
    match = re.search(r'(?:exactly\s+|has\s+|with\s+)?(\d{1,2})\s+(?:different\s+)?(?:hobbies|personal interests|activities)', text)
    if match:
        try:
            hobbies_count = int(match.group(1))
        except ValueError:
            pass
    return {'hobbies_count': hobbies_count}

def _variant(options: list, seed: str = "") -> str:
    """Return a deterministic variant based on a seed to avoid repeated identical phrasing."""
    if not options:
        return ''
    import hashlib
    h = hashlib.sha256(seed.encode('utf-8')).hexdigest()
    idx = int(h[:4], 16) % len(options)
    return options[idx]

def _seed_conversation(manager: dict, employee: dict):
    manager_name = manager['name']
    required = manager.get('required_skills', [])
    overlap_info = _skill_overlap(required, employee.get('skills', [])) if required else {'overlap': [], 'gaps': []}
    # Safely extract first metric without raising StopIteration on empty dicts
    metrics = employee.get('metrics') or {}
    if isinstance(metrics, dict) and metrics:
        first_metric_key, first_metric_val = next(iter(metrics.items()))
    else:
        first_metric_key, first_metric_val = 'Metric', 'N/A'
    
    # Ensure experience_years is not None for display
    experience_years = employee.get('experience_years')
    if experience_years is None:
        experience_years = 0
    
    overlap_txt = (f"Overlap: {', '.join(overlap_info['overlap'])}. Gaps: {', '.join(overlap_info['gaps']) or 'None'}" if required else "No explicit required skills listed yet.")
    intro = f"Reviewing {employee['name']} for project '{manager.get('active_project','(no project)')}': {experience_years} yrs experience; {first_metric_key}={first_metric_val}."
    alignment_pct = _compute_alignment(required, employee.get('skills', [])) if required else 0
    project_eval = f"Project needs: {', '.join(required[:4]) if required else 'TBD'}. Alignment {alignment_pct}%. {overlap_txt}"
    hr_view = f"HR perspective: {employee['name']} shows strong background in {employee.get('education', 'relevant field').split(' - ')[0]}; summary: {employee.get('summary','')[:70]}..."
    next_step = f"Considering task alignment leveraging {employee.get('education', 'their background').split(' - ')[0]} and strengths in {', '.join(employee.get('skills', [])[:2])}."
    return [
        { 'role': 'manager', 'speaker': manager_name, 'text': intro },
        { 'role': 'manager', 'speaker': manager_name, 'text': project_eval },
        { 'role': 'hr', 'speaker': 'HR Representative', 'text': hr_view },
        { 'role': 'manager', 'speaker': manager_name, 'text': next_step }
    ]

@app.get('/api/conversation')
def get_conversation(manager_id: int, employee_id: int):
    convs = _load_conversations()
    key = _conversation_key(manager_id, employee_id)
    if key not in convs:
        manager = fetch_project_manager(manager_id)
        employee = fetch_employee(employee_id)
        if not manager or not employee:
            return JSONResponse({'error': 'Invalid manager or employee id'}, status_code=400)
        try:
            convs[key] = _seed_conversation(manager, employee)
        except Exception as e:
            # Gracefully degrade with minimal seed if unexpected data shape
            convs[key] = [{
                'role': 'manager',
                'speaker': manager.get('name','Manager'),
                'text': f"Conversation seed unavailable due to data error: {type(e).__name__}."
            }]
        _save_conversations(convs)
    else:
        # Diagnostic: detect mismatch and log (auto reseed added in subsequent step)
        manager = fetch_project_manager(manager_id)
        employee = fetch_employee(employee_id)
        try:
            if _conversation_needs_reseed(manager, employee, convs.get(key, [])):
                print(f"DEBUG: Conversation mismatch detected for {key}; intro='{convs[key][0].get('text','')[:80]}', expected employee='{employee.get('name','?')}'.")
        except Exception as diag_err:
            print(f"DEBUG: Conversation mismatch diagnostic failed for {key}: {diag_err}")
    return JSONResponse({'conversation': convs[key]})

@app.post('/api/conversation/continue')
async def continue_conversation(request: Request):
    payload = await request.json()
    manager_id = payload.get('manager_id')
    employee_id = payload.get('employee_id')
    if manager_id is None or employee_id is None:
        return JSONResponse({'error': 'manager_id and employee_id required'}, status_code=400)
    convs = _load_conversations()
    key = _conversation_key(manager_id, employee_id)
    if key not in convs:
        pm = fetch_project_manager(manager_id)
        emp = fetch_employee(employee_id)
        if not pm or not emp:
            return JSONResponse({'error': 'Invalid manager or employee id'}, status_code=400)
        try:
            convs[key] = _seed_conversation(pm, emp)
        except Exception as e:
            convs[key] = [{
                'role': 'manager',
                'speaker': pm.get('name','Manager'),
                'text': f"Conversation seed unavailable due to data error: {type(e).__name__}."
            }]
    else:
        # Auto reseed if mismatch detected
        pm = fetch_project_manager(manager_id)
        emp = fetch_employee(employee_id)
        try:
            msgs = convs.get(key, [])
            _migrate_legacy_roles(msgs)
            if _conversation_needs_reseed(pm, emp, msgs):
                print(f"DEBUG: Auto reseed in continue_conversation for {key}")
                convs[key] = _seed_conversation(pm, emp)
        except Exception as rs_err:
            print(f"DEBUG: Reseed failure in continue_conversation for {key}: {rs_err}")
    # Determine if last message was a teamlead comment requiring answer
    pending_comment = None
    if convs[key] and convs[key][-1]['role'] == 'teamlead':
        pending_comment = convs[key][-1]['text']

    pm = fetch_project_manager(manager_id)
    emp = fetch_employee(employee_id)
    required = pm.get('required_skills', [])
    overlap_info = _skill_overlap(required, emp.get('skills', [])) if required else {'overlap': [], 'gaps': []}
    alignment_pct = _compute_alignment(required, emp.get('skills', [])) if required else 0

    # Craft prompt for LLM with context
    extension_prompt = (
        f"Project: {pm.get('active_project')}\nSummary: {pm.get('project_summary')}\n" 
        f"Required Skills: {', '.join(required)}\nEmployee Skills: {', '.join(emp.get('skills', []))}\n"
        f"Overlap: {', '.join(overlap_info['overlap']) or 'None'} | Gaps: {', '.join(overlap_info['gaps']) or 'None'}\n"
        f"Latest Metrics: {json.dumps(emp.get('metrics', {}))}\n"
        f"Team Lead Question/Comment: {pending_comment or 'None'}\n"
        "Write 2 short messages: first from project manager giving project-fit assessment (reference one metric & one gap if any; if answering a question, answer it explicitly). "
        "Second from HR representative giving actionable recommendation (address the question if present, otherwise suggest onboarding / training for skill gaps). Return JSON array of {role,speaker,text}."
    )
    
    # Prefer full LLM contextual generation when available
    llm_messages = _llm_generate_discussion_messages(pm, emp, pending_comment, convs[key]) if client else None
    if llm_messages:
        convs[key].extend(llm_messages)
    else:
        # Minimal fallback
        if pending_comment:
            if _is_direct_project_question(pending_comment):
                manager_response = f"Leading project: {pm.get('active_project','(unknown)')} – focusing delivery milestones."[:300]
                hr_response = f"HR: Confirmed {emp.get('name','Employee')} supports {pm.get('active_project','project')} with retention & development focus."[:300]
            else:
                manager_response = f"{emp['name']} alignment {alignment_pct}%. Overlap: {', '.join(overlap_info['overlap']) or 'None'}; gaps: {', '.join(overlap_info['gaps'][:2]) or 'None'}. Comment: '{pending_comment[:60]}...'"
                hr_response = _enhanced_answer_teamlead(pending_comment, emp, pm, overlap_info)
            convs[key].append({'role':'manager','speaker':pm['name'],'text':manager_response})
            convs[key].append({'role':'hr','speaker':'HR Representative','text':hr_response})
        else:
            convs[key].append({'role':'manager','speaker':pm['name'],'text':f"Next assessment: alignment {alignment_pct}%. Leverage {', '.join(overlap_info['overlap'][:2]) or 'existing strengths'}; address {', '.join(overlap_info['gaps'][:1]) or 'no major gaps'}."})
            convs[key].append({'role':'hr','speaker':'HR Representative','text':"HR view: maintain engagement and start targeted training for remaining gap areas."})
    _save_conversations(convs)
    return JSONResponse({'conversation': convs[key]})

def _enhanced_answer_teamlead(comment: str, employee: dict, manager: dict, overlap_info: dict) -> str:
    """Simplified fallback responder used ONLY when LLM unavailable."""
    text = comment.lower()
    name = employee.get('name','Employee').split()[0]
    project = manager.get('active_project','the project')
    gaps = overlap_info.get('gaps', [])
    overlaps = overlap_info.get('overlap', [])
    facts = _extract_employee_facts(employee)
    if 'hobbies' in text and facts.get('hobbies_count'):
        return f"Hobby context: {name} has {facts['hobbies_count']} hobbies; maintaining balance while addressing {', '.join(gaps[:1]) or 'no immediate gaps'}."
    return f"Fallback: {name} overlap {', '.join(overlaps[:2]) or 'None'}; gaps {', '.join(gaps[:2]) or 'None'} for {project}."

def _auto_answer_teamlead(comment: str, employee: dict) -> str:
    """Heuristic responder for team lead comments when LLM unavailable.
    Looks for simple question patterns and answers based on employee profile.
    """
    text = comment.lower()
    name = employee.get('name','The employee')
    # Hiking question example
    if 'hike' in text or 'hiking' in text:
        return f"Answered: Yes, {name.split()[0]} enjoys hiking outside of work; it supports resilience and focus at work." if 'yes' not in text else f"Answered: {name.split()[0]}'s hiking interest acknowledged; we can leverage that for wellness initiatives." 
    if 'skill' in text and 'gap' in text:
        gaps = []
        # Derive gaps relative to required_skills if available via a manager context (not passed here); fallback to none
        return f"Answered: Key growth focus will be on closing identified skill gaps through pairing and targeted tasks." 
    if 'velocity' in text or 'speed' in text:
        return f"Answered: Current velocity metrics look stable; we'll monitor as responsibilities expand." 
    if text.endswith('?'):
        return f"Answered: We'll gather data to respond fully; currently no blocker related to '{comment.strip('?')}'."
    return "Answered: Comment acknowledged; integrating into evaluation for next update." 

@app.post('/api/conversation/new')
async def new_conversation(request: Request):
    """Start a fresh conversation between manager and employee, clearing any existing discussion."""
    payload = await request.json()
    manager_id = payload.get('manager_id')
    employee_id = payload.get('employee_id')
    if manager_id is None or employee_id is None:
        return JSONResponse({'error': 'manager_id and employee_id required'}, status_code=400)
    
    manager = fetch_project_manager(manager_id)
    employee = fetch_employee(employee_id)
    if not manager or not employee:
        return JSONResponse({'error': 'Invalid manager or employee id'}, status_code=400)
    
    convs = _load_conversations()
    key = _conversation_key(manager_id, employee_id)
    
    # Force re-seed conversation from scratch
    try:
        convs[key] = _seed_conversation(manager, employee)
    except Exception as e:
        convs[key] = [{
            'role': 'manager',
            'speaker': manager.get('name','Manager'),
            'text': f"Conversation seed unavailable due to data error: {type(e).__name__}."
        }]
    
    _save_conversations(convs)
    return JSONResponse({'conversation': convs[key]})

@app.post('/api/conversation/comment')
async def add_comment(request: Request):
    payload = await request.json()
    manager_id = payload.get('manager_id')
    employee_id = payload.get('employee_id')
    comment = payload.get('text', '').strip()
    if manager_id is None or employee_id is None:
        return JSONResponse({'error': 'manager_id and employee_id required'}, status_code=400)
    if not comment:
        return JSONResponse({'error': 'text required'}, status_code=400)
    convs = _load_conversations()
    key = _conversation_key(manager_id, employee_id)
    if key not in convs:
        # Attempt lazy seed instead of 404 for better UX
        manager = fetch_project_manager(manager_id)
        employee = fetch_employee(employee_id)
        if manager and employee:
            try:
                convs[key] = _seed_conversation(manager, employee)
            except Exception:
                convs[key] = [{
                    'role': 'manager',
                    'speaker': manager.get('name','Manager'),
                    'text': 'Conversation seed unavailable due to data error.'
                }]
        else:
            return JSONResponse({'error': 'Conversation not found and unable to seed (invalid ids).'}, status_code=404)
    convs[key].append({'role': 'teamlead', 'speaker': 'Team Lead', 'text': comment[:500]})
    _save_conversations(convs)
    return JSONResponse({'conversation': convs[key]})


@app.get('/api/all-models')
def get_all_models():
    """Return all configured models, regardless of API key availability."""
    return JSONResponse({'models': RECOMMENDED_MODELS})

@app.get('/api/providers')
def get_providers():
    """Return available providers based on configured API keys."""
    available_providers = get_available_providers()
    
    # Convert to display names (only for implemented providers)
    display_names = {
        'openai': 'OpenAI',
        'google': 'Google',
        'anthropic': 'Anthropic',
        'huggingface': 'HuggingFace',
    }
    
    provider_names = [display_names.get(p, p.title()) for p in available_providers]
    return JSONResponse({'providers': provider_names})

@app.post('/api/test-model')
def test_model(request_data: ModelTestRequest):
    """Test a specific model with a sample prompt."""
    model_name = request_data.model
    if not model_name:
        return JSONResponse({'output': '❌ No model specified'})
    
    if model_name not in RECOMMENDED_MODELS:
        return JSONResponse({'output': f'❌ Model "{model_name}" not found in available models'})
    
    # Check if API key is available for this model's provider
    model_config = RECOMMENDED_MODELS[model_name]
    provider = model_config.get('provider', '').lower()
    available_providers = get_available_providers()
    
    if provider not in available_providers:
        provider_key_map = {
            'openai': 'OPENAI_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'huggingface': 'HUGGINGFACE_API_KEY',
            # Note: groq, deepseek, meta providers are referenced but not implemented
            # 'groq': 'GROQ_API_KEY',
            # 'deepseek': 'DEEPSEEK_API_KEY',
            # 'meta': 'META_API_KEY'
        }
        required_key = provider_key_map.get(provider, f'{provider.upper()}_API_KEY')
        return JSONResponse({'output': f'❌ API key not configured for {provider}\n\nRequired environment variable: {required_key}\n\nPlease add this to your .env file:\n{required_key}=your_api_key_here'})
    
    try:
        # Initialize client for the specific model
        test_client, test_model, test_provider = setup_llm_client(model_name=model_name)
        
        if test_client is None:
            return JSONResponse({'output': f'❌ Failed to initialize client for {model_name}.\n\nPossible reasons:\n- Invalid API key for {provider}\n- Invalid model configuration\n- Network issues'})
        
        # Test the model with a sample prompt
        prompt = f"Hello! Please introduce yourself and confirm that you are the {model_name} model. Keep it brief."
        result = get_completion(prompt, test_client, test_model, test_provider)
        
        # Format the output
        config = RECOMMENDED_MODELS[model_name]
        output = f"✅ Model Test Successful!\n\n"
        output += f"Model: {test_model}\n"
        output += f"Provider: {test_provider}\n"
        output += f"Context Window: {config.get('context_window_tokens', 'Not specified'):,}\n" if config.get('context_window_tokens') else f"Context Window: Not specified\n"
        output += f"Max Output Tokens: {config.get('output_tokens', 'Not specified'):,}\n" if config.get('output_tokens') else f"Max Output Tokens: Not specified\n"
        output += f"Supports Vision: {'Yes' if config.get('vision') else 'No'}\n"
        output += f"Supports Text Generation: {'Yes' if config.get('text_generation') else 'No'}\n"
        output += f"Supports Image Generation: {'Yes' if config.get('image_generation') else 'No'}\n"
        output += f"Supports Image Editing: {'Yes' if config.get('image_modification') else 'No'}\n"
        output += f"Supports Audio Transcription: {'Yes' if config.get('audio_transcription') else 'No'}\n\n"
        output += f"Model Response:\n{result}\n\n"
        output += f"🎉 The {model_name} model is working properly!"
        
        # Save artifact
        try:
            save_artifact(content=output, artifact_type='txt', name=f'model_test_{model_name.replace("-", "_")}', description=f'Test response from {model_name}')
        except Exception:
            pass
            
        return JSONResponse({'output': output})
        
    except Exception as e:
        error_msg = f"❌ Error testing {model_name}:\n\n{str(e)}\n\nThis might be due to:\n- Invalid API key for {provider}\n- Network issues\n- Model temporarily unavailable\n- Rate limiting"
        return JSONResponse({'output': error_msg})

@app.post('/api/set-default-model')
def set_default_model(request_data: SetDefaultModelRequest):
    """Set a new default model for the main app."""
    global client, model_name, api_provider
    
    new_model = request_data.model
    if not new_model:
        return JSONResponse({'success': False, 'message': '❌ No model specified'})
    
    if new_model not in RECOMMENDED_MODELS:
        return JSONResponse({'success': False, 'message': f'❌ Model "{new_model}" not found in available models'})
    
    # Check if API key is available for this model's provider
    model_config = RECOMMENDED_MODELS[new_model]
    provider = model_config.get('provider', '').lower()
    available_providers = get_available_providers()
    
    if provider not in available_providers:
        provider_key_map = {
            'openai': 'OPENAI_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'huggingface': 'HUGGINGFACE_API_KEY',
            # Note: groq, deepseek, meta providers are referenced but not implemented
            # 'groq': 'GROQ_API_KEY',
            # 'deepseek': 'DEEPSEEK_API_KEY',
            # 'meta': 'META_API_KEY'
        }
        required_key = provider_key_map.get(provider, f'{provider.upper()}_API_KEY')
        return JSONResponse({'success': False, 'message': f'❌ API key not configured for {provider}\n\nRequired: {required_key}'})
    
    try:
        # Initialize client for the new default model
        new_client, new_model_name, new_provider = setup_llm_client(model_name=new_model)
        
        if new_client is None:
            return JSONResponse({'success': False, 'message': f'❌ Failed to initialize client for {new_model}'})
        
        # Update global variables
        client = new_client
        model_name = new_model_name
        api_provider = new_provider
        
        return JSONResponse({
            'success': True, 
            'message': f'✅ Default model changed to {new_model_name}',
            'model': new_model_name,
            'provider': new_provider
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'message': f'❌ Error setting default model: {str(e)}'})

@app.post('/api/completion')
def completion():
    if client is None:
        return JSONResponse({'output': 'LLM client not initialized. Please configure API keys in .env file.\n\nExample:\nGOOGLE_API_KEY=your_key_here\nOPENAI_API_KEY=your_key_here'})
    try:
        # Define a common prompt to test actual API connection
        prompt = "Write a haiku about artificial intelligence."
        
        # Make real API call
        result = get_completion(prompt, client, model_name, api_provider)
        
        # Add connection info
        output = f"✅ API Connection Successful!\n\n"
        output += f"Model: {model_name}\n"
        output += f"Provider: {api_provider}\n\n"
        output += f"Prompt: '{prompt}'\n\n"
        output += f"Response:\n{result}\n\n"
        output += f"🎉 Real API response received! This confirms the LLM integration is working properly."
        
        # Save artifact (non-blocking for the demo)
        try:
            save_artifact(content=output, artifact_type='txt', name='ui_test_response', description='Response from UI test')
        except Exception:
            pass
        return JSONResponse({'output': output})
    except Exception as e:
        error_msg = f"❌ Error testing LLM:\n\n{str(e)}\n\nThis might be due to:\n- Invalid API key\n- Network issues\n- Model not available\n- Rate limiting\n\nPlease check your .env configuration and try again."
        return JSONResponse({'output': error_msg})


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('src.main:app', host='127.0.0.1', port=8000, reload=True)