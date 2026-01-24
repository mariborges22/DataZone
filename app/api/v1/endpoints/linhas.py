"""
Endpoint para Linhas de Transmissão
Retorna dados em formato GeoJSON
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from geoalchemy2.functions import (
    ST_AsGeoJSON,
    ST_Intersects,
    ST_MakeEnvelope,
    ST_Simplify,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.linha_transmissao import LinhaTransmissao

router = APIRouter()


@router.get(
    "",
    response_model=dict,
    summary="Listar Linhas de Transmissão",
    description="Retorna linhas de transmissão em formato GeoJSON com filtros opcionais",
)
@limiter.limit("20/minute")  # Rate limit para queries GeoJSON pesadas
async def get_linhas(
    request: Request,
    db: AsyncSession = Depends(get_db),
    # Filtros geográficos
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    # Filtros técnicos
    tensao_min: Optional[float] = Query(None, ge=0, description="Tensão mínima (kV)"),
    tensao_max: Optional[float] = Query(None, ge=0, description="Tensão máxima (kV)"),
    operador: Optional[str] = Query(None, description="Nome do operador"),
    origem: Optional[str] = Query(None, description="Subestação de origem"),
    destino: Optional[str] = Query(None, description="Subestação de destino"),
    # Paginação
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    # Simplificação
    simplify: bool = Query(True, description="Simplificar geometrias para reduzir tamanho"),
):
    """
    Retorna linhas de transmissão em formato GeoJSON
    """
    try:
        # Query base
        query = select(
            LinhaTransmissao.id,
            LinhaTransmissao.nome,
            LinhaTransmissao.codigo,
            LinhaTransmissao.tensao_kv,
            LinhaTransmissao.extensao_km,
            LinhaTransmissao.operador,
            LinhaTransmissao.origem,
            LinhaTransmissao.destino,
            LinhaTransmissao.status,
            LinhaTransmissao.created_at,
            LinhaTransmissao.data_source,
        )

        # Adicionar geometria (simplificada ou não)
        if simplify:
            query = query.add_columns(
                ST_AsGeoJSON(
                    ST_Simplify(LinhaTransmissao.geometry, settings.SIMPLIFY_TOLERANCE)
                ).label("geometry")
            )
        else:
            query = query.add_columns(ST_AsGeoJSON(LinhaTransmissao.geometry).label("geometry"))

        # Aplicar filtros
        if bbox:
            try:
                min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
                envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
                query = query.where(ST_Intersects(LinhaTransmissao.geometry, envelope))
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de bbox inválido")

        if tensao_min is not None:
            query = query.where(LinhaTransmissao.tensao_kv >= tensao_min)

        if tensao_max is not None:
            query = query.where(LinhaTransmissao.tensao_kv <= tensao_max)

        if operador:
            query = query.where(LinhaTransmissao.operador.ilike(f"%{operador}%"))

        if origem:
            query = query.where(LinhaTransmissao.origem.ilike(f"%{origem}%"))

        if destino:
            query = query.where(LinhaTransmissao.destino.ilike(f"%{destino}%"))

        # Paginação
        query = query.offset(skip).limit(limit)

        # Executar query
        result = await db.execute(query)
        rows = result.all()

        # Converter para GeoJSON
        import json

        features = []
        for row in rows:
            row_dict = dict(row._mapping)
            geometry_str = row_dict.pop("geometry")
            geometry = json.loads(geometry_str) if geometry_str else None

            properties = {}
            for key, value in row_dict.items():
                if hasattr(value, "isoformat"):
                    properties[key] = value.isoformat()
                else:
                    properties[key] = value

            features.append({"type": "Feature", "geometry": geometry, "properties": properties})

        return {"type": "FeatureCollection", "features": features}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar linhas: {str(e)}")


@router.get(
    "/{linha_id}",
    response_model=dict,
    summary="Obter Linha por ID",
    description="Retorna uma linha de transmissão específica em formato GeoJSON",
)
@limiter.limit("50/minute")  # Limite mais permissivo para queries por ID
async def get_linha_by_id(
    request: Request,
    linha_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna uma linha de transmissão específica por ID
    """
    try:
        query = select(
            LinhaTransmissao.id,
            LinhaTransmissao.nome,
            LinhaTransmissao.codigo,
            LinhaTransmissao.tensao_kv,
            LinhaTransmissao.extensao_km,
            LinhaTransmissao.operador,
            LinhaTransmissao.origem,
            LinhaTransmissao.destino,
            LinhaTransmissao.status,
            LinhaTransmissao.created_at,
            LinhaTransmissao.data_source,
            ST_AsGeoJSON(LinhaTransmissao.geometry).label("geometry"),
        ).where(LinhaTransmissao.id == linha_id)

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        # Converter para GeoJSON Feature
        import json

        row_dict = dict(row._mapping)
        geometry_str = row_dict.pop("geometry")
        geometry = json.loads(geometry_str) if geometry_str else None

        properties = {}
        for key, value in row_dict.items():
            if hasattr(value, "isoformat"):
                properties[key] = value.isoformat()
            else:
                properties[key] = value

        return {"type": "Feature", "geometry": geometry, "properties": properties}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar linha: {str(e)}")
