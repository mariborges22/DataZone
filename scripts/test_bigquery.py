"""
Script de teste para validar conexão BigQuery
==============================================
Testa se o cliente BigQuery consegue acessar tabelas do projeto público
basedosdados usando o projeto causal-tracker-484821-f1 para billing.
"""

import os

from google.cloud import bigquery

# Configurar credenciais
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/secrets/gpc-service-account.json"


def test_bigquery_connection():
    """Testa conexão com BigQuery e acesso ao projeto público basedosdados."""

    print("=" * 80)
    print("TESTE DE CONEXÃO BIGQUERY")
    print("=" * 80)

    # 1. Criar cliente (billing no seu projeto)
    print("\n1. Criando cliente BigQuery...")
    client = bigquery.Client(project="causal-tracker-484821-f1")
    print(f"   ✅ Cliente criado | Projeto de billing: {client.project}")

    # 2. Teste simples
    print("\n2. Testando query simples...")
    query_test = "SELECT 1 as test"
    job = client.query(query_test)
    result = job.result()
    print(f"   ✅ Query executada | Job ID: {job.job_id}")

    # 3. Testar acesso ao projeto público basedosdados
    print("\n3. Testando acesso ao projeto público basedosdados...")

    # Query que acessa EXPLICITAMENTE o projeto basedosdados
    query_basedosdados = """
    SELECT 
        ano,
        COUNT(*) as total_registros
    FROM 
        `basedosdados.br_anatel_banda_larga_fixa.microdados`
    WHERE 
        ano = 2023
        AND tecnologia IN ('FTTH', 'FTTB')
    GROUP BY ano
    LIMIT 1
    """

    print("   Executando query no projeto basedosdados...")
    job_config = bigquery.QueryJobConfig(use_query_cache=False)
    job = client.query(query_basedosdados, job_config=job_config)

    # Aguardar resultado
    df = job.to_dataframe()

    print(f"   ✅ Query executada com sucesso!")
    print(f"   📊 Resultados encontrados:")
    print(df.to_string(index=False))
    print(f"\n   📈 Métricas:")
    bytes_processed = job.total_bytes_processed if job.total_bytes_processed is not None else 0
    print(f"      - Bytes processados: {bytes_processed:,}")
    print(f"      - Tempo de execução: {job.ended - job.started}")
    print(f"      - Job criado em: {job.project}")

    # 4. Listar datasets do projeto basedosdados (opcional)
    print("\n4. Listando alguns datasets do projeto basedosdados...")
    try:
        datasets = list(client.list_datasets(project="basedosdados", max_results=5))
        if datasets:
            print("   Datasets encontrados:")
            for dataset in datasets:
                print(f"      - {dataset.dataset_id}")
        else:
            print("   ⚠️ Nenhum dataset listado (pode ser limitação de permissões)")
    except Exception as e:
        print(f"   ⚠️ Não foi possível listar datasets: {e}")

    print("\n" + "=" * 80)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 80)
    print("\n📝 Resumo:")
    print("   - Cliente BigQuery: ✅ Conectado")
    print("   - Projeto de billing: causal-tracker-484821-f1")
    print("   - Acesso ao basedosdados: ✅ Funcionando")
    print("   - Tabela testada: basedosdados.br_anatel_banda_larga_fixa.microdados")
    print("\n🎯 Próximo passo: Execute python scripts/extrair_anatel.py")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_bigquery_connection()
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ERRO NO TESTE")
        print("=" * 80)
        print(f"\nErro: {e}")
        print("\nVerifique:")
        print("1. Arquivo de credenciais existe: /secrets/gpc-service-account.json")
        print("2. Service Account tem permissões: BigQuery Data Viewer, BigQuery Job User")
        print("3. Projeto causal-tracker-484821-f1 tem billing habilitado")
        import traceback

        traceback.print_exc()
