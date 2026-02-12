"""
Endpoints para dados BDGD (Base de Dados Geográfica da Distribuidora) - Enel SP
Retorna dados em formato GeoJSON (camadas com geometria) e JSON (tabelas auxiliares)
"""

import json
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
from app.core.security import security
from app.models.bdgd import (
    BdgdArat,
    BdgdCtat,
    BdgdEqtrat,
    BdgdSegcon,
    BdgdSsdat,
    BdgdSub,
    BdgdUntrat,
)

router = APIRouter()


# ============================================
# Helpers
# ============================================


def _build_geojson_features(rows) -> list:
    """Converte rows do banco para lista de GeoJSON Features"""
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
    return features


def _apply_bbox_filter(query, model, bbox: str):
    """Aplica filtro de bounding box na query"""
    if not security.validate_bbox(bbox):
        raise HTTPException(status_code=400, detail="Bounding box inválido ou muito grande")
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
        envelope = ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        return query.where(ST_Intersects(model.geometry, envelope))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de bbox inválido. Use: min_lon,min_lat,max_lon,max_lat",
        )


def _add_geometry_column(query, model, simplify: bool):
    """Adiciona coluna de geometria (simplificada ou não) à query"""
    if simplify:
        return query.add_columns(
            ST_AsGeoJSON(ST_Simplify(model.geometry, settings.SIMPLIFY_TOLERANCE)).label("geometry")
        )
    return query.add_columns(ST_AsGeoJSON(model.geometry).label("geometry"))


# ============================================
# Endpoints com geometria
# ============================================


