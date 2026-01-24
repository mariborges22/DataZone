import os
import sys

import geopandas as gpd
from sqlalchemy import create_engine, text

from app.config import settings
from app.core.logging import app_logger as logger

# Adiciona o diretório raiz ao sys.path para importar módulos da app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def extrair_subestacoes(gdb_path: str):
    """
    Lê o arquivo .gdb da ANEEL, filtra Subestações de Alta Tensão (AT),
    converte o CRS para EPSG:4326 e salva no PostGIS.
    """
    logger.info(f"Iniciando extração de subestações do arquivo: {gdb_path}")

    if not os.path.exists(gdb_path):
        logger.error(f"Arquivo não encontrado: {gdb_path}")
        return

    try:
        # A camada exata pode variar, geralmente é 'SUB' ou 'Subestacao' na BDGD
        # Listar camadas se necessário: fiona.listlayers(gdb_path)
        layer_name = "SUB"

        logger.info(f"Lendo camada '{layer_name}'...")
        # Lendo apenas colunas necessárias para economizar memória se possível
        # Nota: read_file carrega tudo em memória. Para datasets gigantes, usar bbox ou row slice.
        gdf = gpd.read_file(gdb_path, layer=layer_name)

        initial_count = len(gdf)
        logger.info(f"Total de registros encontrados: {initial_count}")

        # Filtros:
        # Assumindo coluna 'POS' (Posição?) ou 'TEN' (Tensão).
        # Ajuste os nomes das colunas conforme o dicionário de dados da Distribuída/ANEEL.
        # Exemplo hipotético: Filtrar onde Tensão Nominal > 69kV ou Classificação é 'AT'

        # Para este MVP, vamos supor que queremos tudo que não seja 'BT' (Baixa Tensão)
        # Se não houver coluna clara, importamos tudo e filtramos no banco, mas o ideal é aqui.
        if "TEN_NOM" in gdf.columns:  # Exemplo de coluna
            gdf_at = gdf[gdf["TEN_NOM"].astype(float) >= 69]
            logger.info(f"Filtrado para Alta Tensão (>69kV): {len(gdf_at)} registros")
        else:
            logger.warning("Coluna de tensão não encontrada. Importando todos os registros.")
            gdf_at = gdf

        # Converter CRS para WGS84 (EPSG:4326)
        if gdf_at.crs != "EPSG:4326":
            logger.info("Convertendo CRS para EPSG:4326...")
            gdf_at = gdf_at.to_crs("EPSG:4326")

        # Selecionar e renomear colunas para bater com o modelo do banco
        # Ajuste conforme seu modelo SQLAlchemy (app.models.subestacao)
        # Exemplo: 'NOME' -> 'nome', 'COD_ID' -> 'codigo'
        columns_map = {
            "NOME": "nome",
            "COD_ID": "codigo",
            "TEN_NOM": "tensao_kv",
            # Adicione outros mapeamentos
        }

        # Manter apenas colunas que existem no dataframe
        valid_columns = {k: v for k, v in columns_map.items() if k in gdf_at.columns}
        gdf_final = gdf_at.rename(columns=valid_columns)

        # Salvar no PostGIS
        engine = create_engine(settings.DATABASE_URL)
        table_name = "subestacoes"

        logger.info(f"Salvando {len(gdf_final)} registros na tabela '{table_name}'...")

        # if_exists='append' para adicionar, 'replace' para recriar
        gdf_final.to_postgis(
            table_name,
            engine,
            if_exists="replace",  # Cuidado em produção!
            index=False,
            dtype={"geometry": "Point"},
        )

        logger.info("Extração e carga de subestações concluída com sucesso!")

    except Exception as e:
        logger.critical(f"Erro fatal na extração de subestações: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Exemplo de uso: pegar caminho dos argumentos ou variável de ambiente
    gdb_path = os.getenv("ANEEL_GDB_PATH", "data/raw/BDGD_ANEEL.gdb")
    extrair_subestacoes(gdb_path)
