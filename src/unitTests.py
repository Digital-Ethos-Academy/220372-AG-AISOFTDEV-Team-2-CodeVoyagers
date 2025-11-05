import json
import os
from src import main

def _json_from_response(resp):
    return json.loads(resp.body)

# Matching payload to recommened models 
def test_get_models_returns_recommended_models():
    resp = main.get_models()
    data = _json_from_response(resp)
    assert 'models' in data
    assert isinstance(data['models'], dict)
    assert data['models'] == main.RECOMMENDED_MODELS

# Global client is None (default)
def test_status_when_no_client():
    main.client = None
    resp = main.status()
    data = _json_from_response(resp)
    assert data['status'] == 'no-client'
    assert data['model'] is None
    assert data['provider'] is None


def test_get_available_providers_with_and_without_env(monkeypatch):
    for k in ('OPENAI_API_KEY', 'GOOGLE_API_KEY', 'ANTHROPIC_API_KEY', 'HUGGINGFACE_API_KEY'):
        monkeypatch.delenv(k, raising=False)
    providers = main.get_available_providers()
    assert providers == []
    monkeypatch.setenv('OPENAI_API_KEY', 'testkey')
    providers = main.get_available_providers()
    assert 'openai' in providers

# Using OPENAI
def test_get_providers_returns_display_names(monkeypatch):
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    monkeypatch.delenv('HUGGINGFACE_API_KEY', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'x')

    resp = main.get_providers()
    data = _json_from_response(resp)
    assert 'providers' in data
    assert 'OpenAI' in data['providers']

# Passing a new model that is not in recommended models
def test_test_model_with_unknown_model():
    req = main.ModelTestRequest(model='nonexistent-model-xyz')
    resp = main.test_model(req)
    data = _json_from_response(resp)
    assert 'output' in data
    assert 'not found' in data['output'] or 'Model' in data['output']
