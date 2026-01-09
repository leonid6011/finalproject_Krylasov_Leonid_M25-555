import hashlib
from datetime import datetime
from typing import Dict, Optional


class User:
    def __init__(
            self,
            user_id: int,
            username: str,
            hashed_password: str,
            salt: str,
            registration_date: str | datetime
    ) -> None:
        self._user_id = user_id

        self.username = username
        
        self._hashed_password = hashed_password
        self._salt = salt
        
        if isinstance(registration_date, str):
            self._registration_date = datetime.fromisoformat(registration_date)
        else:
            self._registration_date = registration_date
        
    # Геттеры
    @property
    def user_id(self) -> int:
        return self._user_id
        
    @property
    def username(self) -> str:
        return self._username
        
    @property
    def registration_date(self) -> datetime:
        return self._registration_date
        
    # Сеттеры
    @username.setter
    def username(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value

    # Методы
    def get_user_info(self) -> dict:
        """
        Возвращает информацию о пользователе без пароля.
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }
        
    def verify_password(self, password: str) -> bool:
        """
        Проверяет правильность введеного пароля.
        """
        hashed = hashlib.sha256((password + self._salt).encode()).hexdigest()
        self._hashed_password = new_hash
        
    # JSON
    def to_dict(self) -> dict:
        """
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }

class Wallet:
    """
    Кошелек пользователя для одой конкретной валюты
    """
    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.balance = balance #через сеттер с валидацией

    @property
    def balance(self) -> float:
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)
    
    # Методы
    def deposit(self, amount: float) -> None:
        """
        Пополнение баланса
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма пополнения должна быть числом.")
        if amount <= 0:
            raise ValueError("Сумма пополнений должна быть положительной.")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        """
        Снятие средств если баланс позволяет.
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма снятия должна быть числом.")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной.")
        if amount > self._balance:
            raise ValueError("На балансе недостаточно средств.")
        self._balance -= float(amount)

    def get_blance_info(self) -> dict:
        """
        Информация о текущем балансе в этой валюте.
        """
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }
    
    # JSON
    def to_dict(self) -> dict:
        """
        Представление кошелька для записи в JSON.
        """
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }
    
    @classmethod
    def from_dict(cls, data:dict) -> "Wallet":
        """
        Создает кошелек из словоря (из JSON).
        """
        return cls(
            currency_code = data.get("currency_code"),
            balance = float(data.get("balance", 0.0))
        )
    
class Portfolio:
    """
    Управляет всеми кошельками одного пользователя.
    """
    def __init__(
            self,
            user: User,
            wallets: Optional[Dict[str, Wallet]] = None
    ) -> None:
        self._user = user
        self._user_id = user.user_id
        self._wallets: Dict[str, Wallet] = wallets or {}

    @property
    def user(self) -> User:
        """
        Объект пользователя (бкз возможности перезаписи).
        """
        return self.user
    
    @property
    def user_id(self) -> int:
        """
        Уникальный идентификатор пользователя
        """
        return self._user_id
    
    @property
    def  wallets(self) -> Dict[str, Wallet]:
        """
        Копия словаря кошельков
        """
        return self._wallets.copy()
    
    # Методы
    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавляем новый кошелек в портфель.
        """
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелек для валюты {code} уже существует.")
        Wallet = Wallet(currency_code = code)
        self._wallets[code] = Wallet
        return Wallet
    
    def get_wallet(self, currency_code: str) -> Wallet:
        """
        Возвращает объект Wallet по коду валюты.
        """
        code = currency_code.upper()
        try:
            return self._wallets[code]
        except KeyError as exc:
            raise KeyError(f"Кошелек для валюты {code} не найден.") from exc
        
    def get_total_value(
            self,
            base_currency: str = "USD",
            exchange_rates: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Возвращает общую тоимость всех валют в указанной базовой валюте.
        """
        base = base_currency.upper()
        # времннная заглушка
        default_rates = {
            "USD": 1.0,
            "EUR": 1.1,
            "BTC": 90000.0
        }
        rates = exchange_rates or default_rates

        if base not in rates:
            #базовая валюта должна быть описана в словаре
            rates = rates.copy()
            rates[base] = 1.0

        total = 0.0
        for code, wallet in self._wallets.items():
            if code not in rates:
                raise KeyError(f"Нет курса для валюты {code}.")
            total += wallet.balance * rates[code]
        return total

    # JSON
    def to_dict(self) -> dict:
        """
        Словарь для сохранения в portfolio.json.
        """
        return {
            "user_id": self._user_id,
            "wallets": {
                code: wallet.to_dict() for code, wallet in self._wallets.items()
           }
        }

    @classsmethod
    def from_dict(cls, data: dict, user: User) -> "Portfolio":
        """
        Создает портфель из словаря (JSON) и объекта пользователя.
        """
        wallets_raw = data.get("wallets", {})
        wallets: Dict[str, Wallet] = {}
        for code, wallet_data in wallets_raw.items():
            wallet_data = dict(wallet_data)
            wallet_data.setdefault("currency_code", code)
            wallets[code] = Wallet.from_dict(wallet_data)
        
        return cls(user=user, wallets=wallets)