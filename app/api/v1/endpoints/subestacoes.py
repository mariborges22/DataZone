"""
Endpoint para Subestações
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
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import security
from app.models.subestacao import Subestacao
from app.schemas.base import FeatureCollectionBase
from app.utils.geo_utils import rows_to_feature_collection

router = APIRouter()


@router.get(
    "",
    response_model=dict,
    summary="Listar Subestações",
    description="Retorna subestações em formato GeoJSON com filtros opcionais",
)
@limiter.limit("20/minute")  # Rate limit para queries GeoJSON pesadas
async def get_subestacoes(
    request: Request,
    db: AsyncSession = Depends(get_db),
    # Filtros geográficos
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    uf: Optional[str] = Query(None, max_length=2, description="Unidade Federativa"),
    municipio: Optional[str] = Query(None, description="Nome do município"),
    # Filtros técnicos
    tensao_min: Optional[float] = Query(None, ge=0, description="Tensão mínima (kV)"),
    tensao_max: Optional[float] = Query(None, ge=0, description="Tensão máxima (kV)"),
    operador: Optional[str] = Query(None, description="Nome do operador"),
    # Paginação
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    # Simplificação
    simplify: bool = Query(True, description="Simplificar geometrias para reduzir tamanho"),
):
    """
    Retorna subestações em formato GeoJSON
    """
    try:
        # Query base - SEGURANÇA: Não expor campos sensíveis
        query = select(
            Subestacao.id,
            Subestacao.nome,
            Subestacao.codigo,
            Subestacao.tensao_kv,
            Subestacao.tipo,
            Subestacao.operador,
            Subestacao.municipio,
            Subestacao.uf,
            Subestacao.capacidade_mva,
            Subestacao.status,
            # SEGURANÇA: Não expor created_at, data_source
        )

        # Adicionar geometria (simplificada ou não)
        if simplify:
            query = query.add_columns(
                ST_AsGeoJSON(ST_Simplify(Subestacao.geometry, settings.SIMPLIFY_TOLERANCE)).label(
                    "geometry"
                )
            )
        else:
            query = query.add_columns(ST_AsGeoJSON(Subestacao.geometry).label("geometry"))

        # Aplicar filtros
        if bbox:
            # SEGURANÇA: Validar bbox antes de usar
            if not security.validate_bbox(bbox):
                raise HTTPException(status_code=400, detail="Bounding box inválido ou muito grande")

            try:
                min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
                envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
                query = query.where(ST_Intersects(Subestacao.geometry, envelope))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de bbox inválido. Use: min_lon,min_lat,max_lon,max_lat",
                )

        if uf:
            query = query.where(Subestacao.uf == uf.upper())

        if municipio:
            query = query.where(Subestacao.municipio.ilike(f"%{municipio}%"))

        if tensao_min is not None:
            query = query.where(Subestacao.tensao_kv >= tensao_min)

        if tensao_max is not None:
            query = query.where(Subestacao.tensao_kv <= tensao_max)

        if operador:
            query = query.where(Subestacao.operador.ilike(f"%{operador}%"))

        # Paginação
        query = query.offset(skip).limit(limit)

        # Executar query
        result = await db.execute(query)
        rows = result.all()

        # Converter para GeoJSON
        # Como ST_AsGeoJSON retorna string, precisamos parsear
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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar subestações: {str(e)}")


@router.get(
    "/{subestacao_id}",
    response_model=dict,
    summary="Obter Subestação por ID",
    description="Retorna uma subestação específica em formato GeoJSON",
)
@limiter.limit("50/minute")  # Limite mais permissivo para queries por ID
async def get_subestacao_by_id(
    request: Request,
    subestacao_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna uma subestação específica por ID
    """
    try:
        query = select(
            Subestacao.id,
            Subestacao.nome,
            Subestacao.codigo,
            Subestacao.tensao_kv,
            Subestacao.tipo,
            Subestacao.operador,
            Subestacao.municipio,
            Subestacao.uf,
            Subestacao.capacidade_mva,
            Subestacao.status,
            # SEGURANÇA: Não expor created_at, data_source
            ST_AsGeoJSON(Subestacao.geometry).label("geometry"),
        ).where(Subestacao.id == subestacao_id)

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Subestação não encontrada")

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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar subestação: {str(e)}")
