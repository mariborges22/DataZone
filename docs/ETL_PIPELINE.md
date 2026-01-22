# Pipeline ETL BigQuery → PostGIS

Documentação completa da pipeline de extração de dados da Anatel (BigQuery) para o PostGIS.

---

## 📋 Visão Geral

Esta pipeline ETL extrai dados de cobertura de fibra óptica (FTTH/FTTB) do projeto **Base dos Dados** no BigQuery e carrega no banco PostGIS local, otimizada para evitar estouro de memória.

**Fonte de Dados**: `basedosdados.br_anatel_banda_larga_fixa.microdados`

**Otimizações**:
- ✅ Agregação server-side no BigQuery (reduz ~95% do tráfego)
- ✅ Processamento em chunks (lazy loading)
- ✅ Inserção batch otimizada no PostgreSQL
- ✅ Retry automático em caso de falhas de rede
- ✅ Logs estruturados com métricas de performance

---

## 🔐 Setup Inicial: Autenticação Google Cloud

### 1. Criar Service Account no GCP

```bash
# 1. Acesse o Google Cloud Console
https://console.cloud.google.com/

# 2. Navegue para: IAM & Admin > Service Accounts

# 3. Clique em "Create Service Account"
#    - Nome: datazone-bigquery-reader
#    - Descrição: Service Account para leitura BigQuery (DataZone Energy)

# 4. Conceder permissões:
#    - BigQuery Data Viewer
#    - BigQuery Job User

# 5. Criar chave JSON:
#    - Clique na Service Account criada
#    - Aba "Keys" > "Add Key" > "Create new key"
#    - Tipo: JSON
#    - Baixar arquivo
```

### 2. Configurar Chave Localmente

```bash
# Copiar chave JSON para o diretório secrets/
cp ~/Downloads/datazone-bigquery-*.json secrets/gcp-service-account.json

# Verificar permissões (read-only recomendado)
chmod 400 secrets/gcp-service-account.json
```

### 3. Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar .env e verificar:
GCP_PROJECT_ID=basedosdados
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-service-account.json
```

---

## 🚀 Execução da Pipeline

### Método 1: Docker Compose (Recomendado)

```bash
# 1. Build do container (primeira vez ou após mudanças)
docker-compose build pipeline_etl

# 2. Executar pipeline
docker-compose --profile etl run --rm pipeline_etl

# 3. Verificar logs em tempo real
tail -f logs/etl_anatel_*.log
```

### Método 2: Execução Direta (Desenvolvimento)

```bash
# Dentro do container
docker-compose --profile etl run --rm pipeline_etl bash

# Executar script manualmente
python scripts/extrair_anatel.py
```

### Método 3: Agendamento (Produção)

```bash
# Adicionar ao crontab para execução diária às 2h da manhã
0 2 * * * cd /path/to/datazone && docker-compose --profile etl run --rm pipeline_etl >> logs/cron.log 2>&1
```

---

## 📊 Monitoramento

### Logs Estruturados

A pipeline gera logs em dois formatos:

1. **Console (stdout)**: Colorido, para acompanhamento em tempo real
2. **Arquivo**: JSON estruturado em `logs/etl_anatel_YYYY-MM-DD.log`

**Exemplo de log**:
```
2026-01-20 16:00:00 | INFO     | Pipeline ETL inicializada | Projeto: basedosdados | Chunk Size: 10000
2026-01-20 16:00:05 | SUCCESS  | ✅ Conectado ao BigQuery | Projeto: basedosdados
2026-01-20 16:00:06 | SUCCESS  | ✅ Conectado ao PostGIS | Versão: 3.3
2026-01-20 16:00:10 | SUCCESS  | ✅ Query executada com sucesso | Linhas: 5,432 | Tempo: 3.45s | Bytes processados: 12,345,678
2026-01-20 16:00:25 | SUCCESS  | ✅ Inserção concluída | Total de linhas: 5,432 | Tempo: 15.23s | Taxa: 356 linhas/s
2026-01-20 16:00:26 | SUCCESS  | ✅ PIPELINE CONCLUÍDA COM SUCESSO | Tempo total: 26.12s
```

### Métricas Importantes

- **Linhas processadas**: Total de registros extraídos do BigQuery
- **Bytes processados**: Volume de dados trafegados (BigQuery)
- **Tempo de execução**: Duração total da pipeline
- **Taxa de inserção**: Linhas/segundo no PostgreSQL

### Verificar Dados no PostGIS

```sql
-- Conectar ao banco
docker-compose exec postgis psql -U datazone_user -d datazone_energy

-- Verificar total de registros
SELECT COUNT(*) FROM geo.cobertura_fibra;

-- Estatísticas por UF
SELECT 
    uf,
    COUNT(*) as total_registros,
    SUM(total_acessos) as total_acessos,
    AVG(velocidade_media_mbps) as velocidade_media
FROM geo.cobertura_fibra
GROUP BY uf
ORDER BY total_acessos DESC;

-- Top 10 municípios com maior cobertura
SELECT 
    municipio,
    uf,
    tecnologia,
    total_acessos,
    total_operadoras,
    velocidade_media_mbps
