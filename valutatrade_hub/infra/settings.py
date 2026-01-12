from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


DEFAULTS: Dict[str, Any] = {
    "DATA_DIR": "data",
    "USERS_FILE": "users.json",
    "PORTFOLIOS_FILE": "portfolios.json",
    "RATES_FILE": "rates.json",
    "RATES_TTL_SECONDS": 300,
    "BASE_CURRENCY": "USD",
    "LOG_FILE": "logs/app.log",
    
    #логирование
    "LOG_MAX_SIZE_BYTES": 1_000_000, #1MB
    "LOG_BACKUP_COUNT": 3,
    "LOG_DIR": "logs",
    "LOG_ACTIONS_FILE": "actions.log",
    
    #форматирование
    "AMOUNT_PRECISION": 4, #знаков после запятой для amount
    "RATE_PRECISION": 2, #знаков после запятой для rate
    "MONEY_PRECISION": 2, #знаков после запятой для денег
    
    "INITIAL_USD_BALANCE": 50000.0,
    "DEFAULT_PAGE_SIZE": 10,  #для show-rates
}


class SettingsLoader:
    """
    Singleton SettingsLoader
    """

    _instance: Optional["SettingsLoader"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
            cls._instance._config = {}
        return cls._instance

    def reload(self) -> None:
        """
        Принудительно перечитать конфиг.
        """
        self._loaded = False
        self._config = {}
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение конфигурации.
        """
        self._load()
        return self._config.get(key, default)

    def _load(self) -> None:
        """
        Загружает конфигурацию из DEFAULTS и pyproject.toml
        """
        if self._loaded:
            return

        config = dict(DEFAULTS)

        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists() and tomllib is not None:
            try:
                data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
                tool_cfg = (data.get("tool") or {}).get("valutatrade") or {}
                for k, v in tool_cfg.items():
                    config[str(k).upper()] = v
            except Exception:
                pass

        data_dir = Path(str(config["DATA_DIR"]))
        config["DATA_DIR"] = str(data_dir)

        config["USERS_PATH"] = str(data_dir / str(config["USERS_FILE"]))
        config["PORTFOLIOS_PATH"] = str(data_dir / str(config["PORTFOLIOS_FILE"]))
        config["RATES_PATH"] = str(data_dir / str(config["RATES_FILE"]))

        self._config = config
        self._loaded = True
