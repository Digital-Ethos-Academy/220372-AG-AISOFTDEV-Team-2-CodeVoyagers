import sys
import os
import json
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add the project's root directory to the Python path to ensure 'utils' can be imported.
try:
    project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))
except Exception:
    project_root = os.path.abspath(os.path.join(os.getcwd()))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import setup_llm_client, get_completion, save_artifact


app = FastAPI(title="AI Utils Demo")

# Serve templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), 'templates'))


@app.on_event("startup")
def startup_event():
    # Try to initialize an LLM client but don't fail startup if it can't be created
    global client, model_name, api_provider
    try:
        client, model_name, api_provider = setup_llm_client(model_name="gemini-2.5-flash")
    except Exception:
        client, model_name, api_provider = None, None, None


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/api/status')
def status():
    return JSONResponse({'status': 'ready' if client else 'no-client', 'model': model_name, 'provider': api_provider})


@app.post('/api/completion')
def completion():
    if client is None:
        raise HTTPException(status_code=503, detail='LLM client not initialized')
    try:
        prompt = "Hello! Can you explain what you are in one sentence?"
        result = get_completion(prompt, client, model_name, api_provider)
        # Save artifact (non-blocking for the demo)
        try:
            save_artifact(content=result, artifact_type='txt', name='ui_test_response', description='Response from UI test')
        except Exception:
            pass
        return JSONResponse({'output': result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('src.main:app', host='127.0.0.1', port=8000, reload=True)