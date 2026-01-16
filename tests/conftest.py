import pytest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Adiciona o diretório raiz ao sys.path para que o pytest encontre a pasta 'app'
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(autouse=True)
def mock_db_connection(monkeypatch):
    """
    Mock global para evitar que qualquer teste tente conectar ao banco real.
    Isso substitui o motor (engine) e a sessão do SQLAlchemy por mocks.
    """
    # Mock do objeto de configurações para garantir que não use URLs reais acidentalmente
    monkeypatch.setattr("app.core.database.sync_engine", MagicMock())
    monkeypatch.setattr("app.core.database.async_engine", MagicMock())
    
    # Mock da função de verificação de conexão usada no health check
    monkeypatch.setattr("app.core.database.check_db_connection", lambda: True)
