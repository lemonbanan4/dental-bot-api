import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def patch_db_functions(monkeypatch):
    # Replace DB helpers with stubs to avoid real DB calls
    monkeypatch.setattr('app.routes.leads.get_clinic_by_public_id', lambda cid: {"id": "fake-clinic-1"} if cid == "test-clinic" else None)
    monkeypatch.setattr('app.routes.leads.get_or_create_session', lambda **kwargs: {"id": "sess-1"})
    monkeypatch.setattr('app.routes.leads.create_lead', lambda **kwargs: None)


def test_lead_post_success():
    client = TestClient(app)
    res = client.post('/leads', json={
        'clinic_id': 'test-clinic',
        'session_id': 's1',
        'name': 'Tester',
        'phone': '+100',
        'message': 'hello'
    })
    assert res.status_code == 200
    assert res.json().get('ok') is True


def test_lead_rate_limit():
    client = TestClient(app)
    payload = {'clinic_id': 'test-clinic', 'session_id': 's2', 'name': 'A', 'phone': '+1', 'message': 'm'}
    # default limiter allows 5 requests; the 6th should be 429
    for i in range(5):
        r = client.post('/leads', json=payload)
        assert r.status_code == 200
    r6 = client.post('/leads', json=payload)
    assert r6.status_code == 429
