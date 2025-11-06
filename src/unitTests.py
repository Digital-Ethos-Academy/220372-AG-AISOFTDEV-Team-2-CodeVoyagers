import json
import os
import main

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
    # Mock load_environment to do nothing (prevent reloading from .env)
    monkeypatch.setattr('main.load_environment', lambda: None)
    
    # Mock os.getenv to simulate empty environment
    def mock_getenv_empty(key, default=None):
        return default
    
    # Mock os.getenv to simulate only OPENAI_API_KEY
    def mock_getenv_openai_only(key, default=None):
        if key == 'OPENAI_API_KEY':
            return 'testkey'
        return default
    
    # Test with no API keys
    monkeypatch.setattr('os.getenv', mock_getenv_empty)
    providers = main.get_available_providers()
    assert providers == []
    
    # Test with only OPENAI_API_KEY
    monkeypatch.setattr('os.getenv', mock_getenv_openai_only)
    providers = main.get_available_providers()
    assert providers == ['openai']

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


# Conversation endpoint tests
def test_get_conversation_seeds_and_returns_list(tmp_path, monkeypatch):
    # Force conversations file to temp
    test_file = tmp_path / 'conversations.json'
    monkeypatch.setattr(main, 'CONVERSATION_FILE', str(test_file))
    # Disable external client usage
    monkeypatch.setattr(main, 'client', None)
    # Provide minimal fetch functions
    monkeypatch.setattr(main, 'fetch_project_manager', lambda mid: {'name': 'PM Test', 'required_skills': ['Python'], 'active_project': 'Alpha', 'project_summary': 'Alpha project desc'} if mid == 1 else None)
    monkeypatch.setattr(main, 'fetch_employee', lambda eid: {'name': 'Emp Test', 'experience_years': 3, 'education': 'BS Computer Science - Uni', 'skills': ['Python'], 'metrics': {'Velocity':'20'}, 'summary':'Solid contributor'} if eid == 2 else None)
    resp = main.get_conversation(manager_id=1, employee_id=2)
    data = _json_from_response(resp)
    assert 'conversation' in data
    assert isinstance(data['conversation'], list)
    assert len(data['conversation']) >= 1

def test_comment_on_conversation_creates_if_missing(tmp_path, monkeypatch):
    test_file = tmp_path / 'conversations.json'
    monkeypatch.setattr(main, 'CONVERSATION_FILE', str(test_file))
    monkeypatch.setattr(main, 'client', None)
    monkeypatch.setattr(main, 'fetch_project_manager', lambda mid: {'name': 'PM Test', 'required_skills': ['Python'], 'active_project': 'Alpha', 'project_summary': 'Alpha project desc'} if mid == 1 else None)
    monkeypatch.setattr(main, 'fetch_employee', lambda eid: {'name': 'Emp Test', 'experience_years': 3, 'education': 'BS Computer Science - Uni', 'skills': ['Python'], 'metrics': {'Velocity':'20'}, 'summary':'Solid contributor'} if eid == 2 else None)
    # Simulate POST body
    class DummyReq:
        async def json(self):
            return {'manager_id': 1, 'employee_id': 2, 'text': 'Is velocity sustainable?'}
    import asyncio
    resp = asyncio.run(main.add_comment(DummyReq()))
    data = _json_from_response(resp)
    assert any(m['role'] == 'teamlead' for m in data['conversation'])

def test_continue_conversation_appends_messages(tmp_path, monkeypatch):
    test_file = tmp_path / 'conversations.json'
    monkeypatch.setattr(main, 'CONVERSATION_FILE', str(test_file))
    monkeypatch.setattr(main, 'client', None)
    monkeypatch.setattr(main, 'fetch_project_manager', lambda mid: {'name': 'PM Test', 'required_skills': ['Python','SQL'], 'active_project': 'Alpha', 'project_summary': 'Alpha project desc'} if mid == 1 else None)
    monkeypatch.setattr(main, 'fetch_employee', lambda eid: {'name': 'Emp Test', 'experience_years': 5, 'education': 'BS Computer Science - Uni', 'skills': ['Python'], 'metrics': {'Quality':'95/100'}, 'summary':'Strong engineer focused on quality'} if eid == 2 else None)
    # Seed conversation first
    main.get_conversation(manager_id=1, employee_id=2)
    # Continue
    class DummyReq2:
        async def json(self):
            return {'manager_id': 1, 'employee_id': 2}
    import asyncio
    resp2 = asyncio.run(main.continue_conversation(DummyReq2()))
    data2 = _json_from_response(resp2)
    # Expect > initial seed length
    assert len(data2['conversation']) >= 5
