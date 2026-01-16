"""
DataZone Energy - FastAPI Application
Ponto de entrada principal da API
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.database import init_db, close_db, check_db_connection
from app.core.logging import app_logger as logger
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciamento do ciclo de vida da aplicação
    """
    # Startup
    logger.info("🚀 Iniciando DataZone Energy API...")
    logger.info(f"Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")

    # Verificar conexão com banco
    if check_db_connection():
        logger.info("✅ Conexão com PostgreSQL/PostGIS estabelecida")
    else:
        logger.error("❌ Falha ao conectar com o banco de dados")

    # Inicializar banco de dados
    try:
        await init_db()
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")

    yield

    # Shutdown
    logger.info("🛑 Encerrando DataZone Energy API...")
    await close_db()
    logger.info("✅ Conexões fechadas")


# ============================================
# Criar aplicação FastAPI
# ============================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Plataforma de Inteligência Geográfica para Site Selection de Data Centers",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)


# ============================================
# Middlewares
# ============================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compressão GZIP
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============================================
# Rotas
# ============================================


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de health check para monitoramento
    """
    db_status = check_db_connection()

    return JSONResponse(
        status_code=200 if db_status else 503,
        content={
            "status": "healthy" if db_status else "unhealthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected" if db_status else "disconnected",
        },
    )


# Root
@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raiz da API
    """
    return {
        "message": "DataZone Energy API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# Incluir rotas da API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ============================================
# Exception Handlers
# ============================================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handler global para exceções não tratadas
    """
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
