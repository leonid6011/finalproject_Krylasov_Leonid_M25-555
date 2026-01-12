# Настройка логов (формат, уровень, ротация)
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_path: str | None = None, level: int = logging.INFO) -> None:
    """
    Человекочитаемые логи в файл с ротацией.
    Пример строки: 
    INFO 2025-10-09T12:05:22 BUY user='alice' currency='BTC' 
    amount=0.0500 rate=59300.00 base='USD' result=OK
    """
    from valutatrade_hub.infra.settings import SettingsLoader
    
    logger = logging.getLogger()
    logger.setLevel(level)

    #чтобы не плодить хендлеры при повторном запуске или импорте
    if logger.handlers:
        return

    settings = SettingsLoader()
    
    if log_path is None:
        log_dir = settings.get("LOG_DIR", "logs")
        Path(log_dir).mkdir(exist_ok=True)
        log_file = settings.get("LOG_ACTIONS_FILE", "actions.log")
        log_path = f"{log_dir}/{log_file}"

    max_bytes = settings.get("LOG_MAX_SIZE_BYTES", 1_000_000)
    backup_count = settings.get("LOG_BACKUP_COUNT", 3)
    
    handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(levelname)s %(asctime)s %(message)s", 
                            "%Y-%m-%dT%H:%M:%S")
    handler.setFormatter(fmt)
    logger.addHandler(handler)