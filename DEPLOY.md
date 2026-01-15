# 🚀 Guia de Deploy - DataZone Energy

## Pré-requisitos

1. **Conta no Railway**: https://railway.app
2. **Conta no GitHub**: Repositório criado
3. **Conta no Sentry** (opcional): https://sentry.io

---

## 📋 Passo a Passo: Setup Inicial

### 1. Preparar Repositório GitHub

```bash
# Inicializar Git (se ainda não fez)
git init
git add .
git commit -m "Initial commit"

# Criar repositório no GitHub e conectar
git remote add origin https://github.com/seu-usuario/datazone-energy.git
git branch -M main
git push -u origin main

# Criar branches
git checkout -b staging
git push -u origin staging

git checkout -b develop
git push -u origin develop
```

### 2. Configurar Railway

#### A. Criar Projeto

1. Acesse https://railway.app
2. Clique em "New Project"
3. Escolha "Deploy from GitHub repo"
4. Selecione `datazone-energy`

#### B. Adicionar PostgreSQL

1. No projeto, clique em "+ New"
2. Escolha "Database" → "PostgreSQL"
3. Railway cria automaticamente e fornece `DATABASE_URL`

#### C. Configurar Variáveis de Ambiente (Production)

```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<gerar com: openssl rand -hex 32>
BACKEND_CORS_ORIGINS=["https://seudominio.com"]
LOG_LEVEL=WARNING
SQL_LOGGING=False
```

#### D. Configurar Domínio

1. Settings → Domains
2. Adicionar domínio customizado ou usar `.up.railway.app`

### 3. Configurar GitHub Secrets

No GitHub: Settings → Secrets and variables → Actions

Adicionar:
```
RAILWAY_STAGING_TOKEN    # Token do Railway (Staging)
RAILWAY_PROD_TOKEN       # Token do Railway (Production)
STAGING_URL              # https://staging.up.railway.app
PRODUCTION_URL           # https://api.datazone.com
SLACK_WEBHOOK            # (opcional)
SENTRY_AUTH_TOKEN        # (opcional)
```

**Como obter Railway Token:**
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Obter token
railway whoami
```

---

## 🔄 Workflow de Deploy

### Development → Staging → Production

```
1. Desenvolver em branch 'develop'
   ↓
2. Pull Request para 'staging'
   ↓ (GitHub Actions: test + lint)
3. Merge para 'staging'
   ↓ (GitHub Actions: deploy to staging)
4. Testar em staging
   ↓
5. Pull Request para 'main'
   ↓ (GitHub Actions: test + lint)
6. Merge para 'main'
   ↓ (GitHub Actions: deploy to production)
7. ✅ Em produção!
```

---

## 🧪 Testando o Pipeline

### 1. Testar Deploy para Staging

```bash
# Fazer mudança
echo "# Test" >> README.md

# Commit e push para staging
git checkout staging
git add .
git commit -m "test: CI/CD pipeline"
git push origin staging

# Acompanhar no GitHub Actions
# https://github.com/seu-usuario/datazone-energy/actions
```

### 2. Verificar Deploy

```bash
# Health check
curl https://staging.up.railway.app/health

# Documentação
curl https://staging.up.railway.app/docs
```

---

## 🔧 Comandos Úteis Railway

```bash
# Ver logs em tempo real
railway logs

# Executar comando no container
railway run python scripts/process_data.py

# Ver variáveis de ambiente
railway variables

# Rollback (voltar versão anterior)
railway rollback
```

---

## 📊 Monitoramento

### Sentry (Recomendado)

1. Criar projeto em https://sentry.io
2. Copiar DSN
3. Adicionar ao Railway:
   ```
   SENTRY_DSN=https://xxx@sentry.io/xxx
   ```
4. Instalar SDK:
   ```bash
   pip install sentry-sdk[fastapi]
   ```

### Railway Metrics (Built-in)

- CPU Usage
- Memory Usage
- Network Traffic
- Request Rate

---

## 🚨 Troubleshooting

### Deploy falhou

```bash
# Ver logs do build
railway logs --deployment <deployment-id>

# Verificar variáveis
railway variables
```

### Banco não conecta

```bash
# Verificar DATABASE_URL
railway variables | grep DATABASE_URL

# Testar conexão
railway run python -c "from app.core.database import check_db_connection; print(check_db_connection())"
```

### Health check falha

```bash
# Ver logs da aplicação
railway logs --tail 100

# Verificar se porta está correta
# Railway usa $PORT automaticamente
```

---

## ✅ Checklist Final

- [ ] Repositório GitHub criado e configurado
- [ ] Branches criadas (main, staging, develop)
- [ ] Railway projeto criado
- [ ] PostgreSQL adicionado
- [ ] Variáveis de ambiente configuradas
- [ ] GitHub Secrets configurados
- [ ] GitHub Actions workflow testado
- [ ] Deploy para staging funcionando
- [ ] Health check OK
- [ ] Domínio configurado
- [ ] Monitoramento ativo (Sentry)
- [ ] Documentação atualizada

---

**Próximo passo**: Fazer primeiro deploy! 🚀
