import logging
import sys

from loguru import logger

from app.config import settings


class InterceptHandler(logging.Handler):
    """
    Handler para interceptar logs do logging padrão do Python e redirecionar para o Loguru.
    Veja: https://loguru.readthedocs.io/en/stable/resources/recipes.html#intercepting-standard-logging-messages-on-the-fly
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    """
    Configura o sistema de logging baseado no ambiente
    """
    # Remover handlers padrão do Loguru
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
        rotation="00:00",
        retention=retention_days,
        compression="zip",
        backtrace=True,
        diagnose=settings.ENVIRONMENT != "production",
    )

    # Interceptar logs de bibliotecas (incluindo uvicorn, sqlalchemy, etc)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Silenciar logs muito ruidosos em níveis inferiores a WARNING
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    logger.info(
        f"Logging unificado configurado - Ambiente: {settings.ENVIRONMENT} | Nível: {log_level}"
    )

    return logger


# Instância global do logger
app_logger = setup_logging()
