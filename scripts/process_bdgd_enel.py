"""
Script para processar dados da BDGD (Base de Dados Geográfica da Distribuidora)
Enel SP - Lê arquivo Geodatabase (.gdb) e carrega no PostGIS

Camadas processadas:
- SUB: Subestações de distribuição (MultiPolygon)
- SSDAT: Segmentos de rede AT (MultiLineString)
- UNTRAT: Transformadores AT (Point)
- ARAT: Área de concessão (MultiPolygon)
- CTAT: Circuitos AT (tabela sem geometria)
- EQTRAT: Equipamentos transformadores AT (tabela sem geometria)
- SEGCON: Segmentos condutores (tabela sem geometria)
"""

import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
from loguru import logger
from sqlalchemy import create_engine, text

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

# Caminho do arquivo GDB
GDB_PATH = Path("data/raw/Enel_SP_390_2024-12-31_V11_20250926-0906.gdb/Enel_SP_390_2024-12-31_V11_20250926-0906.gdb")

# Camadas com geometria
GEO_LAYERS = {
    "SUB": {
        "table": "bdgd_sub",
        "geometry_type": "MULTIPOLYGON",
        "description": "Subestações de distribuição",
    },
    "SSDAT": {
        "table": "bdgd_ssdat",
        "geometry_type": "MULTILINESTRING",
        "description": "Segmentos de rede AT",
    },
    "UNTRAT": {
        "table": "bdgd_untrat",
        "geometry_type": "POINT",
        "description": "Transformadores AT",
    },
    "ARAT": {
        "table": "bdgd_arat",
        "geometry_type": "MULTIPOLYGON",
        "description": "Área de concessão",
    },
}

# Camadas sem geometria (tabelas auxiliares)
TABLE_LAYERS = {
    "CTAT": {
        "table": "bdgd_ctat",
        "description": "Circuitos AT",
    },
    "EQTRAT": {
        "table": "bdgd_eqtrat",
        "description": "Equipamentos transformadores AT",
    },
    "SEGCON": {
        "table": "bdgd_segcon",
        "description": "Segmentos condutores",
    },
}


