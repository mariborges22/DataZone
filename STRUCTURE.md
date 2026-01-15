# DataZone Energy - Estrutura de Diretórios

## Visão Geral
Este documento descreve a estrutura de diretórios do projeto DataZone Energy.

## Estrutura

```
DataZone Energy/
├── app/                          # Código da aplicação
│   ├── __init__.py
│   ├── main.py                   # Ponto de entrada FastAPI
│   ├── config.py                 # Configurações e variáveis de ambiente
│   ├── api/                      # Endpoints da API
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── subestacoes.py
│   │   │   │   ├── linhas.py
│   │   │   │   └── fibra.py
│   │   │   └── router.py
│   ├── core/                     # Funcionalidades core
│   │   ├── __init__.py
│   │   ├── database.py           # Conexão com banco
│   │   ├── security.py           # Autenticação e segurança
│   │   └── logging.py            # Configuração de logs
│   ├── models/                   # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── subestacao.py
│   │   ├── linha_transmissao.py
│   │   └── fibra_optica.py
│   ├── schemas/                  # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── subestacao.py
│   │   ├── linha_transmissao.py
│   │   └── fibra_optica.py
│   ├── services/                 # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── geo_service.py
│   │   └── data_processor.py
│   └── utils/                    # Utilitários
│       ├── __init__.py
│       ├── geo_utils.py
│       └── validators.py
├── scripts/                      # Scripts de processamento
│   ├── init_db.sql              # Inicialização do banco
│   ├── process_aneel_data.py    # Processar dados ANEEL
│   └── process_anatel_data.py   # Processar dados ANATEL
├── data/                         # Dados (não versionados)
│   ├── raw/                      # Dados brutos
│   │   ├── .gitkeep
│   │   └── README.md
│   └── processed/                # Dados processados
│       ├── .gitkeep
│       └── README.md
├── tests/                        # Testes
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   └── test_services/
├── logs/                         # Logs (não versionados)
│   └── .gitkeep
├── backups/                      # Backups do banco (não versionados)
│   └── .gitkeep
├── .github/                      # GitHub Actions
│   └── workflows/
│       └── deploy.yml
├── Dockerfile                    # Imagem Docker da aplicação
├── docker-compose.yml            # Orquestração de containers
├── requirements.txt              # Dependências Python
├── .env.example                  # Template de variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
└── README.md                     # Documentação principal
```

## Próximos Passos
1. Criar estrutura de diretórios
2. Implementar configuração base da aplicação
3. Desenvolver modelos e schemas
4. Criar endpoints da API
