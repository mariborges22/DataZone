from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

# Mock do modelo para evitar erros de importação se o DB não estiver conectado
class MockZoneamentoSP:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Mock do atributo _mapping usado na conversão para dict
        self._mapping = kwargs

@pytest.fixture
def mock_db_session():
    """Fixture para criar uma sessão de banco mockada."""
    session = AsyncMock()
    return session

@pytest.fixture
def client(mock_db_session):
    """Fixture do cliente de teste com override de dependência do DB."""
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_list_zoneamento_success(client, mock_db_session):
    """
    Testa a listagem de zoneamentos com sucesso (200 OK).
    Simula o retorno do banco de dados com dados fictícios.
    """
    # 1. Configurar o Mock do Banco de Dados
    # Simula o resultado de db.execute(query).all()
    mock_result = MagicMock()
    
    # Criando objetos mock que simulam as linhas retornadas pelo SQLAlchemy
    # Precisamos simular a geometria como string GeoJSON pq o endpoint faz parse disso
    row1 = MockZoneamentoSP(
        id_original="123",
        cd_tipo_legislacao_zoneamento="LEI",
        cd_numero_legislacao_zoneamento="18177",
        an_legislacao_zoneamento=2024,
        cd_zoneamento_perimetro="ZEPAM",
        tx_zoneamento_perimetro="Zona Especial de Proteção Ambiental",
        cd_identificador="ZP-01",
        tx_observacao_perimetro="Obs teste",
        dt_atualizacao=datetime(2024, 1, 1),
        cd_usuario_atualizacao="admin",
        data_source="TESTE",
        geometry='{"type": "MultiPolygon", "coordinates": [[[[0,0], [0,1], [1,1], [1,0], [0,0]]]]}'
    )
    
    # Configura o retorno do mock
    mock_result.all.return_value = [row1]
    
    # O mock da sessão deve retornar nosso mock_result quando execute() for chamado
    mock_db_session.execute.return_value = mock_result

    # 2. Executar a Requisição
    response = client.get("/api/v1/zoneamento-sp?limit=10&simplify=true")

    # 3. Asserções
    assert response.status_code == 200
    data = response.json()
    
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    
    feature = data["features"][0]
    assert feature["properties"]["cd_zoneamento_perimetro"] == "ZEPAM"
    assert feature["properties"]["an_legislacao_zoneamento"] == 2024
    assert feature["geometry"]["type"] == "MultiPolygon"

def test_get_zoneamento_by_id_success(client, mock_db_session):
    """Testa a busca de zoneamento por ID com sucesso."""
    
    # Mock do resultado
    mock_result = MagicMock()
    row = MockZoneamentoSP(
        id_original="TEST-ID-1",
        cd_tipo_legislacao_zoneamento="LEI",
        cd_numero_legislacao_zoneamento="18177",
        an_legislacao_zoneamento=2024,
        cd_zoneamento_perimetro="ZC",
        tx_zoneamento_perimetro="Zona Centralidade",
        cd_identificador="ZC-01",
        tx_observacao_perimetro=None,
        dt_atualizacao=None,
        cd_usuario_atualizacao=None,
        data_source="TESTE",
        geometry='{"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]}'
    )
    
    # .first() retorna a primeira linha
    mock_result.first.return_value = row
    mock_db_session.execute.return_value = mock_result

    response = client.get("/api/v1/zoneamento-sp/TEST-ID-1")

    assert response.status_code == 200
    feature = response.json()
    assert feature["type"] == "Feature"
    assert feature["properties"]["id_original"] == "TEST-ID-1"
    assert feature["properties"]["cd_zoneamento_perimetro"] == "ZC"

def test_get_zoneamento_by_id_not_found(client, mock_db_session):
    """Testa a busca por ID inexistente (404 Not Found)."""
    
    mock_result = MagicMock()
    mock_result.first.return_value = None # Nenhum resultado encontrado
    mock_db_session.execute.return_value = mock_result

    response = client.get("/api/v1/zoneamento-sp/ID_INEXISTENTE")

    assert response.status_code == 404
    assert response.json()["detail"] == "Zoneamento com ID ID_INEXISTENTE não encontrado"
