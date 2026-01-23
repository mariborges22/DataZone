from fastapi.testclient import TestClient

from app.main import app


def test_read_root():
    """
    Verifica se o endpoint raiz está respondendo corretamente.
    """
    # Instanciando cliente dentro do teste para isolamento
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "DataZone Energy API" in response.json()["message"]


def test_health_check_endpoint():
    """
    Verifica se o endpoint de 'health check' está funcionando.
    O banco de dados deve aparecer como 'connected' devido ao mock no conftest.py.
    """
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
