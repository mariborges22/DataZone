# 🔒 Guia de Segurança - DataZone Energy

## ✅ Medidas de Segurança Implementadas

### 1. **SQL Logging Desabilitado**
- ❌ **Antes**: Queries SQL expostas nos logs (`echo=True`)
- ✅ **Agora**: `echo=False` em `app/core/database.py`
- **Benefício**: Previne exposição de estrutura do banco e dados sensíveis

### 2. **Módulo de Segurança Completo**
Criado `app/core/security.py` com:

#### 🔐 Criptografia
- **Algoritmo**: Fernet (AES-128)
- **Derivação de Chave**: PBKDF2 com SHA-256
- **Uso**: Criptografar dados sensíveis antes de armazenar

```python
from app.core.security import security

# Criptografar
encrypted = security.encrypt("dado_sensivel")

# Descriptografar
decrypted = security.decrypt(encrypted)
```

#### 🛡️ Proteção contra SQL Injection
- **Validação de Inputs**: Sanitização automática
- **Remoção de Caracteres Perigosos**: `;`, `--`, `/*`, `EXEC`, etc.
- **Limite de Tamanho**: Máximo 1000 caracteres por input

#### 📍 Validação de Bounding Box
- **Ranges Válidos**: -180 a 180 (lon), -90 a 90 (lat)
- **Tamanho Máximo**: 10 graus (previne queries muito grandes)
- **Validação Lógica**: min < max

#### 🚫 Remoção de Dados Sensíveis
Campos **NUNCA** expostos ao frontend:
- `created_at` - Timestamp de criação
- `updated_at` - Timestamp de atualização
- `data_source` - Fonte dos dados
- `password`, `token`, `secret`, `api_key` - Credenciais

### 3. **Endpoints Seguros**
- ✅ Validação de bbox antes de executar queries
- ✅ Campos sensíveis removidos do response
- ✅ Mensagens de erro genéricas (não expõem detalhes internos)

### 4. **Rate Limiting e Proteção DDoS** ⭐ NOVO
Implementado em `app/core/rate_limit.py` com:

#### 🚦 Limites por Endpoint
- **Health Check**: 300 req/min (monitoramento)
- **Root**: 100 req/min (informacional)
- **Queries GeoJSON**: 20 req/min (operações pesadas)
- **Queries por ID**: 50 req/min (operações leves)
- **Rate Limit Status**: 60 req/min (debug)

#### 🔍 Identificação Inteligente de Cliente
- **Prioridade 1**: IP real (X-Forwarded-For header)
- **Prioridade 2**: IP direto da requisição
- **Prioridade 3**: User-Agent (fallback)

#### 📊 Features
- ✅ Suporte a Redis para ambiente distribuído
- ✅ Fallback para memória (desenvolvimento)
- ✅ Headers de rate limit nas respostas
- ✅ Logs de tentativas de abuso
- ✅ Whitelist para IPs internos
- ✅ Resposta customizada 429 (Too Many Requests)

```python
# Exemplo de resposta quando limite excedido
{
  "error": "Rate limit exceeded",
  "message": "Você excedeu o limite de requisições. Tente novamente em alguns segundos.",
  "detail": "20 per 1 minute",
  "endpoint": "/api/v1/fibra"
}
```

### 5. **SQL Injection em Scripts ETL** ⭐ NOVO
Correção em `scripts/extrair_anatel.py`:

#### 🛡️ Validação de Table Names
- **Whitelist**: Apenas `[a-zA-Z0-9_]`
- **Limite**: Máximo 63 caracteres (PostgreSQL limit)
- **Sanitização**: Método `_validate_table_name()`

```python
# Antes (VULNERÁVEL)
conn.execute(text(f"CREATE INDEX ON geo.{table_name}"))

# Depois (SEGURO)
validated_name = self._validate_table_name(table_name)
conn.execute(text(f"CREATE INDEX ON geo.{validated_name}"))
```

---

## 🔐 Boas Práticas Implementadas

