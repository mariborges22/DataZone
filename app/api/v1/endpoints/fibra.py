"""
Endpoint para Infraestrutura de Fibra Ótica
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
from app.models.fibra_optica import FibraOptica

router = APIRouter()


@router.get(
    "",
    response_model=dict,
    summary="Listar Infraestrutura de Fibra Ótica",
    description="Retorna pontos de fibra ótica em formato GeoJSON com filtros opcionais",
)
@limiter.limit("20/minute")  # Rate limit para queries GeoJSON pesadas
async def get_fibra(
    request: Request,
    db: AsyncSession = Depends(get_db),
    # Filtros geográficos
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    uf: Optional[str] = Query(None, max_length=2, description="Unidade Federativa"),
    municipio: Optional[str] = Query(None, description="Nome do município"),
    # Filtros técnicos
    operadora: Optional[str] = Query(None, description="Nome da operadora"),
    tecnologia: Optional[str] = Query(None, description="Tipo de tecnologia"),
    capacidade_min: Optional[float] = Query(None, ge=0, description="Capacidade mínima (Gbps)"),
    # Paginação
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    # Simplificação
    simplify: bool = Query(True, description="Simplificar geometrias para reduzir tamanho"),
):
    """
    Retorna infraestrutura de fibra ótica em formato GeoJSON
    """
    try:
        # Query base
        query = select(
            FibraOptica.id,
            FibraOptica.operadora,
            FibraOptica.tipo,
            FibraOptica.tecnologia,
            FibraOptica.municipio,
            FibraOptica.uf,
            FibraOptica.capacidade_gbps,
            FibraOptica.status,
            FibraOptica.created_at,
            FibraOptica.data_source,
        )

        # Adicionar geometria (simplificada ou não)
        if simplify:
            query = query.add_columns(
                ST_AsGeoJSON(ST_Simplify(FibraOptica.geometry, settings.SIMPLIFY_TOLERANCE)).label(
                    "geometry"
                )
            )
        else:
            query = query.add_columns(ST_AsGeoJSON(FibraOptica.geometry).label("geometry"))

        # Aplicar filtros
        if bbox:
            try:
                min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
                envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
                query = query.where(ST_Intersects(FibraOptica.geometry, envelope))
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de bbox inválido")

        if uf:
            query = query.where(FibraOptica.uf == uf.upper())

        if municipio:
            query = query.where(FibraOptica.municipio.ilike(f"%{municipio}%"))

        if operadora:
            query = query.where(FibraOptica.operadora.ilike(f"%{operadora}%"))

        if tecnologia:
            query = query.where(FibraOptica.tecnologia.ilike(f"%{tecnologia}%"))

        if capacidade_min is not None:
            query = query.where(FibraOptica.capacidade_gbps >= capacidade_min)

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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar fibra: {str(e)}")


@router.get(
    "/{fibra_id}",
    response_model=dict,
    summary="Obter Ponto de Fibra por ID",
    description="Retorna um ponto de fibra ótica específico em formato GeoJSON",
)
@limiter.limit("50/minute")  # Limite mais permissivo para queries por ID
async def get_fibra_by_id(
    request: Request,
    fibra_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna um ponto de fibra ótica específico por ID
    """
    try:
        query = select(
            FibraOptica.id,
            FibraOptica.operadora,
            FibraOptica.tipo,
            FibraOptica.tecnologia,
            FibraOptica.municipio,
            FibraOptica.uf,
            FibraOptica.capacidade_gbps,
            FibraOptica.status,
            FibraOptica.created_at,
            FibraOptica.data_source,
            ST_AsGeoJSON(FibraOptica.geometry).label("geometry"),
        ).where(FibraOptica.id == fibra_id)

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Ponto de fibra não encontrado")

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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar fibra: {str(e)}")
