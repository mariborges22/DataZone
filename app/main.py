"""
DataZone Energy - FastAPI Application
Ponto de entrada principal da API
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.config import settings
from app.core.database import check_db_connection, close_db, init_db
from app.core.logging import app_logger as logger
from app.core.rate_limit import (
    custom_rate_limit_exceeded_handler,
    get_rate_limit_status,
    limiter,
)


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

# Adicionar rate limiter ao state da aplicação
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)


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
@limiter.limit("300/minute")  # Limite alto para monitoramento
async def health_check(request: Request):
    """
    Endpoint de health check para monitoramento
    """
    try:
        db_status = check_db_connection()
    except Exception:
        db_status = False

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
@limiter.limit("100/minute")
async def root(request: Request):
    """
    Endpoint raiz da API
    """
    return JSONResponse(
        content={
            "message": "DataZone Energy API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
            "rate_limit_status": "/api/v1/rate-limit-status",
        }
    )


# Rate limit status (útil para debug)
@app.get("/api/v1/rate-limit-status", tags=["System"])
@limiter.limit("60/minute")
async def rate_limit_status(request: Request):
    """
    Retorna status atual de rate limiting para o cliente
    """
    return get_rate_limit_status(request)


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
    import os

    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
