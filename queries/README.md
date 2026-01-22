# Pipeline ETL BigQuery - Quick Start

## 📦 Arquivos Criados

```
DataZone Energy/
├── docker/
│   ├── Dockerfile.pipeline          # Container ETL otimizado
│   └── requirements-pipeline.txt    # Dependências BigQuery
├── queries/
│   └── extrair_fibra.sql           # Query otimizada (FTTH/FTTB)
├── scripts/
│   ├── extrair_anatel.py           # Script ETL refatorado
│   └── init_cobertura_fibra.sql    # Schema da tabela
├── docs/
│   └── ETL_PIPELINE.md             # Documentação completa
├── secrets/                         # (criar e adicionar chave JSON)
│   └── gcp-service-account.json    # Chave de autenticação GCP
├── docker-compose.yml              # Atualizado com serviço pipeline_etl
└── .env.example                    # Atualizado com vars BigQuery
```

## 🚀 Próximos Passos

### 1. Criar Tabela no PostGIS

```bash
# Executar script de criação da tabela
docker-compose exec postgis psql -U datazone_user -d datazone_energy -f /app/scripts/init_cobertura_fibra.sql
```

### 2. Configurar Chave GCP

```bash
# Copiar sua chave JSON para o diretório secrets/
cp ~/Downloads/sua-chave-gcp.json secrets/gcp-service-account.json
```

### 3. Build do Container

```bash
docker-compose build pipeline_etl
```

### 4. Executar Pipeline

```bash
docker-compose --profile etl run --rm pipeline_etl
```

## 📖 Documentação Completa

Consulte `docs/ETL_PIPELINE.md` para:
- Setup detalhado de autenticação GCP
- Monitoramento e logs
- Troubleshooting
- Performance tuning
- Manutenção

## 🔐 Segurança

- ✅ Chave JSON protegida no `.gitignore`
- ✅ Volume montado como read-only
- ✅ Credenciais via variáveis de ambiente
- ✅ Conexão PostGIS via rede interna Docker

## 📊 Características

- **Otimização**: Agregação no BigQuery reduz ~95% do tráfego
- **Performance**: Processamento em chunks (lazy loading)
- **Resiliência**: Retry automático em falhas de rede
- **Observabilidade**: Logs estruturados com métricas
- **Governança**: Queries versionadas em SQL
