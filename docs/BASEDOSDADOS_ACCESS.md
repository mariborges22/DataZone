# Acesso ao Projeto Público basedosdados

## ✅ Configuração Correta

Seu projeto `causal-tracker-484821-f1` é usado para **billing** (faturamento), mas as queries acessam as tabelas do projeto **público** `basedosdados`.

### Como Funciona

```python
# Cliente BigQuery (billing no seu projeto)
client = bigquery.Client(project='causal-tracker-484821-f1')

# Query acessa EXPLICITAMENTE o projeto basedosdados
query = """
SELECT * 
FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
WHERE ano = 2023
"""

# Job criado em: causal-tracker-484821-f1 (você paga)
# Dados vêm de: basedosdados.br_anatel_banda_larga_fixa.microdados (público)
result = client.query(query)
```

---

## 📋 Sintaxe Correta

**Sempre use a sintaxe completa com 3 partes**:

```sql
`projeto.dataset.tabela`
```

### ✅ Correto (Explícito)
```sql
SELECT * FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
```

### ❌ Errado (Implícito - usa seu projeto vazio)
```sql
SELECT * FROM `br_anatel_banda_larga_fixa.microdados`
```

---

## 🧪 Teste de Conexão

Execute o script de teste:

```bash
# Dentro do container
python scripts/test_bigquery.py
```

**Saída esperada**:
```
✅ Cliente criado | Projeto de billing: causal-tracker-484821-f1
✅ Query executada | Job ID: xxx
✅ Query executada com sucesso!
📊 Resultados encontrados:
   ano  total_registros
  2023         1234567
```

---

## 📁 Arquivos Verificados

### ✅ `queries/extrair_fibra.sql`
```sql
-- CORRETO: Usa sintaxe explícita
FROM `basedosdados.br_anatel_banda_larga_fixa.microdados`
```

### ✅ `scripts/extrair_anatel.py`
```python
# CORRETO: Cliente usa seu projeto para billing
self.bq_client = bigquery.Client(project='causal-tracker-484821-f1')

# Query (do arquivo .sql) acessa basedosdados explicitamente
```

---

## 🔍 Troubleshooting

### Problema: "Table not found"

**Causa**: Query não está usando sintaxe explícita

**Solução**: Sempre use `basedosdados.dataset.tabela`

### Problema: "Access Denied"

**Causa**: Service Account sem permissões

**Solução**: Adicionar roles no GCP Console:
- `BigQuery Data Viewer`
- `BigQuery Job User`

### Problema: "Billing not enabled"

**Causa**: Projeto `causal-tracker-484821-f1` sem billing

**Solução**: Habilitar billing no GCP Console

---

## 🎯 Validação Final

```bash
# 1. Teste de conexão
python scripts/test_bigquery.py

# 2. Pipeline completa
python scripts/extrair_anatel.py
```

**Tudo funcionando?** Você verá:
```
✅ Conectado ao BigQuery | Projeto faturador: causal-tracker-484821-f1
✅ Query executada com sucesso | Linhas: X,XXX | Bytes processados: XX,XXX,XXX
```

---

## 📚 Referências

- [BigQuery Public Datasets](https://cloud.google.com/bigquery/public-data)
- [Base dos Dados](https://basedosdados.org/)
- [BigQuery Billing](https://cloud.google.com/bigquery/pricing)
