"""
DataZone Energy - Extração Zoneamento SP (BigQuery → PostGIS)
================================================================
Pipeline ETL para extrair dados de zoneamento urbano de São Paulo do BigQuery
e carregar no PostGIS de forma otimizada.

Fonte: Lei 18.177/2024 - Zoneamento do Município de São Paulo
Autor: DataZone Energy Team
Data: 2026-01-28
"""

import os
import sys
import time
from typing import Optional

import pandas as pd
from geoalchemy2 import WKTElement
from google.cloud import bigquery
from loguru import logger
from sqlalchemy import create_engine, text

# Configurar logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger.add(
    "logs/etl_zoneamento_sp_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
)


class ZoneamentoSPETL:
    """Pipeline ETL para extração de dados de Zoneamento SP do BigQuery."""

    def __init__(
        self,
        project_id: str,
        database_url: str,
        bigquery_dataset: str,
        bigquery_table: str,
        chunk_size: int = 5000,
    ):
        """
        Inicializa a pipeline ETL.

        Args:
            project_id: ID do projeto GCP para billing (ex: 'causal-tracker-484821-f1')
            database_url: URL de conexão PostgreSQL
            bigquery_dataset: Nome do dataset no BigQuery (ex: 'zoneamento_sp')
            bigquery_table: Nome da tabela no BigQuery (ex: 'zoneamento_curado')
            chunk_size: Tamanho dos chunks para processamento
        """
        self.project_id = project_id
        self.database_url = database_url
        self.bigquery_dataset = bigquery_dataset
        self.bigquery_table = bigquery_table
        self.chunk_size = chunk_size

        self.bq_client: Optional[bigquery.Client] = None
        self.pg_engine = None

        logger.info(
            f"Pipeline ETL inicializada | "
            f"Projeto: {project_id} | "
            f"Tabela: {bigquery_dataset}.{bigquery_table} | "
            f"Chunk Size: {chunk_size}"
        )

    def _validate_credentials(self) -> bool:
        """Valida credenciais do Google Cloud (ADC)."""
        try:
            import google.auth

            credentials, project = google.auth.default()
            if not credentials:
                logger.error("Credenciais ADC não encontradas!")
                return False
            logger.success(f"Credenciais GCP (ADC) detectadas. Projeto: {project}")
            return True
        except Exception as e:
            logger.error(f"Erro ao validar credenciais ADC: {e}")
            return False

    def _connect_bigquery(self) -> bool:
        """Estabelece conexão com BigQuery."""
        try:
            self.bq_client = bigquery.Client(project=self.project_id)

            # Teste de conexão
            query_test = "SELECT 1 as test"
            job_config = bigquery.QueryJobConfig(use_query_cache=False, use_legacy_sql=False)
            self.bq_client.query(query_test, job_config=job_config).result()

            logger.success(f"✅ Conectado ao BigQuery | Projeto: {self.project_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao conectar BigQuery: {e}")
            return False

    def _connect_postgres(self) -> bool:
        """Estabelece conexão com PostgreSQL/PostGIS."""
        try:
            self.pg_engine = create_engine(self.database_url)

            # Teste de conexão
            with self.pg_engine.connect() as conn:
                result = conn.execute(text("SELECT PostGIS_Version()"))
                version = result.fetchone()[0]
                logger.success(f"✅ Conectado ao PostGIS | Versão: {version}")

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            return False

    def _execute_bigquery(self) -> Optional[pd.DataFrame]:
        """
        Executa query no BigQuery e retorna DataFrame.

        Returns:
            DataFrame com resultados ou None em caso de erro
        """
        try:
            logger.info("Executando query no BigQuery...")
            start_time = time.time()

            # Query otimizada: extrai dados com geometria em WKT
            query = f"""
            SELECT
                id,
                cd_tipo_legislacao_zoneamento,
                cd_numero_legislacao_zoneamento,
                an_legislacao_zoneamento,
                cd_zoneamento_perimetro,
                tx_zoneamento_perimetro,
                cd_identificador,
                tx_observacao_perimetro,
                dt_atualizacao,
                cd_usuario_atualizacao,
                ST_AsText(geometry) as geometry_wkt
            FROM
                `{self.project_id}.{self.bigquery_dataset}.{self.bigquery_table}`
            """

            # Configurar job
            job_config = bigquery.QueryJobConfig(
                use_query_cache=False,
                use_legacy_sql=False,
            )

            # Executar query
            query_job = self.bq_client.query(query, job_config=job_config)
            df = query_job.to_dataframe()

            elapsed_time = time.time() - start_time

            # Log de performance
            bytes_processed = (
                query_job.total_bytes_processed if query_job.total_bytes_processed else 0
            )

            logger.success(
                f"✅ Query executada com sucesso | "
                f"Linhas: {len(df):,} | "
                f"Tempo: {elapsed_time:.2f}s | "
                f"Bytes processados: {bytes_processed:,}"
            )

            return df

        except Exception as e:
            logger.error(f"❌ Erro ao executar query BigQuery: {e}")
            return None

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara DataFrame para inserção no PostGIS.

        Args:
            df: DataFrame bruto do BigQuery

        Returns:
            DataFrame preparado
        """
        logger.info("Preparando dados para inserção...")

        # Renomear coluna 'id' para 'id_original' para evitar conflito com PK auto-increment
        df = df.rename(columns={"id": "id_original"})

        # Converter geometria WKT para GeoAlchemy2 WKTElement
        logger.info("Convertendo geometrias WKT para PostGIS...")

        # Função para converter POLYGON em MULTIPOLYGON
        def to_multipolygon_wkt(wkt):
            if wkt.startswith("MULTIPOLYGON"):
                return wkt
            elif wkt.startswith("POLYGON"):
                # Envolve o polígono em MULTIPOLYGON
                coords = wkt[7:]  # Remove "POLYGON"
                return f"MULTIPOLYGON({coords})"
            return wkt

        df["geometry"] = df["geometry_wkt"].apply(
            lambda wkt: WKTElement(to_multipolygon_wkt(wkt), srid=4326)
        )
        df = df.drop("geometry_wkt", axis=1)

        # Converter data_atualizacao para datetime (se não for None)
        if "dt_atualizacao" in df.columns:
            df["dt_atualizacao"] = pd.to_datetime(df["dt_atualizacao"], errors="coerce")

        # Adicionar metadados de carga
        df["data_source"] = "BIGQUERY_SP_ZONEAMENTO"

        # Tratar valores nulos
        df = df.fillna({
            "tx_observacao_perimetro": "",
            "cd_identificador": "",
            "cd_usuario_atualizacao": "",
        })

        logger.info(f"Dados preparados | Linhas: {len(df):,} | Colunas: {list(df.columns)}")
        return df

    def _insert_to_postgres(self, df: pd.DataFrame, table_name: str = "zoneamento_sp") -> bool:
        """
        Insere dados no PostgreSQL em chunks.

        Args:
            df: DataFrame para inserir
            table_name: Nome da tabela destino

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            from geoalchemy2 import Geometry

            logger.info(f"Iniciando inserção no PostgreSQL | Tabela: geo.{table_name}")
            start_time = time.time()

            # Inserir em chunks para melhor performance
            total_chunks = (len(df) // self.chunk_size) + 1

            for i, chunk_start in enumerate(range(0, len(df), self.chunk_size)):
                chunk_end = min(chunk_start + self.chunk_size, len(df))
                chunk = df.iloc[chunk_start:chunk_end]

                # Primeira iteração: replace (limpa tabela)
                # Demais: append
                if_exists_mode = "replace" if i == 0 else "append"

                chunk.to_sql(
                    table_name,
                    self.pg_engine,
                    schema="geo",
                    if_exists=if_exists_mode,
                    index=False,
                    method="multi",
                    chunksize=1000,
                    dtype={"geometry": Geometry("MULTIPOLYGON", srid=4326)},
                )

                logger.info(
                    f"Chunk {i+1}/{total_chunks} inserido | "
                    f"Linhas: {len(chunk)} | "
                    f"Progresso: {(chunk_end/len(df)*100):.1f}%"
                )

            elapsed_time = time.time() - start_time
            logger.success(
                f"✅ Inserção concluída | "
                f"Total de linhas: {len(df):,} | "
                f"Tempo: {elapsed_time:.2f}s | "
                f"Taxa: {len(df)/elapsed_time:.0f} linhas/s"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao inserir dados no PostgreSQL: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _create_indexes(self, table_name: str = "zoneamento_sp") -> bool:
        """Cria índices na tabela para otimizar consultas."""
        try:
            logger.info("Criando índices...")

            with self.pg_engine.connect() as conn:
                # Índice espacial (PostGIS cria automaticamente com GIST)
                conn.execute(
                    text(
                        f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_geometry
                    ON geo.{table_name} USING GIST (geometry)
                """
                    )
                )

                # Índice por código de zoneamento
                conn.execute(
                    text(
                        f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_codigo
                    ON geo.{table_name} (cd_zoneamento_perimetro)
                """
                    )
                )

                # Índice por ano da legislação
                conn.execute(
                    text(
                        f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_ano
                    ON geo.{table_name} (an_legislacao_zoneamento)
                """
                    )
                )

                # Índice por id_original
                conn.execute(
                    text(
                        f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_id_original
                    ON geo.{table_name} (id_original)
                """
                    )
                )

                conn.commit()

            logger.success("✅ Índices criados com sucesso")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar índices (não crítico): {e}")
            return False

    def run(self) -> bool:
        """
        Executa a pipeline ETL completa.

        Returns:
            True se sucesso, False caso contrário
        """
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO PIPELINE ETL ZONEAMENTO SP (BigQuery → PostGIS)")
        logger.info("=" * 80)

        pipeline_start = time.time()

        try:
            # 1. Validar credenciais
            if not self._validate_credentials():
                return False

            # 2. Conectar BigQuery
            if not self._connect_bigquery():
                return False

            # 3. Conectar PostgreSQL
            if not self._connect_postgres():
                return False

            # 4. Executar query BigQuery
            df = self._execute_bigquery()
            if df is None or df.empty:
                logger.warning("⚠️ Nenhum dado retornado do BigQuery")
                return False

            # 5. Preparar dados
            df_prepared = self._prepare_dataframe(df)

            # 6. Inserir no PostgreSQL
            if not self._insert_to_postgres(df_prepared):
                return False

            # 7. Criar índices
            self._create_indexes()

            # Sucesso!
            total_time = time.time() - pipeline_start
            logger.success("=" * 80)
            logger.success(f"✅ PIPELINE CONCLUÍDA COM SUCESSO | Tempo total: {total_time:.2f}s")
            logger.success("=" * 80)

            return True

        except Exception as e:
            logger.critical(f"❌ ERRO CRÍTICO NA PIPELINE: {e}", exc_info=True)
            return False


def main():
    """Função principal."""
    # Carregar variáveis de ambiente
    project_id = os.getenv("GCP_PROJECT_ID", "causal-tracker-484821-f1")
    database_url = os.getenv("DATABASE_URL")

    # ⚠️ IMPORTANTE: Substitua pelos nomes reais do seu BigQuery
    bigquery_dataset = os.getenv("BIGQUERY_DATASET", "SEU_DATASET_AQUI")
    bigquery_table = os.getenv("BIGQUERY_TABLE", "SUA_TABELA_CURADA_AQUI")

    chunk_size = int(os.getenv("ETL_CHUNK_SIZE", "5000"))

    # Validações
    if not database_url:
        logger.error("DATABASE_URL não configurada!")
        sys.exit(1)

    if bigquery_dataset == "SEU_DATASET_AQUI" or bigquery_table == "SUA_TABELA_CURADA_AQUI":
        logger.error("⚠️ Configure BIGQUERY_DATASET e BIGQUERY_TABLE no .env ou nas variáveis de ambiente!")
        logger.error("Exemplo no .env:")
        logger.error("  BIGQUERY_DATASET=zoneamento_sp")
        logger.error("  BIGQUERY_TABLE=zoneamento_curado")
        sys.exit(1)

    logger.info(f"Configurações:")
    logger.info(f"  Projeto GCP: {project_id}")
    logger.info(f"  Dataset: {bigquery_dataset}")
    logger.info(f"  Tabela: {bigquery_table}")
    logger.info(f"  Chunk size: {chunk_size}")

    # Criar e executar pipeline
    pipeline = ZoneamentoSPETL(
        project_id=project_id,
        database_url=database_url,
        bigquery_dataset=bigquery_dataset,
        bigquery_table=bigquery_table,
        chunk_size=chunk_size,
    )

    success = pipeline.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
