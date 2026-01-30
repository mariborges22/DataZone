"""
Configuração do banco de dados PostgreSQL/PostGIS
Suporte para conexões síncronas e assíncronas
"""

from typing import AsyncGenerator

from geoalchemy2 import Geometry
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# Base para modelos SQLAlchemy
Base = declarative_base()


# ============================================
# Engine Síncrono (para scripts de migração)
# ============================================
import os


# Função para garantir URL correta para drivers assíncronos
def get_async_database_url(url: str) -> str:
    if url and url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# Obter URL do ambiente (prioridade sobre settings)
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL") or get_async_database_url(DATABASE_URL)

sync_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.MAX_CONNECTIONS_POOL,
    max_overflow=10,
    echo=False,  # SEGURANÇA: Nunca logar SQL queries
)

# Session síncrona
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# ============================================
# Engine Assíncrono (para API)
# ============================================
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.MAX_CONNECTIONS_POOL,
    max_overflow=10,
    echo=False,  # SEGURANÇA: Nunca logar SQL queries
)

# Session assíncrona
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ============================================
# Dependency Injection para FastAPI
# ============================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que fornece sessão de banco de dados assíncrona
    Uso: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """
    Dependency para sessão síncrona (scripts)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================
# Funções auxiliares
# ============================================
async def init_db() -> None:
    """
    Inicializa o banco de dados (cria tabelas se não existirem)
    """
    async with async_engine.begin() as conn:
        # Importar todos os modelos aqui para garantir que sejam registrados
        from app.models import fibra_optica, linha_transmissao, subestacao, zoneamento_sp

        # Criar todas as tabelas
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Fecha conexões com o banco de dados
    """
    await async_engine.dispose()


def check_db_connection() -> bool:
    """
    Verifica se a conexão com o banco está funcionando
    """
    try:
        from sqlalchemy import text

        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False
