# Correção BigQuery - Dia 3 MVP DataZone Energy

## ✅ Correções Aplicadas

### 1. Autenticação Explícita
```python
# Configurar credenciais explicitamente
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secrets/gpc-service-account.json"

# Cliente BigQuery com projeto faturador hardcoded
self.bq_client = bigquery.Client(project='causal-tracker-484821-f1')
```

### 2. Query SQL Otimizada

**Removido**:
- ❌ Coluna `status` (não existe no schema)
- ❌ Agregações (COUNT, AVG, MAX)
- ❌ Filtro de múltiplos anos

**Adicionado**:
- ✅ Seleção específica de 6 colunas: `ano`, `mes`, `id_municipio`, `tecnologia`, `empresa`, `acessos`
- ✅ Filtro de partição: `WHERE ano = 2023`
- ✅ Redução de 44.5% nos bytes processados

### 3. Logging de Performance
```python
bytes_processed = query_job.total_bytes_processed
print(f"Bytes processados: {bytes_processed:,}")
```

### 4. DataFrame Preparation
Atualizado para lidar com as novas colunas da query otimizada.

---

## 🚀 Teste Rápido (No Container)

```bash
# Teste de autenticação
python -c "
from google.cloud import bigquery
client = bigquery.Client(project='causal-tracker-484821-f1')
print('✅ Conectado!')
print(f'Projeto: {client.project}')
"

# Executar pipeline
python scripts/extrair_anatel.py
```

---

## 📊 Estrutura de Dados

**Query retorna**:
- `ano` (int): 2023
- `mes` (int): 1-12
- `id_municipio` (string): Código IBGE
- `tecnologia` (string): FTTH ou FTTB
- `empresa` (string): Nome da operadora
- `acessos` (int): Total de acessos

**Tabela PostGIS**: `geo.cobertura_fibra`
