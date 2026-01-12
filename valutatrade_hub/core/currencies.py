# Базовый класс Currency и наследники Fiat/Crypto

from abc import ABC, abstractmethod
from typing import Dict

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс для всех валют.
    Определяет общую структуру для фиатных и криптовалют.
    """
    def __init__(self, name: str, code: str) -> None:
        if not name.strip():
            raise ValueError("Название валюты не может быть пустым.")

        if not code.isupper() or not (2 <= len(code) <= 5):
            raise ValueError("Код валюты должен быть в "
                             "верхнем регистре (2–5 символов).")

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Строковое представление валюты для UI/логов.
        """
        pass

class FiatCurrency(Currency):
    """
    Фиатная валюта USD, EUR, GBP, RUB
    """
    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name, code)

        if not issuing_country.strip():
            raise ValueError("Страна эмиссии не может быть пустой.")

        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    """
    Криптовалюта BTC, ETH, SOL.
    """
    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        super().__init__(name, code)

        if not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым.")

        if market_cap <= 0:
            raise ValueError("Рыночная капитализация должна быть положительной.")

        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )

_CURRENCIES: Dict[str, Currency] = {
    #фиатные валюты
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    #криптовалюты
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of History", 8.5e10),
}

def get_currency(code: str) -> Currency:
    """
    Возвращает объект Currency по коду валюты.
    """
    code = code.strip().upper()

    try:
        return _CURRENCIES[code]
    except KeyError as exc:
        raise CurrencyNotFoundError(code) from exc