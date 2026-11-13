from fastapi.testclient import TestClient
from app.main import app

def test_health_and_correlation_id():
    with TestClient(app) as client:
        assert client.get('/healthz').json() == {'status': 'ok'}
        r = client.get('/work', headers={'x-request-id': 'test-correlation'})
        assert r.status_code == 200 and r.headers['x-request-id'] == 'test-correlation'

def test_error_and_metrics():
    with TestClient(app) as client:
        assert client.get('/work?fail=true').status_code == 503
        metrics = client.get('/metrics').text
        assert 'lab_http_requests_total{method="GET",route="/work",status="503"}' in metrics
        assert 'lab_http_request_duration_seconds_bucket' in metrics
