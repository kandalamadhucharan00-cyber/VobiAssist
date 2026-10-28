from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['service'] == 'vobiassist'


def test_chat_endpoint_replies():
    response = client.post('/api/chat', json={'message': 'How do I troubleshoot 401 errors?'})
    assert response.status_code == 200
    payload = response.json()
    assert 'response' in payload
    assert isinstance(payload['response'], str)


def test_real_call_safeguard():
    response = client.post('/api/vobiz/call', json={'to': '+14155550100', 'from': '+14155550101', 'answer_url': 'https://example.com'})
    assert response.status_code == 403
    payload = response.json()
    assert 'disabled' in payload['detail'].lower()