@router.get(
    "/sub",
    response_model=dict,
    summary="Subestações de Distribuição (BDGD)",
    description="Retorna subestações da BDGD Enel SP em formato GeoJSON",
)
@limiter.limit("20/minute")
async def get_bdgd_sub(
    request: Request,
    db: AsyncSession = Depends(get_db),
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    cod_id: Optional[str] = Query(None, description="Código identificador"),
    nome: Optional[str] = Query(None, description="Nome da subestação"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    simplify: bool = Query(True, description="Simplificar geometrias"),
):
    try:
        query = select(
            BdgdSub.id,
            BdgdSub.cod_id,
            BdgdSub.dist,
            BdgdSub.pos,
            BdgdSub.nome,
        )
        query = _add_geometry_column(query, BdgdSub, simplify)

        if bbox:
            query = _apply_bbox_filter(query, BdgdSub, bbox)
        if cod_id:
            query = query.where(BdgdSub.cod_id == cod_id)
        if nome:
            query = query.where(BdgdSub.nome.ilike(f"%{nome}%"))

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        return {"type": "FeatureCollection", "features": _build_geojson_features(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar subestações BDGD: {str(e)}")


@router.get(
    "/ssdat",
    response_model=dict,
    summary="Segmentos de Rede AT (BDGD)",
    description="Retorna segmentos de rede de alta tensão da BDGD Enel SP em formato GeoJSON",
)
@limiter.limit("20/minute")
async def get_bdgd_ssdat(
    request: Request,
    db: AsyncSession = Depends(get_db),
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    cod_id: Optional[str] = Query(None, description="Código identificador"),
    ctat: Optional[str] = Query(None, description="Código do circuito AT"),
    conj: Optional[str] = Query(None, description="Código do conjunto"),
    tip_cnd: Optional[str] = Query(None, description="Tipo de condutor"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    simplify: bool = Query(True, description="Simplificar geometrias"),
):
    try:
        query = select(
            BdgdSsdat.id,
            BdgdSsdat.cod_id,
            BdgdSsdat.ctat,
            BdgdSsdat.ct_cod_op,
            BdgdSsdat.conj,
            BdgdSsdat.dist,
            BdgdSsdat.fas_con,
            BdgdSsdat.tip_inst,
            BdgdSsdat.tip_cnd,
            BdgdSsdat.comp,
        )
        query = _add_geometry_column(query, BdgdSsdat, simplify)

        if bbox:
            query = _apply_bbox_filter(query, BdgdSsdat, bbox)
        if cod_id:
            query = query.where(BdgdSsdat.cod_id == cod_id)
        if ctat:
            query = query.where(BdgdSsdat.ctat == ctat)
        if conj:
            query = query.where(BdgdSsdat.conj == conj)
        if tip_cnd:
            query = query.where(BdgdSsdat.tip_cnd == tip_cnd)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        return {"type": "FeatureCollection", "features": _build_geojson_features(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar segmentos AT: {str(e)}")


@router.get(
    "/untrat",
    response_model=dict,
    summary="Transformadores AT (BDGD)",
    description="Retorna transformadores de alta tensão da BDGD Enel SP em formato GeoJSON",
)
@limiter.limit("20/minute")
async def get_bdgd_untrat(
    request: Request,
    db: AsyncSession = Depends(get_db),
    bbox: Optional[str] = Query(None, description="Bounding box: min_lon,min_lat,max_lon,max_lat"),
    cod_id: Optional[str] = Query(None, description="Código identificador"),
    sub: Optional[str] = Query(None, description="Código da subestação"),
    mun: Optional[str] = Query(None, description="Código do município"),
    pot_nom_min: Optional[float] = Query(None, ge=0, description="Potência nominal mínima (MVA)"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    simplify: bool = Query(False, description="Simplificar geometrias"),
):
    try:
        query = select(
            BdgdUntrat.id,
            BdgdUntrat.cod_id,
            BdgdUntrat.sub,
            BdgdUntrat.dist,
            BdgdUntrat.sit_ativ,
            BdgdUntrat.tip_unid,
            BdgdUntrat.pot_nom,
            BdgdUntrat.per_fer,
            BdgdUntrat.per_tot,
            BdgdUntrat.conj,
            BdgdUntrat.mun,
            BdgdUntrat.tip_trafo,
        )
        query = _add_geometry_column(query, BdgdUntrat, simplify)

        if bbox:
            query = _apply_bbox_filter(query, BdgdUntrat, bbox)
        if cod_id:
            query = query.where(BdgdUntrat.cod_id == cod_id)
        if sub:
            query = query.where(BdgdUntrat.sub == sub)
        if mun:
            query = query.where(BdgdUntrat.mun == mun)
        if pot_nom_min is not None:
            query = query.where(BdgdUntrat.pot_nom >= pot_nom_min)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        return {"type": "FeatureCollection", "features": _build_geojson_features(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transformadores AT: {str(e)}")


@router.get(
    "/arat",
    response_model=dict,
    summary="Área de Concessão (BDGD)",
    description="Retorna a área de concessão da Enel SP em formato GeoJSON",
)
@limiter.limit("20/minute")
async def get_bdgd_arat(
    request: Request,
    db: AsyncSession = Depends(get_db),
    simplify: bool = Query(True, description="Simplificar geometrias"),
):
    try:
        query = select(
            BdgdArat.id,
            BdgdArat.cod_id,
            BdgdArat.dist,
            BdgdArat.fun_pr,
            BdgdArat.fun_te,
        )
        query = _add_geometry_column(query, BdgdArat, simplify)

        result = await db.execute(query)
        rows = result.all()

        return {"type": "FeatureCollection", "features": _build_geojson_features(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar área de concessão: {str(e)}")


# ============================================
# Endpoints sem geometria (tabelas auxiliares)
# ============================================


@router.get(
    "/ctat",
    response_model=dict,
    summary="Circuitos AT (BDGD)",
    description="Retorna circuitos de alta tensão da BDGD Enel SP",
)
@limiter.limit("20/minute")
async def get_bdgd_ctat(
    request: Request,
    db: AsyncSession = Depends(get_db),
    cod_id: Optional[str] = Query(None, description="Código identificador"),
    nome: Optional[str] = Query(None, description="Nome do circuito"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
):
    try:
        query = select(
            BdgdCtat.id,
            BdgdCtat.cod_id,
            BdgdCtat.nome,
            BdgdCtat.ten_nom,
            BdgdCtat.pac_ini,
            BdgdCtat.dist,
        )

        if cod_id:
            query = query.where(BdgdCtat.cod_id == cod_id)
        if nome:
            query = query.where(BdgdCtat.nome.ilike(f"%{nome}%"))

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        data = []
        for row in rows:
            row_dict = dict(row._mapping)
            for key, value in row_dict.items():
                if hasattr(value, "isoformat"):
                    row_dict[key] = value.isoformat()
            data.append(row_dict)

        return {"total": len(data), "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar circuitos AT: {str(e)}")


@router.get(
    "/eqtrat",
    response_model=dict,
    summary="Equipamentos Transformadores AT (BDGD)",
    description="Retorna equipamentos de transformadores AT da BDGD Enel SP",
)
@limiter.limit("20/minute")
async def get_bdgd_eqtrat(
    request: Request,
    db: AsyncSession = Depends(get_db),
    cod_id: Optional[str] = Query(None, description="Código identificador"),
    uni_tr_at: Optional[str] = Query(None, description="Unidade transformadora AT"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
):
    try:
        query = select(
            BdgdEqtrat.id,
            BdgdEqtrat.cod_id,
            BdgdEqtrat.tip_inst,
            BdgdEqtrat.uni_tr_at,
            BdgdEqtrat.clas_ten,
            BdgdEqtrat.pot_nom,
            BdgdEqtrat.ten_pri,
            BdgdEqtrat.ten_sec,
            BdgdEqtrat.ten_ter,
            BdgdEqtrat.per_fer,
            BdgdEqtrat.per_tot,
        )

        if cod_id:
            query = query.where(BdgdEqtrat.cod_id == cod_id)
        if uni_tr_at:
            query = query.where(BdgdEqtrat.uni_tr_at == uni_tr_at)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        data = []
        for row in rows:
            row_dict = dict(row._mapping)
            for key, value in row_dict.items():
                if hasattr(value, "isoformat"):
                    row_dict[key] = value.isoformat()
            data.append(row_dict)

        return {"total": len(data), "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar equipamentos AT: {str(e)}")


@router.get(
    "/segcon",
    response_model=dict,
    summary="Segmentos Condutores (BDGD)",
    description="Retorna tipos de segmentos condutores da BDGD Enel SP",
)
@limiter.limit("20/minute")
async def get_bdgd_segcon(
    request: Request,
    db: AsyncSession = Depends(get_db),
    cod_id: Optional[str] = Query(None, description="Código identificador"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
):
    try:
        query = select(
            BdgdSegcon.id,
            BdgdSegcon.cod_id,
            BdgdSegcon.dist,
            BdgdSegcon.r1,
            BdgdSegcon.x1,
            BdgdSegcon.cnom,
            BdgdSegcon.cap_max,
            BdgdSegcon.r_regul,
        )

        if cod_id:
            query = query.where(BdgdSegcon.cod_id == cod_id)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        data = []
        for row in rows:
            row_dict = dict(row._mapping)
            for key, value in row_dict.items():
                if hasattr(value, "isoformat"):
                    row_dict[key] = value.isoformat()
            data.append(row_dict)

        return {"total": len(data), "data": data}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao buscar segmentos condutores: {str(e)}"
        )
