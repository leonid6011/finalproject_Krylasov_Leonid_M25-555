from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthError,
    InsufficientFundsError,
    NotLoggedInError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import setup_logging


def normalize_currency(code: str) -> str:
    return (code or "").strip().upper()

class WalletApp:
    """
    register, login, logout, show_portfolio, buy, sell, get_rate
    """

    def __init__(self) -> None:
        setup_logging()

        self._current_user_id: Optional[int] = None
        self._settings = SettingsLoader()
        data_dir = self._settings.get("DATA_DIR", "data")
        self._db = DatabaseManager(data_dir)

    def _require_login(self) -> int:
        if self._current_user_id is None:
            raise NotLoggedInError()
        return self._current_user_id

    def _get_username_by_id(self, user_id: int) -> str:
        users = self._db.load_users()
        raw = next((u for u in users if u.get("user_id") == user_id), None)
        if raw is None:
            raise AuthError("Текущий пользователь не найден в базе")
        return str(raw.get("username"))

    def _load_rates(self) -> Dict[str, Any]:
        """
        Загружает rates.json через DatabaseManager.
        """
        try:
            return self._db.load_rates()
        except Exception:
            return {}

    @log_action("REGISTER", verbose=False)
    def register(self, username: str, password: str) -> int:
        """
        Регистрирует нового пользователя.
        """
        username = (username or "").strip()
        if not username:
            raise ValueError("Имя пользователя не может быть пустым.")
        if not isinstance(password, str) or len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")

        users = self._db.load_users()
        if any(u.get("username") == username for u in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        new_id = (max((int(u.get("user_id", 0)) for u in users), default=0) + 1)
        salt = uuid.uuid4().hex[:8]
        reg_date = datetime.now().isoformat(timespec="seconds")

        user = User(
            user_id=new_id,
            username=username,
            hashed_password="",
            salt=salt,
            registration_date=reg_date,
        )
        user.change_password(password)

        users.append(user.to_dict())
        self._db.save_users(users)

        portfolios = self._db.load_portfolios()

        #получаем начальный баланс USD
        settings = SettingsLoader()
        initial_usd = float(settings.get("INITIAL_USD_BALANCE", 50000.0))

        portfolios.append({
            "user_id": new_id, 
            "wallets": {"USD": initial_usd}
        })
        self._db.save_portfolios(portfolios)
        
        return new_id

    @log_action("LOGIN", verbose=False)
    def login(self, username: str, password: str) -> int:
        """
        Выполняет вход пользователя в систему.
        """
        username = (username or "").strip()
        if not username:
            raise ValueError("username обязателен.")
        if not password:
            raise ValueError("password обязателен.")

        users = self._db.load_users()
        raw = next((u for u in users if u.get("username") == username), None)
        if raw is None:
            raise AuthError(f"Пользователь '{username}' не найден")

        user = User(
            user_id=int(raw["user_id"]),
            username=str(raw["username"]),
            hashed_password=str(raw["hashed_password"]),
            salt=str(raw["salt"]),
            registration_date=str(raw["registration_date"]),
        )

        if not user.verify_password(password):
            raise AuthError("Неверный пароль")

        self._current_user_id = user.user_id
        return user.user_id

    def logout(self) -> None:
        """
        Выполняет выход из системы.
        """
        self._current_user_id = None

    def get_rate(self, currency_code: str, base_currency: str = "USD") -> float:
        """
        Возвращает курс currency_code относительно base_currency.
        """
        from datetime import datetime
        
        currency = normalize_currency(currency_code)
        base = normalize_currency(base_currency)

        #валидация через get_currency()
        get_currency(currency)
        get_currency(base)

        if currency == base:
            return 1.0

        #проверка TTL и автообновление
        rates_data = self._load_rates()
        
        #получаем TTL из настроек
        ttl_seconds = self._settings.get("RATES_TTL_SECONDS", 300)
        last_update = rates_data.get("last_update")
        
        #проверяем, устарел ли кеш
        needs_update = False
        if last_update:
            try:
                last_update_dt = datetime.fromisoformat(last_update)
                age_seconds = (datetime.now() - last_update_dt).total_seconds()
                if age_seconds > ttl_seconds:
                    needs_update = True
            except (ValueError, TypeError):
                needs_update = True
        else:
            needs_update = True
        
        if needs_update:
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Кеш курсов устарел (возраст: "
                               f"{age_seconds if last_update else 'N/A'}s, "
                               f"TTL: {ttl_seconds}s). Требуется обновление."
                               )
            except Exception as e:
                raise ApiRequestError(f"Не удалось обновить курсы: {e}")
            
        is_legacy = isinstance(rates_data, dict) and "pairs" in rates_data
        pairs = rates_data.get("pairs", {}) if is_legacy else rates_data

        if not isinstance(pairs, dict):
            raise ApiRequestError(f"Курс для '{currency}_{base}' "
                                  "не найден в кеше. Попробуйте выполнить update-rates."
                                  )

        pair_direct = f"{currency}_{base}"
        item = pairs.get(pair_direct)
        if isinstance(item, dict) and "rate" in item:
            return float(item["rate"])

        pair_inverse = f"{base}_{currency}"
        item = pairs.get(pair_inverse)
        if isinstance(item, dict) and "rate" in item:
            rate_inverse = float(item["rate"])
            if rate_inverse != 0:
                return 1.0 / rate_inverse
            raise ValueError(f"Курс для '{pair_inverse}' "
                             "равен нулю, невозможно инвертировать."
                             )

        raise ApiRequestError(f"Курс для '{pair_direct}' "
                              "не найден в кеше. Попробуйте выполнить update-rates."
                              )

    def get_rate_detailed(
            self,
            currency_code: str,
            base_currency: str = "USD"
        ) -> Dict[str, Any]:
        """
        Возвращает детальную информацию о курсе.
        """
        currency = normalize_currency(currency_code)
        base = normalize_currency(base_currency)

        #валидация через get_currency()
        get_currency(currency)
        get_currency(base)

        if currency == base:
            return {
                "rate": 1.0,
                "rate_inverse": 1.0,
                "updated_at": "N/A",
                "from": currency,
                "to": base,
            }

        rates_data = self._load_rates()

        is_legacy = isinstance(rates_data, dict) and "pairs" in rates_data
        pairs = rates_data.get("pairs", {}) if is_legacy else rates_data

        if not isinstance(pairs, dict):
            raise ApiRequestError(f"Курс для '{currency}_{base}' "
                                  "не найден в кеше. Попробуйте выполнить update-rates."
                                  )

        pair_direct = f"{currency}_{base}"
        item_direct = pairs.get(pair_direct)

        pair_inverse = f"{base}_{currency}"
        item_inverse = pairs.get(pair_inverse)

        if isinstance(item_direct, dict) and "rate" in item_direct:
            rate_direct = float(item_direct["rate"])
            rate_inverse_calc = 1.0 / rate_direct if rate_direct != 0 else 0.0
            updated_at = item_direct.get("updated_at", "N/A")
            
        elif isinstance(item_inverse, dict) and "rate" in item_inverse:
            rate_inverse_found = float(item_inverse["rate"])
            rate_direct = 1.0 / rate_inverse_found if rate_inverse_found != 0 else 0.0
            rate_inverse_calc = rate_inverse_found
            updated_at = item_inverse.get("updated_at", "N/A")
            
        else:
            raise ApiRequestError(f"Курс для '{pair_direct}' "
                                  "не найден в кеше. Попробуйте выполнить update-rates."
                                  )

        return {
            "rate": rate_direct,
            "rate_inverse": rate_inverse_calc,
            "updated_at": updated_at,
            "from": currency,
            "to": base,
        }

    def show_portfolio(
        self,
        base_currency: str = "USD",
    ) -> Tuple[str, List[Tuple[str, float, float]], float]:
        """
        Показывает портфель пользователя с оценкой в базовой валюте.
        """
        user_id = self._require_login()
        base = normalize_currency(base_currency)

        get_currency(base)

        username = self._get_username_by_id(user_id)

        portfolios = self._db.load_portfolios()
        pf_raw = next((p for p in portfolios if p.get("user_id") == user_id), None)
        if pf_raw is None:
            pf_raw = {"user_id": user_id, "wallets": {}}

        users = self._db.load_users()
        user_raw = next(u for u in users if u.get("user_id") == user_id)
        user = User(
            user_id=int(user_raw["user_id"]),
            username=str(user_raw["username"]),
            hashed_password=str(user_raw["hashed_password"]),
            salt=str(user_raw["salt"]),
            registration_date=str(user_raw["registration_date"]),
        )
        portfolio = Portfolio.from_dict(pf_raw, user=user)

        rows: List[Tuple[str, float, float]] = []
        total_in_base = 0.0

        for code, wallet in portfolio.wallets.items():
            amount = float(wallet.balance)
            rate = self.get_rate(code, base)
            value_base = amount * rate
            rows.append((code, amount, value_base))
            total_in_base += value_base

        return username, rows, total_in_base

    @log_action("BUY", verbose=True)
    def buy(self, currency_code: str, amount: float) -> Tuple[float, float, float]:
        """
        Покупка валюты за USD.
        """
        user_id = self._require_login()
        code = normalize_currency(currency_code)

        get_currency(code)

        if not isinstance(amount, (int, float)) or float(amount) <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        rate = self.get_rate(code, "USD")

        portfolios = self._db.load_portfolios()
        pf = next((p for p in portfolios if p.get("user_id") == user_id), None)
        if pf is None:
            pf = {"user_id": user_id, "wallets": {}}
            portfolios.append(pf)

        wallets = pf.get("wallets", {})
        
        #списание с USD кошелька
        usd_cost = float(amount) * rate
        usd_wallet = wallets.get("USD", {"balance": 0.0})
        old_usd = float(usd_wallet.get("balance", 0.0))
        
        if old_usd < usd_cost:
            raise InsufficientFundsError(
                available=old_usd,
                required=usd_cost,
                code="USD"
            )
        
        new_usd = old_usd - usd_cost
        wallets["USD"] = {"balance": new_usd}

        old_balance = float(wallets.get(code, {}).get("balance", 0.0))
        new_balance = old_balance + float(amount)
        wallets[code] = {"balance": new_balance}
        pf["wallets"] = wallets
        self._db.save_portfolios(portfolios)
        return old_balance, new_balance, rate

    @log_action("SELL", verbose=True)
    def sell(self, currency_code: str, amount: float) -> Tuple[float, float, float]:
        """
        Продажа валюту за USD.
        """
        user_id = self._require_login()
        code = normalize_currency(currency_code)

        #валидация валюты, может выбросить CurrencyNotFoundError
        get_currency(code)

        if not isinstance(amount, (int, float)) or float(amount) <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        rate = self.get_rate(code, "USD")

        portfolios = self._db.load_portfolios()
        pf = next((p for p in portfolios if p.get("user_id") == user_id), None)
        if pf is None:
            raise ValueError("Портфель не найден.")

        wallets = pf.get("wallets", {})
        if code not in wallets:
            raise ValueError(
                f"У вас нет кошелька '{code}'. "
                f"Добавьте валюту: она создаётся автоматически при первой покупке."
            )

        old_balance = float(wallets[code].get("balance", 0.0))
        need = float(amount)

        if old_balance < need:
            raise InsufficientFundsError(
                available=old_balance,
                required=need,
                code=code,
            )

        #уменьшаем баланс проданной валюты
        new_balance = old_balance - need
        wallets[code] = {"balance": new_balance}
        usd_proceeds = float(amount) * rate
        
        usd_wallet = wallets.get("USD", {"balance": 0.0})
        old_usd = float(usd_wallet.get("balance", 0.0))
        new_usd = old_usd + usd_proceeds
        wallets["USD"] = {"balance": new_usd}
        pf["wallets"] = wallets
        self._db.save_portfolios(portfolios)

        return old_balance, new_balance, rate