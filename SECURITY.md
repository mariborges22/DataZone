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
- [ ] Rate limiting implementado
- [ ] Logs centralizados (não expor ao público)
- [ ] Backup automático do banco
- [ ] Monitoramento de segurança ativo

---

## 📊 Monitoramento de Segurança

### Logs a Monitorar
- Tentativas de SQL injection
- Bboxes inválidos (possível ataque)
- Erros 500 frequentes
- Acessos a endpoints inexistentes
- Tentativas de autenticação falhadas

### Alertas Recomendados
- Mais de 10 erros 400 em 1 minuto (possível scan)
- Mais de 5 erros 500 em 1 minuto (possível ataque)
- Bbox com tamanho > 10 graus (possível DoS)
- Queries com caracteres suspeitos

---

## 🔒 Próximas Melhorias de Segurança

### Fase 1 (MVP) ✅
- [x] Desabilitar SQL logging
- [x] Criar módulo de segurança
- [x] Validar inputs
- [x] Remover campos sensíveis

### Fase 2 (Pós-MVP)
- [ ] Implementar autenticação JWT
- [ ] Rate limiting por IP
- [ ] CAPTCHA em endpoints públicos
- [ ] Auditoria de acessos
- [ ] Criptografia de dados em repouso
- [ ] 2FA para admin
- [ ] WAF (Web Application Firewall)
- [ ] Penetration testing

---

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Status**: 🔒 Segurança Implementada - Pronto para Produção