FROM geo.cobertura_fibra
ORDER BY total_acessos DESC
LIMIT 10;
```

---

## 🔧 Troubleshooting

### Erro: "GOOGLE_APPLICATION_CREDENTIALS não configurada"

**Causa**: Variável de ambiente não definida ou chave JSON não encontrada.

**Solução**:
```bash
# Verificar se arquivo existe
ls -la secrets/gcp-service-account.json

# Verificar variável no .env
grep GOOGLE_APPLICATION_CREDENTIALS .env

# Recriar container
docker-compose build pipeline_etl
```

### Erro: "Permission denied" ao acessar BigQuery

**Causa**: Service Account sem permissões adequadas.

**Solução**:
1. Acesse GCP Console > IAM & Admin
2. Localize a Service Account
3. Adicione roles:
   - `BigQuery Data Viewer`
   - `BigQuery Job User`

### Erro: "Connection refused" ao conectar PostgreSQL

**Causa**: Container PostGIS não está rodando ou não passou no healthcheck.

**Solução**:
```bash
# Verificar status dos containers
docker-compose ps

# Verificar logs do PostGIS
docker-compose logs postgis

# Reiniciar PostGIS
docker-compose restart postgis

# Aguardar healthcheck (10-30 segundos)
docker-compose ps | grep postgis
```

### Erro: "Out of memory" durante processamento

**Causa**: Chunk size muito grande para memória disponível.

**Solução**:
```bash
# Reduzir chunk size no .env
ETL_CHUNK_SIZE=5000  # Padrão: 10000

# Ou passar diretamente
docker-compose --profile etl run --rm -e ETL_CHUNK_SIZE=5000 pipeline_etl
```

### Query BigQuery muito lenta

**Causa**: Tabela `basedosdados` pode estar com alta carga.

**Solução**:
- Executar em horários de menor uso (madrugada)
- Verificar status do BigQuery: https://status.cloud.google.com/

---

## 🛠️ Manutenção

### Atualizar Query BigQuery

1. Editar arquivo `queries/extrair_fibra.sql`
2. Testar query no BigQuery Console
3. Rebuild container:
   ```bash
   docker-compose build pipeline_etl
   ```

### Adicionar Novas Fontes de Dados

1. Criar nova query em `queries/extrair_<fonte>.sql`
2. Duplicar `scripts/extrair_anatel.py` como `scripts/extrair_<fonte>.py`
3. Ajustar mapeamento de colunas e tabela destino
4. Adicionar ao `docker-compose.yml` (opcional: novo serviço)

### Backup dos Dados

```bash
# Exportar tabela para CSV
docker-compose exec postgis psql -U datazone_user -d datazone_energy -c "\COPY geo.cobertura_fibra TO '/backups/cobertura_fibra.csv' CSV HEADER"

# Dump completo do schema geo
docker-compose exec postgis pg_dump -U datazone_user -d datazone_energy -n geo > backups/geo_schema_$(date +%Y%m%d).sql
```

---

## 📈 Performance Tuning

### Otimizações Aplicadas

1. **BigQuery**:
   - Agregação server-side (GROUP BY no SQL)
   - Filtros aplicados antes da transferência
   - Cache de queries habilitado

2. **Rede**:
   - Processamento em chunks (evita timeout)
   - Compressão automática (gzip)

3. **PostgreSQL**:
   - Inserção batch (`method='multi'`)
   - Índices criados após inserção (mais rápido)
   - Transações otimizadas

4. **Memória**:
   - Lazy loading (não carrega tudo na RAM)
   - Garbage collection automático entre chunks

### Benchmarks Esperados

| Métrica | Valor Típico |
|---------|--------------|
| Tempo total | 20-60 segundos |
| Taxa de inserção | 300-500 linhas/s |
| Uso de memória | < 1GB |
| Bytes processados (BigQuery) | 10-50 MB |

---

## 🔒 Segurança

### Checklist de Segurança

- ✅ Chave JSON nunca commitada no Git (`.gitignore`)
- ✅ Volume montado como read-only (`:ro`)
- ✅ Credenciais via variáveis de ambiente
- ✅ Conexão PostGIS via rede interna Docker
- ✅ Limites de recursos configurados (prevenção DoS)
- ✅ Logs não contêm dados sensíveis

### Rotação de Credenciais

```bash
# 1. Criar nova Service Account no GCP
# 2. Baixar nova chave JSON
# 3. Substituir arquivo
mv secrets/gcp-service-account.json secrets/gcp-service-account.json.old
cp ~/Downloads/nova-chave.json secrets/gcp-service-account.json

# 4. Testar
docker-compose --profile etl run --rm pipeline_etl

# 5. Deletar chave antiga no GCP Console
# 6. Remover arquivo local
rm secrets/gcp-service-account.json.old
```

---

## 📚 Referências

- [Base dos Dados - Documentação](https://basedosdados.org/)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [Docker Compose Profiles](https://docs.docker.com/compose/profiles/)

---

## 🆘 Suporte

Em caso de dúvidas ou problemas:

1. Verificar logs: `tail -f logs/etl_anatel_*.log`
2. Consultar esta documentação
3. Abrir issue no repositório do projeto
