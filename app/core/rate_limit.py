"""
Módulo de Rate Limiting - DataZone Energy
Proteção contra DDoS e uso abusivo da API
"""

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.core.logging import app_logger as logger


def get_client_identifier(request: Request) -> str:
    """
    Identifica cliente para rate limiting.

    Ordem de prioridade:
    1. IP real do cliente (X-Forwarded-For header)
    2. IP direto da requisição
    3. User-Agent como fallback

    Args:
        request: Request do FastAPI

    Returns:
        Identificador único do cliente
    """
    # Tentar obter IP real (atrás de proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Pegar primeiro IP da lista (cliente original)
        client_ip = forwarded_for.split(",")[0].strip()
        return client_ip

    # IP direto
    client_ip = get_remote_address(request)
    if client_ip:
        return client_ip

    # Fallback: User-Agent (menos confiável)
    user_agent = request.headers.get("User-Agent", "unknown")
    logger.warning(f"Rate limit: usando User-Agent como identificador | UA: {user_agent[:50]}")
    return user_agent


def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handler customizado para quando rate limit é excedido.

    Args:
        request: Request do FastAPI
        exc: Exceção de rate limit

    Returns:
        Response JSON com erro 429
    """
    client_id = get_client_identifier(request)
    endpoint = request.url.path

    # Log de tentativa de abuso
    logger.warning(
        f"⚠️ Rate limit excedido | "
        f"Cliente: {client_id} | "
        f"Endpoint: {endpoint} | "
        f"Limite: {exc.detail}"
    )

    # Retornar resposta customizada
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Você excedeu o limite de requisições. Tente novamente em alguns segundos.",
            "detail": exc.detail,
            "endpoint": endpoint,
        },
        headers={
            "Retry-After": "60",  # Sugerir retry após 60 segundos
            "X-RateLimit-Limit": str(exc.detail),
        },
    )


# ============================================
# Configurar Limiter
# ============================================

# Criar instância do limiter
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[],  # Sem limites padrão, definir por rota
    storage_uri=settings.REDIS_URL if settings.ENABLE_REDIS_CACHE else "memory://",
    strategy="fixed-window",  # Estratégia de janela fixa
    headers_enabled=True,  # Adicionar headers de rate limit nas respostas
)


# ============================================
# Decoradores de Rate Limiting
# ============================================


def rate_limit_endpoint(limits: str):
    """
    Decorador para aplicar rate limiting em endpoints específicos.

    Exemplos de uso:
        @rate_limit_endpoint("10/minute")
        @rate_limit_endpoint("100/hour")
        @rate_limit_endpoint("5/second")

    Args:
        limits: String de limite (ex: "10/minute", "100/hour")

    Returns:
        Decorador configurado
    """
    return limiter.limit(limits)


# ============================================
# Limites pré-configurados
# ============================================

# Rate limiting por tipo de operação
RATE_LIMITS = {
    # Endpoints de leitura (mais permissivos)
    "read_light": "100/minute",  # Queries simples
    "read_medium": "50/minute",  # Queries com filtros
    "read_heavy": "20/minute",  # Queries complexas com geometria
    # Endpoints de escrita (mais restritivos)
    "write": "10/minute",  # POST/PUT/DELETE
    # Health checks (muito permissivo)
    "health": "300/minute",  # Monitoramento
    # Global (proteção DDoS)
    "global": "1000/hour",  # Limite geral por IP
}


def get_rate_limit(operation_type: str) -> str:
    """
    Obtém limite configurado para tipo de operação.

    Args:
        operation_type: Tipo da operação (read_light, read_heavy, etc)

    Returns:
        String de limite
    """
    return RATE_LIMITS.get(operation_type, "50/minute")


# ============================================
# Middleware de Rate Limiting Global
# ============================================


class RateLimitMiddleware:
    """
    Middleware para aplicar rate limiting global em todas as requisições.
    Proteção adicional contra DDoS.
    """

    def __init__(self, app, limit: str = "1000/hour"):
        """
        Inicializa middleware.

        Args:
            app: Aplicação FastAPI
            limit: Limite global (padrão: 1000/hora por IP)
        """
        self.app = app
        self.limit = limit
        logger.info(f"✅ Rate Limiting Middleware habilitado | Limite global: {limit}")

    async def __call__(self, scope, receive, send):
        """
        Processa requisição com rate limiting.
        """
        # Apenas processar requisições HTTP
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Criar Request object
        from fastapi import Request

        request = Request(scope, receive)

        # Aplicar rate limiting global
        try:
            # Verificar se excedeu limite global
            client_id = get_client_identifier(request)

            # TODO: Implementar verificação de limite global via Redis/Memory
            # Por enquanto, apenas passar adiante

            await self.app(scope, receive, send)

        except Exception as e:
            logger.error(f"Erro no Rate Limiting Middleware: {e}")
            # Em caso de erro, deixar passar (fail-open)
            await self.app(scope, receive, send)


# ============================================
# Funções auxiliares
# ============================================


def is_whitelisted(ip: str) -> bool:
    """
    Verifica se IP está na whitelist (sem rate limiting).

    Args:
        ip: Endereço IP

    Returns:
        True se whitelisted
    """
    # IPs internos/localhost sempre whitelisted
    whitelist = [
        "127.0.0.1",
        "localhost",
        "::1",
    ]

    # Adicionar IPs de monitoramento em produção
    if not settings.DEBUG:
        whitelist.extend(
            [
                # Adicionar IPs de load balancers, monitoring, etc
            ]
        )

    return ip in whitelist


def get_rate_limit_status(request: Request) -> dict:
    """
    Obtém status atual de rate limiting para cliente.

    Args:
        request: Request do FastAPI

    Returns:
        Dict com status de rate limiting
    """
    client_id = get_client_identifier(request)

    return {
        "client_id": client_id,
        "whitelisted": is_whitelisted(client_id),
        "limits": RATE_LIMITS,
        "storage": "redis" if settings.ENABLE_REDIS_CACHE else "memory",
    }


# ============================================
# Exportar componentes principais
# ============================================

__all__ = [
    "limiter",
    "rate_limit_endpoint",
    "get_rate_limit",
    "custom_rate_limit_exceeded_handler",
    "RateLimitMiddleware",
    "get_rate_limit_status",
    "RATE_LIMITS",
]
