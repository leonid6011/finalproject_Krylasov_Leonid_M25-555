# valutatrade_hub/infra/database.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

from valutatrade_hub.core.utils import read_json, write_json


@dataclass
class DatabaseManager:
    """
    Простой файловый DB слой. Хранит и отдает данные из json
    """

    data_dir: Union[str, Path]

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._users_path = self.data_dir / "users.json"
        self._portfolios_path = self.data_dir / "portfolios.json"
        self._rates_path = self.data_dir / "rates.json"

    def load_users(self) -> list[dict[str, Any]]:
        """
        Загружает список пользователей из users.json.
        """
        return read_json(self._users_path, default=[])

    def save_users(self, users: list[dict[str, Any]]) -> None:
        """
        Сохраняет список пользователей в users.json.
        """
        write_json(self._users_path, users)

    def load_portfolios(self) -> list[dict[str, Any]]:
        """
        Загружает список портфелей из portfolios.json.
        """
        return read_json(self._portfolios_path, default=[])

    def save_portfolios(self, portfolios: list[dict[str, Any]]) -> None:
        """
        Сохраняет список портфелей в portfolios.json.
        """
        write_json(self._portfolios_path, portfolios)

    def load_rates(self) -> dict[str, Any]:
        """
        Загружает кэш курсов из rates.json.
        """
        return read_json(self._rates_path, default={})

    def save_rates(self, rates: dict[str, Any]) -> None:
        """
        Сохраняет кэш курсов в rates.json.
        """
        write_json(self._rates_path, rates)

