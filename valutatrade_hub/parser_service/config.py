# valutatrade_hub/parser_service/config.py
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class ParserConfig:
    """
    Конфигурация Parser Service.
    """

    EXCHANGERATE_API_KEY: str | None = field(
        default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY")
    )

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_FIAT_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL")

    CRYPTO_ID_MAP: Dict[str, str] = field(
        default_factory=lambda: {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}
    )

    REQUEST_TIMEOUT: int = 10

    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    def require_exchangerate_key(self) -> str:
        """
        Возвращает API ключ ExchangeRate-API или бросает исключение.
        """
        if not self.EXCHANGERATE_API_KEY:
            raise RuntimeError("missing EXCHANGERATE_API_KEY (env var)")
        return self.EXCHANGERATE_API_KEY