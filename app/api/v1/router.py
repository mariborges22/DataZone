"""
Router principal da API v1
Agrega todos os endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import bdgd, fibra, linhas, subestacoes, zoneamento_sp

api_router = APIRouter()

# Incluir rotas dos endpoints
api_router.include_router(subestacoes.router, prefix="/subestacoes", tags=["Subestações"])

api_router.include_router(linhas.router, prefix="/linhas", tags=["Linhas de Transmissão"])

api_router.include_router(fibra.router, prefix="/fibra", tags=["Fibra Ótica"])

api_router.include_router(zoneamento_sp.router, prefix="/zoneamento-sp", tags=["Zoneamento SP"])

api_router.include_router(bdgd.router, prefix="/bdgd", tags=["BDGD - Enel SP"])
