import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


# Verificação de segurança para não rodar em produção ou sem querer
def test_environment_check():
    """Garante que estamos rodando em modo de teste de integração."""
    assert (
        os.getenv("TEST_TYPE") == "integration"
    ), "Este teste deve rodar com TEST_TYPE=integration"


def test_list_zoneamento_integration():
    """
    Teste de integração REAL conectando ao banco PostGIS no Docker.
    Verifica se a API consegue consultar o banco e retornar GeoJSON válido.
    """
    # Utiliza o TestClient do FastAPI que, sem os mocks do conftest,
    # vai tentar usar a engine real definida no app.core.database
    with TestClient(app) as client:
        # A URL do endpoint
        response = client.get("/api/v1/zoneamento-sp?limit=5")

        # Se conectar com sucesso, deve retornar 200 (OK)
        # Se falhar conexão, retornaria 500 ou erro de startup
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert isinstance(data["features"], list)

        # Se houver dados no banco, valida o primeiro item
        if len(data["features"]) > 0:
            feature = data["features"][0]
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature
