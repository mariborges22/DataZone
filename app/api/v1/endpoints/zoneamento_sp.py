"""
Endpoint para Zoneamento Urbano de São Paulo
Retorna polígonos de zoneamento em formato GeoJSON
Fonte: Lei 18.177/2024
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
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
from app.models.zoneamento_sp import ZoneamentoSP

router = APIRouter()


@router.get(
    "",
    response_model=dict,
    summary="Listar Zoneamento de São Paulo",
    description="Retorna polígonos de zoneamento urbano de São Paulo em formato GeoJSON",
)
@limiter.limit("20/minute")  # Rate limit para queries GeoJSON pesadas
async def get_zoneamento(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    # Filtros geográficos
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    # Filtros de zoneamento
    cd_zoneamento_perimetro: Optional[str] = Query(
        None, description="Código do zoneamento (ex: ZEPAM, ZC, ZEIS-1, ZM, ZER-1)"
    ),
    an_legislacao_zoneamento: Optional[int] = Query(
        None, ge=1900, le=2100, description="Ano da legislação"
    ),
    cd_tipo_legislacao_zoneamento: Optional[str] = Query(
        None, description="Tipo da legislação (lei, decreto, etc.)"
    ),
    # Paginação
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    # Simplificação (MUITO importante para polígonos!)
    simplify: bool = Query(True, description="Simplificar geometrias para reduzir tamanho"),
    simplify_tolerance: Optional[float] = Query(
        None, ge=0.0001, le=0.01, description="Tolerância de simplificação (padrão: 0.001)"
    ),
):
    """
    Retorna polígonos de zoneamento urbano de São Paulo em formato GeoJSON.

    **Filtros disponíveis:**
    - `bbox`: Filtro espacial por bounding box
    - `cd_zoneamento_perimetro`: Código do zoneamento (ZEPAM, ZC, ZEIS-1, etc)
    - `an_legislacao_zoneamento`: Ano da legislação
    - `cd_tipo_legislacao_zoneamento`: Tipo da legislação

    **Performance:**
    - Use `simplify=true` (padrão) para reduzir o tamanho da resposta
    - Use `bbox` para consultar apenas áreas específicas
    - Limite os resultados com `limit` (máximo 1000)
    """
    try:
        # Query base - selecionar todos os campos
        query = select(
            ZoneamentoSP.id_original,
            ZoneamentoSP.cd_tipo_legislacao_zoneamento,
            ZoneamentoSP.cd_numero_legislacao_zoneamento,
            ZoneamentoSP.an_legislacao_zoneamento,
            ZoneamentoSP.cd_zoneamento_perimetro,
            ZoneamentoSP.tx_zoneamento_perimetro,
            ZoneamentoSP.cd_identificador,
            ZoneamentoSP.tx_observacao_perimetro,
            ZoneamentoSP.dt_atualizacao,
            ZoneamentoSP.cd_usuario_atualizacao,
            ZoneamentoSP.data_source,
        )

        # Adicionar geometria (simplificada ou não)
        tolerance = simplify_tolerance if simplify_tolerance else settings.SIMPLIFY_TOLERANCE
        if simplify:
            query = query.add_columns(
                ST_AsGeoJSON(ST_Simplify(ZoneamentoSP.geometry, tolerance)).label("geometry")
            )
        else:
            query = query.add_columns(ST_AsGeoJSON(ZoneamentoSP.geometry).label("geometry"))

        # Aplicar filtros espaciais
        if bbox:
            try:
                min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))

                # Validar bbox para São Paulo (aproximadamente)
                if not (-47.0 <= min_lon <= -46.0 and -24.0 <= min_lat <= -23.0):
                    raise HTTPException(
                        status_code=400, detail="Bounding box fora dos limites de São Paulo"
                    )

                envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
                query = query.where(ST_Intersects(ZoneamentoSP.geometry, envelope))
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de bbox inválido")

        # Aplicar filtros de zoneamento
        if cd_zoneamento_perimetro:
            query = query.where(
                ZoneamentoSP.cd_zoneamento_perimetro.ilike(f"%{cd_zoneamento_perimetro}%")
            )

        if an_legislacao_zoneamento:
            query = query.where(ZoneamentoSP.an_legislacao_zoneamento == an_legislacao_zoneamento)

        if cd_tipo_legislacao_zoneamento:
            query = query.where(
                ZoneamentoSP.cd_tipo_legislacao_zoneamento.ilike(
                    f"%{cd_tipo_legislacao_zoneamento}%"
                )
            )

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

            # Converter campos datetime para ISO format
            properties = {}
            for key, value in row_dict.items():
                if hasattr(value, "isoformat"):
                    properties[key] = value.isoformat()
                else:
                    properties[key] = value

            features.append({"type": "Feature", "geometry": geometry, "properties": properties})

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "count": len(features),
                "skip": skip,
                "limit": limit,
                "simplified": simplify,
                "tolerance": tolerance if simplify else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar zoneamento: {str(e)}")


@router.get(
    "/{zoneamento_id}",
    response_model=dict,
    summary="Obter Zoneamento por ID",
    description="Retorna um polígono de zoneamento específico em formato GeoJSON",
)
@limiter.limit("50/minute")  # Limite mais permissivo para queries por ID
async def get_zoneamento_by_id(
    request: Request,
    response: Response,
    zoneamento_id: str,
    db: AsyncSession = Depends(get_db),
    simplify: bool = Query(True, description="Simplificar geometria"),
):
    """
    Retorna um polígono de zoneamento específico por ID original.
    """
    try:
        query = select(
            ZoneamentoSP.id_original,
            ZoneamentoSP.cd_tipo_legislacao_zoneamento,
            ZoneamentoSP.cd_numero_legislacao_zoneamento,
            ZoneamentoSP.an_legislacao_zoneamento,
            ZoneamentoSP.cd_zoneamento_perimetro,
            ZoneamentoSP.tx_zoneamento_perimetro,
            ZoneamentoSP.cd_identificador,
            ZoneamentoSP.tx_observacao_perimetro,
            ZoneamentoSP.dt_atualizacao,
            ZoneamentoSP.cd_usuario_atualizacao,
            ZoneamentoSP.data_source,
        )

        # Adicionar geometria
        if simplify:
            query = query.add_columns(
                ST_AsGeoJSON(ST_Simplify(ZoneamentoSP.geometry, settings.SIMPLIFY_TOLERANCE)).label(
                    "geometry"
                )
            )
        else:
            query = query.add_columns(ST_AsGeoJSON(ZoneamentoSP.geometry).label("geometry"))

        query = query.where(ZoneamentoSP.id_original == zoneamento_id)

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=404, detail=f"Zoneamento com ID {zoneamento_id} não encontrado"
            )

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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar zoneamento: {str(e)}")


@router.get(
    "/stats/summary",
    response_model=dict,
    summary="Estatísticas de Zoneamento",
    description="Retorna estatísticas resumidas sobre o zoneamento de São Paulo",
)
@limiter.limit("10/minute")
async def get_zoneamento_stats(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna estatísticas sobre os dados de zoneamento.

    **Retorna:**
    - Total de polígonos
    - Tipos de zoneamento únicos
    - Anos de legislação
    - Contagem por tipo de legislação
    """
    try:
        from sqlalchemy import func

        # Total de registros
        total_query = select(func.count(ZoneamentoSP.id_original))
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # Tipos de zoneamento únicos
        tipos_query = (
            select(
                ZoneamentoSP.cd_zoneamento_perimetro,
                func.count(ZoneamentoSP.id_original).label("count"),
            )
            .group_by(ZoneamentoSP.cd_zoneamento_perimetro)
            .order_by(func.count(ZoneamentoSP.id_original).desc())
            .limit(20)
        )

        tipos_result = await db.execute(tipos_query)
        tipos = [{"codigo": row[0], "count": row[1]} for row in tipos_result.all()]

        # Anos de legislação
        anos_query = (
            select(
                ZoneamentoSP.an_legislacao_zoneamento,
                func.count(ZoneamentoSP.id_original).label("count"),
            )
            .group_by(ZoneamentoSP.an_legislacao_zoneamento)
            .order_by(ZoneamentoSP.an_legislacao_zoneamento.desc())
        )

        anos_result = await db.execute(anos_query)
        anos = [{"ano": row[0], "count": row[1]} for row in anos_result.all() if row[0] is not None]

        return {
            "total_poligonos": total,
            "tipos_zoneamento": tipos,
            "anos_legislacao": anos,
            "fonte": "BigQuery - Lei 18.177/2024",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")
