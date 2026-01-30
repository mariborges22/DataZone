# Zoneamento SP - Quick Start

## 1. Configurar .env

```bash
BIGQUERY_DATASET=seu_dataset        # ⚠️ SUBSTITUA
BIGQUERY_TABLE=sua_tabela_curada    # ⚠️ SUBSTITUA
DATABASE_URL=postgresql://...
```

## 2. Criar tabela e popular

```bash
# Cria tabela e popula do BigQuery
python scripts/extrair_sao_paulo_municipio.py
```

## 3. Usar API

**Iniciar:**
```bash
uvicorn app.main:app --reload
```

**Endpoints:**
```bash
# Listar todos
GET /api/v1/zoneamento-sp

# Filtrar por tipo
GET /api/v1/zoneamento-sp?cd_zoneamento_perimetro=ZEPAM

# Filtrar por área (bbox)
GET /api/v1/zoneamento-sp?bbox=-46.65,-23.60,-46.60,-23.55

# Buscar por ID
GET /api/v1/zoneamento-sp/123

# Estatísticas
GET /api/v1/zoneamento-sp/stats/summary
```

**Docs:** `http://localhost:8000/docs`

## Arquivos criados

- `app/models/zoneamento_sp.py` - Modelo PostGIS
- `app/schemas/zoneamento_sp.py` - Schemas Pydantic
- `app/api/v1/endpoints/zoneamento_sp.py` - Endpoints API
- `scripts/extrair_sao_paulo_municipio.py` - ETL BigQuery→PostGIS

## Dica importante

Use `simplify=true` (padrão) e `bbox` para queries rápidas:
```bash
GET /api/v1/zoneamento-sp?bbox=-46.7,-23.6,-46.5,-23.5&simplify=true
```

Pronto! 🚀
