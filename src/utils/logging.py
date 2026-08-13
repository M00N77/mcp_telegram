import logging
import sys

def setup_logging():
    """Настройка логирования строго в stderr (критично для MCP)"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Удаляем любые существующие обработчики, чтобы ничего не попало в stdout
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Уменьшаем уровень логирования для httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger
