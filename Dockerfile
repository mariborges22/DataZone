# Base image com Python 3.11 e suporte a bibliotecas GIS
FROM python:3.11-slim-bullseye

# Metadados
LABEL maintainer="DataZone Energy Team"
LABEL description="Backend API para plataforma de inteligência geográfica"

# Variáveis de ambiente para otimização
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema para bibliotecas GIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Bibliotecas GIS essenciais
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    python3-gdal \
    # Ferramentas de build
    gcc \
    g++ \
    make \
    python3-dev \
    # Bibliotecas PostgreSQL
    libpq-dev \
    postgresql-client \
    # Utilitários
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configurar variáveis de ambiente para GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (melhor cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para dados temporários
RUN mkdir -p /app/data/raw /app/data/processed /app/logs

# Expor porta da API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão (pode ser sobrescrito no docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
