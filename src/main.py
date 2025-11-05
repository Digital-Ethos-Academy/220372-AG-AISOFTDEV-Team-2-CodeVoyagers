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
    # Note: groq, deepseek, meta providers are referenced in main.py but not implemented in utils/providers
    # Commenting out until those providers are added
    # if os.getenv('GROQ_API_KEY'):
    #     available_providers.append('groq')
    # if os.getenv('DEEPSEEK_API_KEY'):
    #     available_providers.append('deepseek')
    # if os.getenv('META_API_KEY'):
    #     available_providers.append('meta')
    
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
    try:
        payload = await request.json()
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
        emp = insert_employee(payload)
        return JSONResponse({'employee': emp})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)


def _llm_generate_json(prompt: str, schema_description: str) -> Optional[dict]:
    """Helper to call LLM to get structured JSON-like data. Falls back to None on failure."""
    if client is None:
        return None
    full_prompt = f"You are a data generator. {schema_description}\nPrompt: {prompt}\nReturn ONLY minified JSON.".strip()
    try:
        raw = get_completion(full_prompt, client, model_name, api_provider)
        # Attempt to locate JSON substring
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1 and end > start:
            import json as _json
            snippet = raw[start:end+1]
            return _json.loads(snippet)
    except Exception:
        return None
    return None


@app.post('/api/generate/project-manager')
async def generate_project_manager(request: Request):
    """Generate project manager data optionally based on a user prompt."""
    data = await request.json() if request.headers.get('content-type','').startswith('application/json') else {}
    user_prompt = data.get('prompt', '').strip()
    base_prompt = user_prompt or "Generate a realistic senior software project manager profile overseeing engineering delivery."
    schema_desc = "Return JSON with keys: name, role, department, email, experience_years (int), focus_area."
    result = _llm_generate_json(base_prompt, schema_desc)
    if result is None:
        import random
        sample_names = ["Sarah Johnson", "Michael Chen", "Emma Rodriguez", "David Park", "Lisa Thompson"]
        sample_roles = ["Senior Project Manager", "Technical Project Manager", "Program Manager", "Delivery Lead", "Agile Coach"]
        sample_departments = ["Platform Engineering", "Data Science", "AI Initiatives", "Cloud Services", "Product Enablement"]
        name = random.choice(sample_names)
        role = random.choice(sample_roles)
        dept = random.choice(sample_departments)
        result = {
            'name': name,
            'role': role,
            'department': dept,
            'email': f"{name.lower().replace(' ', '.')}@example.com",
            'experience_years': random.randint(5,15),
            'focus_area': 'Delivery Optimization'
        }
    return JSONResponse({'project_manager': result})


@app.post('/api/generate/employee')
async def generate_employee(request: Request):
    """Generate employee data optionally based on a user prompt."""
    data = await request.json() if request.headers.get('content-type','').startswith('application/json') else {}
    user_prompt = data.get('prompt', '').strip()
    base_prompt = user_prompt or "Generate a realistic software engineer employee profile with current performance indicators and growth potential." 
    schema_desc = "Return JSON with keys: name, title, experience_years (int), education, location, skills (list of 4-8), metrics (object with 3-5 performance indicators like Velocity, Quality Score, Projects Delivered), summary (short paragraph)."
    result = _llm_generate_json(base_prompt, schema_desc)
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
        metrics = {"Projects Delivered": str(random.randint(5,40)), "Quality Score": f"{random.randint(80,97)}/100", "Velocity": f"{random.randint(12,30)} story points/sprint"}
        summary = f"Consistent {title.lower()} with {experience_years} years of experience delivering impactful features. Strengths in {skills[0]} and {skills[1]} with growing leadership potential."
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

def _seed_conversation(manager: dict, employee: dict):
    manager_name = manager['name']
    return [
        { 'role': 'manager', 'speaker': manager_name, 'text': f"Reviewing {employee['name']}'s recent performance: {employee['experience_years']} years experience and strong delivery in {', '.join(employee['skills'][:2])}." },
        { 'role': 'manager', 'speaker': manager_name, 'text': f"Key metric snapshot shows {next(iter(employee['metrics'].items()))[0]} at {next(iter(employee['metrics'].items()))[1]}. Assessing readiness for upcoming strategic initiative." },
        { 'role': 'lead', 'speaker': 'Tech Lead', 'text': f"{employee['name']} has been consistent. Their summary indicates reliability: {employee['summary'][:80]}..." },
        { 'role': 'manager', 'speaker': manager_name, 'text': f"Agreed. Considering assigning them to a high-impact task leveraging their background in {employee['education'].split(' - ')[0]}." }
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
        convs[key] = _seed_conversation(manager, employee)
        _save_conversations(convs)
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
        manager = fetch_project_manager(manager_id)
        employee = fetch_employee(employee_id)
        if not manager or not employee:
            return JSONResponse({'error': 'Invalid manager or employee id'}, status_code=400)
        convs[key] = _seed_conversation(manager, employee)
    extension_prompt = f"Add two concise evaluation lines where project manager {fetch_project_manager(manager_id)['name']} discusses employee {fetch_employee(employee_id)['name']}'s readiness for a strategic task. Return JSON list of message objects with role, speaker, text." 
    llm_lines = _llm_generate_json(extension_prompt, "Return an array of message objects: [{role: string, speaker: string, text: string}, ...]") if client else None
    if isinstance(llm_lines, list):
        convs[key].extend(llm_lines[:2])
    else:
        convs[key].append({'role': 'manager', 'speaker': fetch_project_manager(manager_id)['name'], 'text': 'Preparing growth plan and assigning them to a higher complexity feature set next sprint.'})
        convs[key].append({'role': 'lead', 'speaker': 'Tech Lead', 'text': 'Recommend pairing with a senior engineer for architectural mentoring.'})
    _save_conversations(convs)
    return JSONResponse({'conversation': convs[key]})

@app.post('/api/conversation/comment')
async def add_comment(request: Request):
    payload = await request.json()
    manager_id = payload.get('manager_id')
    employee_id = payload.get('employee_id')
    comment = payload.get('text', '').strip()
    if not comment:
        return JSONResponse({'error': 'text required'}, status_code=400)
    convs = _load_conversations()
    key = _conversation_key(manager_id, employee_id)
    if key not in convs:
        return JSONResponse({'error': 'Conversation not found'}, status_code=404)
    convs[key].append({'role': 'teamlead', 'speaker': 'Team Lead', 'text': comment})
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
        # Note: groq, deepseek, meta providers are referenced but not implemented
        # 'groq': 'Groq',
        # 'deepseek': 'DeepSeek',
        # 'meta': 'Meta'
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