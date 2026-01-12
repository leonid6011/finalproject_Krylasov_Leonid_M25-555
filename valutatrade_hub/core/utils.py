from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_root() -> Path:
    """
    Возвращает корневую директорию проекта.
    """
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    """
    Возвращает путь к директории data.
    """
    return project_root() / "data"


def read_json(path: Path, default: Any) -> Any:
    """
    Читает JSON файл с автоматическим созданием при отсутствии.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, default)
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    """
    Записывает данные в JSON файл с созданием директории.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_amount(value: str) -> float:
    """
    Валидирует и конвертирует сумму в float.
    """
    try:
        amount = float(value)
    except ValueError as exc:
        raise ValueError("amount должен быть числом.") from exc
    if amount <= 0:
        raise ValueError("amount должен быть > 0.")
    return amount


def normalize_currency(code: str) -> str:
    """
    Нормализует код валюты к верхнему регистру.
    """
    code = (code or "").strip().upper()
    if not code:
        raise ValueError("currency_code не может быть пустым.")
    return code