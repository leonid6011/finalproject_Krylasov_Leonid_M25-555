from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

import requests

from .config import ParserConfig


class ApiRequestError(RuntimeError):
    """
    диная ошибка для проблем сети/внешнего API.
    """


class BaseApiClient(ABC):
    """
    Абстрактный базовый класс для API клиентов.
    """
    name: str
    display_name: str

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        raise NotImplementedError


@dataclass
class CoinGeckoClient(BaseApiClient):
    """
    Клиент для получения курсов криптовалют от CoinGecko API.
    """
    config: ParserConfig
    name: str = "coingecko"
    display_name: str = "CoinGecko"

    def fetch_rates(self) -> Dict[str, float]:
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        vs = self.config.BASE_FIAT_CURRENCY.lower()

        url = self.config.COINGECKO_URL
        params = {"ids": ids, "vs_currencies": vs}

        try:
            resp = requests.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                raise ApiRequestError(f"HTTP {resp.status_code}")

            data = resp.json()
            out: Dict[str, float] = {}

            for code, cg_id in self.config.CRYPTO_ID_MAP.items():
                try:
                    rate = float(data[cg_id][vs])
                except Exception:
                    continue
                out[f"{code}_{self.config.BASE_FIAT_CURRENCY}"] = rate

            return out

        except requests.exceptions.RequestException:
            raise ApiRequestError("Network error.")
        except ValueError:
            raise ApiRequestError("Invalid response.")


@dataclass
class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент для получения курсов фиатных валют от ExchangeRate-API.
    """
    config: ParserConfig
    name: str = "exchangerate"
    display_name: str = "ExchangeRate-API"

    def fetch_rates(self) -> Dict[str, float]:
        api_key = self.config.require_exchangerate_key()
        base = self.config.BASE_FIAT_CURRENCY.upper()

        url = f"{self.config.EXCHANGERATE_API_URL}/{api_key}/latest/{base}"

        try:
            resp = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                raise ApiRequestError(f"HTTP {resp.status_code}")

            data = resp.json()
            rates = data.get("conversion_rates") or data.get("rates")
            if not isinstance(rates, dict):
                raise ApiRequestError("Invalid response.")
            out: Dict[str, float] = {}

            for code in self.config.FIAT_CURRENCIES:
                code_u = code.upper()
                if code_u == base:
                    continue
                v = rates.get(code_u)
                if v is None:
                    continue
                v = float(v)
                if v != 0:
                    out[f"{code_u}_{base}"] = 1.0 / v

            return out

        except requests.exceptions.RequestException:
            raise ApiRequestError("Network error.")
        except ApiRequestError:
            raise
        except Exception:
            raise ApiRequestError("Invalid response.")