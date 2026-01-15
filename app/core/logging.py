"""
Configuração atualizada de logging com suporte a múltiplos ambientes
"""

import sys
from loguru import logger
from app.config import settings


def setup_logging():
    """
    Configura o sistema de logging baseado no ambiente
    """
    # Remover handlers padrão
    logger.remove()
    
    # Determinar nível de log baseado no ambiente
    log_level = settings.LOG_LEVEL
    
    # Formato de log
    if settings.ENVIRONMENT == "production":
        # Formato JSON para produção (facilita parsing)
        log_format = (
            "{{"
            '"time":"{time:YYYY-MM-DD HH:mm:ss.SSS}",'
            '"level":"{level}",'
            '"message":"{message}",'
            '"file":"{file}",'
            '"function":"{function}",'
            '"line":{line}'
            "}}"
        )
    else:
        # Formato colorido para dev/staging
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Console output (apenas dev e staging)
    if settings.ENVIRONMENT != "production":
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    
    # File output (todos os ambientes)
    retention_days = "30 days" if settings.ENVIRONMENT == "production" else "7 days"
    
    logger.add(
        f"logs/{settings.ENVIRONMENT}_{{time:YYYY-MM-DD}}.log",
        format=log_format,
        level=log_level,
        rotation="00:00",  # Nova arquivo à meia-noite
        retention=retention_days,
        compression="zip",
        backtrace=True,
        diagnose=settings.ENVIRONMENT != "production",  # Apenas em dev/staging
    )
    
    # Arquivo de erros separado (todos os ambientes)
    logger.add(
        f"logs/{settings.ENVIRONMENT}_errors_{{time:YYYY-MM-DD}}.log",
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # Manter erros por mais tempo
        compression="zip",
        backtrace=True,
        diagnose=settings.ENVIRONMENT != "production",
    )
    
    # Arquivo de erros críticos (apenas produção)
    if settings.ENVIRONMENT == "production":
        logger.add(
            "logs/critical_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="CRITICAL",
            rotation="00:00",
            retention="180 days",  # 6 meses
            compression="zip",
        )
    
    logger.info(f"Logging configurado - Ambiente: {settings.ENVIRONMENT} | Nível: {log_level}")
    
    return logger


# Instância global do logger
app_logger = setup_logging()