def setup_logging():
    """Configurar logging para o script"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )
    logger.add(
        "logs/process_bdgd_enel_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
    )


def validate_gdf(gdf: gpd.GeoDataFrame, layer_name: str) -> gpd.GeoDataFrame:
    """
    Valida e limpa GeoDataFrame

    Args:
        gdf: GeoDataFrame a validar
        layer_name: Nome da camada (para logs)

    Returns:
        GeoDataFrame validado e limpo
    """
    logger.info(f"Validando {layer_name}...")
    original_count = len(gdf)

    # Remover geometrias inválidas
    invalid_geoms = ~gdf.geometry.is_valid
    if invalid_geoms.any():
        logger.warning(
            f"Encontradas {invalid_geoms.sum()} geometrias inválidas. Corrigindo..."
        )
        gdf.loc[invalid_geoms, "geometry"] = gdf.loc[invalid_geoms, "geometry"].buffer(0)

    # Remover geometrias vazias
    gdf = gdf[~gdf.geometry.is_empty].copy()

    # Remover duplicatas
    gdf = gdf.drop_duplicates()

    # Converter CRS de EPSG:4674 (SIRGAS 2000) para EPSG:4326 (WGS84)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        logger.info(f"Convertendo CRS de {gdf.crs} para EPSG:4326...")
        gdf = gdf.to_crs(epsg=4326)
    elif gdf.crs is None:
        logger.warning("CRS não definido. Assumindo EPSG:4326")
        gdf.set_crs(epsg=4326, inplace=True)

    final_count = len(gdf)
    logger.info(
        f"Registros após validação: {final_count} ({original_count - final_count} removidos)"
    )
    return gdf


def process_geo_layer(engine, gdb_path: str, layer_name: str, config: dict) -> int:
    """
    Processa uma camada com geometria do GDB e carrega no PostGIS

    Args:
        engine: SQLAlchemy engine
        gdb_path: Caminho para o arquivo .gdb
        layer_name: Nome da camada no GDB
        config: Configuração da camada (table, geometry_type, description)

    Returns:
        Número de registros inseridos
    """
    table_name = config["table"]
    logger.info(f"--- Processando {layer_name} ({config['description']}) ---")

    # Ler camada do GDB
    logger.info(f"Lendo camada {layer_name}...")
    gdf = gpd.read_file(str(gdb_path), layer=layer_name)
    logger.info(f"Registros lidos: {len(gdf):,}")
    logger.info(f"Colunas: {[c for c in gdf.columns if c != 'geometry']}")
    logger.info(f"Tipo geometria: {gdf.geometry.type.unique()}")

    # Validar e limpar
    gdf = validate_gdf(gdf, layer_name)

    # Renomear colunas para lowercase
    gdf.columns = [c.lower() for c in gdf.columns]

    # Remover colunas calculadas do shape (serão recalculadas pelo PostGIS)
    drop_cols = [c for c in ["shape_length", "shape_area"] if c in gdf.columns]
    if drop_cols:
        gdf = gdf.drop(columns=drop_cols)

    # Adicionar metadados
    gdf["data_source"] = "BDGD_ENEL_SP"

    # Inserir no PostGIS
    logger.info(f"Inserindo {len(gdf):,} registros na tabela geo.{table_name}...")
    gdf.to_postgis(
        name=table_name,
        con=engine,
        schema="geo",
        if_exists="replace",
        index=False,
        chunksize=1000,
    )

    logger.success(f"{len(gdf):,} registros inseridos em geo.{table_name}")
    return len(gdf)


def process_table_layer(engine, gdb_path: str, layer_name: str, config: dict) -> int:
    """
    Processa uma camada sem geometria (tabela auxiliar)

    Args:
        engine: SQLAlchemy engine
        gdb_path: Caminho para o arquivo .gdb
        layer_name: Nome da camada no GDB
        config: Configuração da camada (table, description)

    Returns:
        Número de registros inseridos
    """
    table_name = config["table"]
    logger.info(f"--- Processando {layer_name} ({config['description']}) ---")

    # Ler camada como DataFrame
    logger.info(f"Lendo camada {layer_name}...")
    df = pyogrio.read_dataframe(str(gdb_path), layer=layer_name)
    df = pd.DataFrame(df)
    logger.info(f"Registros lidos: {len(df):,}")
    logger.info(f"Colunas: {list(df.columns)}")

    # Renomear colunas para lowercase
    df.columns = [c.lower() for c in df.columns]

    # Renomear colunas reservadas do PostgreSQL
    reserved_renames = {"cmax": "cap_max", "cmin": "cap_min"}
    df = df.rename(columns={k: v for k, v in reserved_renames.items() if k in df.columns})

    # Remover duplicatas
    original = len(df)
    df = df.drop_duplicates()
    if len(df) < original:
        logger.info(f"Removidas {original - len(df)} duplicatas")

    # Remover coluna geometry se existir (vazia)
    if "geometry" in df.columns:
        df = df.drop(columns=["geometry"])

    # Adicionar metadados
    df["data_source"] = "BDGD_ENEL_SP"

    # Inserir no banco
    logger.info(f"Inserindo {len(df):,} registros na tabela geo.{table_name}...")
    df.to_sql(
        name=table_name,
        con=engine,
        schema="geo",
        if_exists="replace",
        index=False,
        chunksize=1000,
    )

    logger.success(f"{len(df):,} registros inseridos em geo.{table_name}")
    return len(df)


def create_indexes(engine):
    """Criar índices espaciais e B-tree para as tabelas BDGD"""
    logger.info("Criando índices...")

    indexes = [
        # Índices espaciais (GIST)
        "CREATE INDEX IF NOT EXISTS idx_bdgd_sub_geom ON geo.bdgd_sub USING GIST (geometry)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_ssdat_geom ON geo.bdgd_ssdat USING GIST (geometry)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_untrat_geom ON geo.bdgd_untrat USING GIST (geometry)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_arat_geom ON geo.bdgd_arat USING GIST (geometry)",
        # Índices B-tree
        "CREATE INDEX IF NOT EXISTS idx_bdgd_sub_cod_id ON geo.bdgd_sub (cod_id)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_ssdat_cod_id ON geo.bdgd_ssdat (cod_id)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_ssdat_ctat ON geo.bdgd_ssdat (ctat)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_untrat_cod_id ON geo.bdgd_untrat (cod_id)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_untrat_sub ON geo.bdgd_untrat (sub)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_ctat_cod_id ON geo.bdgd_ctat (cod_id)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_eqtrat_cod_id ON geo.bdgd_eqtrat (cod_id)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_eqtrat_uni_tr_at ON geo.bdgd_eqtrat (uni_tr_at)",
        "CREATE INDEX IF NOT EXISTS idx_bdgd_segcon_cod_id ON geo.bdgd_segcon (cod_id)",
    ]

    with engine.connect() as conn:
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                conn.commit()
            except Exception as e:
                logger.warning(f"Erro ao criar índice: {e}")

    logger.success("Índices criados com sucesso")


def main():
    """Função principal - processa todas as camadas BDGD"""
    setup_logging()

    logger.info("=" * 80)
    logger.info("PROCESSAMENTO BDGD - ENEL SP")
    logger.info("=" * 80)

    start_time = time.time()

    # Verificar arquivo GDB
    if not GDB_PATH.exists():
        logger.error(f"Arquivo não encontrado: {GDB_PATH}")
        logger.info("Coloque o arquivo .gdb em data/raw/")
        sys.exit(1)

    logger.info(f"Arquivo GDB: {GDB_PATH}")

    # Listar camadas disponíveis
    layers = pyogrio.list_layers(str(GDB_PATH))
    logger.info(f"Total de camadas no GDB: {len(layers)}")

    # Conectar ao banco
    logger.info("Conectando ao banco de dados...")
    engine = create_engine(settings.DATABASE_URL)

    # Garantir schema existe
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS geo"))
        conn.commit()

    total_records = 0
    results = {}

    # Processar camadas com geometria
    logger.info("\n" + "=" * 80)
    logger.info("CAMADAS COM GEOMETRIA")
    logger.info("=" * 80)

    for layer_name, config in GEO_LAYERS.items():
        try:
            count = process_geo_layer(engine, str(GDB_PATH), layer_name, config)
            results[layer_name] = count
            total_records += count
        except Exception as e:
            logger.error(f"Erro ao processar {layer_name}: {e}")
            logger.exception(e)
            results[layer_name] = f"ERRO: {e}"

    # Processar camadas sem geometria
    logger.info("\n" + "=" * 80)
    logger.info("TABELAS AUXILIARES (SEM GEOMETRIA)")
    logger.info("=" * 80)

    for layer_name, config in TABLE_LAYERS.items():
        try:
            count = process_table_layer(engine, str(GDB_PATH), layer_name, config)
            results[layer_name] = count
            total_records += count
        except Exception as e:
            logger.error(f"Erro ao processar {layer_name}: {e}")
            logger.exception(e)
            results[layer_name] = f"ERRO: {e}"

    # Criar índices
    logger.info("\n" + "=" * 80)
    logger.info("CRIAÇÃO DE ÍNDICES")
    logger.info("=" * 80)
    create_indexes(engine)

    # Resumo final
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO FINAL")
    logger.info("=" * 80)
    for layer, count in results.items():
        status = f"{count:,} registros" if isinstance(count, int) else count
        logger.info(f"  {layer:<10s}: {status}")
    logger.info(f"\nTotal de registros: {total_records:,}")
    logger.info(f"Tempo total: {elapsed:.1f}s")

    engine.dispose()
    logger.success("Processamento BDGD concluído!")


if __name__ == "__main__":
    main()
