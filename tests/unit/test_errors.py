from fastapi.testclient import TestClient
from app.main import app
from app.exceptions.base import ClubNotFoundError, PermissionDeniedError

client = TestClient(app)

def test_domain_error_mapping_404():
    @app.get("/_t404")
    def _t():
        raise ClubNotFoundError()
    r = client.get("/_t404")
    assert r.status_code == 404
    assert r.json()["detail"]

def test_domain_error_mapping_403():
    @app.get("/_t403")
    def _t():
        raise PermissionDeniedError()
    r = client.get("/_t403")
    assert r.status_code == 403



