# valutatrade_hub/core/exceptions.py
# пользовательские исключения

class AuthError(Exception):
    """
    Ошибки аутентификации (неверный пароль / нет пользователя).
    """
    pass

class WalletAppError(Exception):
    """
    Базовая ошибка приложения.
    """
    pass

class CurrencyNotFoundError(WalletAppError):
    """
    Неизвестная валюта.
    """
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class InsufficientFundsError(WalletAppError):
    """
    Недостаточно средств.
    """
    def __init__(self, available: float, required: float, code: str) -> None:
        self.available = available
        self.required = required
        self.code = code
        msg = (
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )
        super().__init__(msg)


class ApiRequestError(WalletAppError):
    """
    Сбой внешнего API (Parser/заглушка/сеть).
    """
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")

class NotLoggedInError(WalletAppError):
    """
    Пользователь не выполнил login.
    """
    def __init__(self):
        super().__init__("Сначала выполните login")