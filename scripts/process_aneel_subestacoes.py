"""
Script para processar dados de Subestações da ANEEL
Lê arquivos Geodatabase (.gdb) e carrega no PostGIS
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger
from sqlalchemy import create_engine

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


def setup_logging():
    """Configurar logging para o script"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )
    logger.add(
        "logs/process_aneel_subestacoes_{time:YYYY-MM-DD}.log",
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

    # Registros originais
    original_count = len(gdf)
    logger.info(f"Registros originais: {original_count}")

    # Remover geometrias inválidas
    invalid_geoms = ~gdf.geometry.is_valid
    if invalid_geoms.any():
        logger.warning(
            f"Encontradas {invalid_geoms.sum()} geometrias inválidas. Tentando corrigir..."
        )
        gdf.loc[invalid_geoms, "geometry"] = gdf.loc[invalid_geoms, "geometry"].buffer(0)

    # Remover geometrias vazias
    gdf = gdf[~gdf.geometry.is_empty].copy()

    # Remover duplicatas
    gdf = gdf.drop_duplicates()

    # Converter para EPSG:4326 se necessário
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


def process_subestacoes(gdb_path: str, layer_name: str = None) -> None:
    """
    Processa subestações de arquivo GDB da ANEEL

    Args:
        gdb_path: Caminho para o arquivo .gdb
        layer_name: Nome da camada (opcional, tenta detectar automaticamente)
    """
    logger.info("=" * 80)
    logger.info("PROCESSAMENTO DE SUBESTAÇÕES - ANEEL")
    logger.info("=" * 80)

    gdb_path = Path(gdb_path)

    # Verificar se arquivo existe
    if not gdb_path.exists():
        logger.error(f"Arquivo não encontrado: {gdb_path}")
        return

    logger.info(f"Arquivo GDB: {gdb_path}")

    try:
        # Listar camadas disponíveis
        import fiona

        layers = fiona.listlayers(str(gdb_path))
        logger.info(f"Camadas disponíveis: {layers}")

        # Detectar camada de subestações
        if layer_name is None:
            # Tentar encontrar camada com nome relacionado a subestações
            possible_names = [
                "subestacao",
                "subestacoes",
                "substation",
                "substations",
                "se",
            ]
            layer_name = next(
                (l for l in layers if any(name in l.lower() for name in possible_names)),
                layers[0] if layers else None,
            )

        if layer_name is None:
            logger.error("Nenhuma camada encontrada no arquivo GDB")
            return

        logger.info(f"Usando camada: {layer_name}")

        # Ler GeoDataFrame
        logger.info("Lendo dados...")
        gdf = gpd.read_file(gdb_path, layer=layer_name)

        logger.info(f"Colunas disponíveis: {list(gdf.columns)}")
        logger.info(f"Tipo de geometria: {gdf.geometry.type.unique()}")

        # Validar e limpar dados
        gdf = validate_gdf(gdf, layer_name)

        # Mapear colunas (ajustar conforme estrutura real do arquivo)
        # NOTA: Você precisará ajustar isso baseado nas colunas reais do seu arquivo
        column_mapping = {
            # Exemplo de mapeamento - AJUSTAR CONFORME NECESSÁRIO
            # 'NOME_CAMPO_GDB': 'nome_campo_banco',
        }

        # Preparar DataFrame para inserção
        df_to_insert = gdf.copy()

        # Adicionar metadados
        df_to_insert["data_source"] = "ANEEL"

        # Criar engine de conexão
        logger.info("Conectando ao banco de dados...")
        engine = create_engine(settings.DATABASE_URL)

        # Inserir no banco
        logger.info("Inserindo dados no PostGIS...")
        df_to_insert.to_postgis(
            name="subestacoes",
            con=engine,
            schema="geo",
            if_exists="append",  # 'replace' para sobrescrever, 'append' para adicionar
            index=False,
        )

        logger.success(f"✅ {len(df_to_insert)} subestações inseridas com sucesso!")

        # Estatísticas
        logger.info("\n" + "=" * 80)
        logger.info("ESTATÍSTICAS")
        logger.info("=" * 80)

        # Contar por UF (se disponível)
        if "uf" in df_to_insert.columns:
            logger.info("\nDistribuição por UF:")
            uf_counts = df_to_insert["uf"].value_counts()
            for uf, count in uf_counts.items():
                logger.info(f"  {uf}: {count}")

        # Contar por tensão (se disponível)
        if "tensao_kv" in df_to_insert.columns:
            logger.info("\nDistribuição por faixa de tensão:")
            df_to_insert["faixa_tensao"] = pd.cut(
                df_to_insert["tensao_kv"],
                bins=[0, 69, 138, 230, 500, 1000],
                labels=["< 69kV", "69-138kV", "138-230kV", "230-500kV", "> 500kV"],
            )
            tensao_counts = df_to_insert["faixa_tensao"].value_counts()
            for faixa, count in tensao_counts.items():
                logger.info(f"  {faixa}: {count}")

        engine.dispose()

    except Exception as e:
        logger.error(f"Erro ao processar subestações: {e}")
        logger.exception(e)
        raise


def main():
    """Função principal"""
    setup_logging()

    # AJUSTAR O CAMINHO DO ARQUIVO GDB
    gdb_path = "data/raw/aneel_subestacoes.gdb"

    # Processar
    process_subestacoes(gdb_path)


if __name__ == "__main__":
    main()
