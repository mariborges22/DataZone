# DataZone Energy

**Plataforma de Inteligência Geográfica para Site Selection de Data Centers**

## 🎯 Objetivo
MVP para o cliente Canal Solar: sistema de análise geoespacial que integra dados de infraestrutura energética (ANEEL) e telecomunicações (ANATEL) para identificar localizações ideais para instalação de Data Centers.

## 🚀 Stack Tecnológica

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Banco de Dados**: PostgreSQL 15 + PostGIS 3.3
- **Processamento GIS**: GeoPandas, Shapely, Fiona
- **ORM**: SQLAlchemy + GeoAlchemy2
- **Servidor**: Uvicorn

### Infraestrutura
- **Containerização**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deploy**: Railway (backend) + Vercel (frontend)
- **Monitoramento**: Logs estruturados com Loguru

## 📦 Início Rápido

### Pré-requisitos
- Docker Desktop instalado
- Git
- 4GB RAM disponível

### 1. Clonar e Configurar

```bash
# Clonar o repositório
git clone <repository-url>
cd "DataZone Energy"

# Copiar variáveis de ambiente
cp .env.example .env

# Editar .env com suas configurações (opcional para desenvolvimento)
```

### 2. Iniciar Ambiente

```bash
# Construir e iniciar containers
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f api
```

### 3. Acessar Aplicação

- **API**: http://localhost:8000
- **Documentação Interativa**: http://localhost:8000/docs
- **PgAdmin** (opcional): http://localhost:5050

### 4. Verificar Saúde

```bash
# Health check
curl http://localhost:8000/health

# Verificar PostGIS
docker-compose exec postgis psql -U datazone_user -d datazone_energy -c "SELECT PostGIS_Version();"
```

## 📁 Estrutura do Projeto

```
DataZone Energy/
├── app/                    # Código da aplicação FastAPI
├── scripts/                # Scripts de processamento de dados
├── data/                   # Dados brutos e processados (não versionado)
├── tests/                  # Testes automatizados
├── Dockerfile              # Imagem Docker
├── docker-compose.yml      # Orquestração
└── requirements.txt        # Dependências Python
```

Ver [STRUCTURE.md](STRUCTURE.md) para detalhes completos.

## 🗺️ Roadmap MVP (10 dias)

### Dias 1-3: Processamento de Dados
- [ ] Extrair subestações de arquivos .gdb (ANEEL)
- [ ] Extrair linhas de transmissão (ANEEL)
- [ ] Processar dados de fibra ótica (ANATEL)
- [ ] Converter CRS para EPSG:4326
- [ ] Carregar dados no PostGIS

### Dia 4: API
- [ ] Endpoint `/api/v1/subestacoes` (GeoJSON)
- [ ] Endpoint `/api/v1/linhas` (GeoJSON)
- [ ] Endpoint `/api/v1/fibra` (GeoJSON)
- [ ] Filtros geográficos (bbox, raio)
- [ ] Otimização com ST_Simplify

### Dia 5: DevOps
- [ ] GitHub Actions workflow
- [ ] Deploy automático no Railway
- [ ] Variáveis de ambiente seguras
- [ ] Monitoramento básico

### Dias 6-10: Integração e Testes
- [ ] Integração com frontend React
- [ ] Testes de carga
- [ ] Documentação
- [ ] Ajustes finais

## 🔧 Comandos Úteis

### Docker

```bash
# Parar containers
docker-compose down

# Reconstruir após mudanças
docker-compose up -d --build

# Limpar volumes (CUIDADO: apaga dados)
docker-compose down -v

# Acessar shell do container
docker-compose exec api bash
docker-compose exec postgis psql -U datazone_user -d datazone_energy
```

### Desenvolvimento

```bash
# Instalar dependências localmente (opcional)
pip install -r requirements.txt

# Executar testes
docker-compose exec api pytest

# Formatar código
docker-compose exec api black app/
docker-compose exec api isort app/
```

## 🔐 Segurança

- **Nunca** commitar o arquivo `.env`
- Gerar `SECRET_KEY` segura em produção: `openssl rand -hex 32`
- Frontend **nunca** acessa banco diretamente
- Todas as comunicações via API REST (GeoJSON)

## 📊 Otimizações de Performance

1. **Simplificação de Geometrias**: `ST_Simplify` para reduzir tráfego
2. **Índices Espaciais**: GIST indexes em todas as colunas geometry
3. **Cache**: Redis para queries frequentes (opcional)
4. **Paginação**: Limitar resultados por request
5. **Compressão**: GZIP nas respostas da API

## 🐛 Troubleshooting

### PostGIS não inicia
```bash
docker-compose logs postgis
# Verificar se a porta 5432 está livre
```

### Erro de permissão em volumes
```bash
# Windows: executar Docker Desktop como administrador
```

### GDAL não encontrado
```bash
# Reconstruir imagem
docker-compose build --no-cache api
```

## 📚 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [PostGIS Manual](https://postgis.net/documentation/)
- [GeoPandas Guide](https://geopandas.org/)
- [Railway Docs](https://docs.railway.app/)

## 👥 Equipe

- **Backend Sênior**: Desenvolvimento da API e processamento GIS
- **Cliente**: Canal Solar

## 📝 Licença

Proprietary - DataZone Energy © 2024

---

**Status**: 🚧 Em Desenvolvimento - MVP Fase 1