### 1. **Princípio do Menor Privilégio**
- Frontend **NUNCA** acessa banco diretamente
- Apenas dados necessários são expostos
- Metadados internos ficam no backend

### 2. **Defense in Depth**
- Múltiplas camadas de segurança
- SQLAlchemy ORM (proteção nativa)
- Validação customizada adicional
- Sanitização de inputs

### 3. **Fail Secure**
- Em caso de erro, retornar vazio (não expor detalhes)
- Logs de erro apenas no servidor
- Mensagens genéricas para o usuário

---

## 🚨 O que NÃO Fazer

### ❌ NUNCA:
1. Logar queries SQL em produção
2. Expor mensagens de erro detalhadas ao frontend
3. Retornar stack traces para o usuário
4. Usar concatenação de strings para SQL
5. Expor campos de metadados (`created_at`, `data_source`)
6. Aceitar inputs sem validação
7. Armazenar senhas em texto plano
8. Commitar `.env` no Git

---

## 🔧 Configurações de Produção

### Variáveis de Ambiente Críticas

```bash
# .env (PRODUÇÃO)

# Gerar chave segura
SECRET_KEY=$(openssl rand -hex 32)

# Desabilitar debug
DEBUG=False

# Ambiente
ENVIRONMENT=production

# Banco (usar variáveis do Railway)
DATABASE_URL=${DATABASE_URL}
ASYNC_DATABASE_URL=${ASYNC_DATABASE_URL}

# CORS (apenas domínios autorizados)
BACKEND_CORS_ORIGINS=["https://seudominio.com"]
```

### Checklist de Deploy

- [ ] `DEBUG=False` em produção
- [ ] `SECRET_KEY` gerada com `openssl rand -hex 32`
- [ ] CORS configurado apenas para domínios autorizados
- [ ] HTTPS habilitado (certificado SSL)
- [ ] Firewall configurado
- [x] **Rate limiting implementado** ✅
- [ ] Redis habilitado para rate limiting em produção (`ENABLE_REDIS_CACHE=true`)
- [ ] Logs centralizados (não expor ao público)
- [ ] Backup automático do banco
- [ ] Monitoramento de segurança ativo
- [ ] Instalar dependências: `pip install -r requirements.txt`

---

## 📊 Monitoramento de Segurança

### Logs a Monitorar
- Tentativas de SQL injection
- Bboxes inválidos (possível ataque)
- Erros 500 frequentes
- Acessos a endpoints inexistentes
- Tentativas de autenticação falhadas
- ⭐ **Rate limit excedido** (log: "⚠️ Rate limit excedido")
- ⭐ **Validação de table name falhou** (possível SQL injection em scripts)

### Alertas Recomendados
- Mais de 10 erros 400 em 1 minuto (possível scan)
- Mais de 5 erros 500 em 1 minuto (possível ataque)
- Bbox com tamanho > 10 graus (possível DoS)
- Queries com caracteres suspeitos
- ⭐ **Mais de 50 erros 429 por IP em 5 minutos** (possível DDoS)
- ⭐ **Mesmo IP excedendo rate limit em múltiplos endpoints** (bot malicioso)

---

## 🔒 Próximas Melhorias de Segurança

### Fase 1 (MVP) ✅ CONCLUÍDA
- [x] Desabilitar SQL logging
- [x] Criar módulo de segurança
- [x] Validar inputs
- [x] Remover campos sensíveis
- [x] **Rate limiting por IP** ⭐ IMPLEMENTADO
- [x] **SQL Injection prevention em scripts** ⭐ IMPLEMENTADO
- [x] **Proteção DDoS** ⭐ IMPLEMENTADO

### Fase 2 (Pós-MVP)
- [ ] Implementar autenticação JWT
- [ ] CAPTCHA em endpoints públicos
- [ ] Auditoria de acessos
- [ ] Criptografia de dados em repouso
- [ ] 2FA para admin
- [ ] WAF (Web Application Firewall)
- [ ] Penetration testing
- [ ] Análise de vulnerabilidades automatizada

---

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Status**: 🔒 Segurança Implementada - Pronto para Produção
