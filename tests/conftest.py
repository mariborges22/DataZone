import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

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
    monkeypatch.setattr("app.core.database.async_engine", AsyncMock())

    # Mock da função de verificação de conexão usada no health check
    monkeypatch.setattr("app.core.database.check_db_connection", lambda: True)

    # Mock de funções assíncronas de ciclo de vida (lifespan)
    # Mock de funções assíncronas de ciclo de vida (lifespan)
    # Importante: Mockar tanto na origem quanto no destino (app.main) onde é usado
    mock_init_db = AsyncMock()
    mock_close_db = AsyncMock()

    monkeypatch.setattr("app.core.database.init_db", mock_init_db)
    monkeypatch.setattr("app.core.database.close_db", mock_close_db)

    # Tentar mockar no app.main se já estiver importado
    import sys

    if "app.main" in sys.modules:
        monkeypatch.setattr("app.main.init_db", mock_init_db)
        monkeypatch.setattr("app.main.close_db", mock_close_db)
