# @log_action (логирование операций)
from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


def log_action(
        action: str, 
        verbose: bool = False
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Логирует OK ERROR и пробрасывает исключения дальше.
    Берет username через self._get_username_by_id, self._current_user_id,
    а также currency_code amount base rate из аргументов.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            from valutatrade_hub.infra.settings import SettingsLoader
            
            logger = logging.getLogger(__name__)
            
            settings = SettingsLoader()
            amount_precision = settings.get("AMOUNT_PRECISION", 4)
            rate_precision = settings.get("RATE_PRECISION", 2)

            user_repr = None
            try:
                uid = getattr(self, "_current_user_id", None)
                if uid is not None and hasattr(self, "_get_username_by_id"):
                    user_repr = getattr(self, "_get_username_by_id")(uid)
                elif uid is not None:
                    user_repr = str(uid)
            except Exception:
                user_repr = "unknown"

            currency = kwargs.get("currency_code") or \
                kwargs.get("currency") or (args[0] if len(args) >= 1 else None)
            amount = kwargs.get("amount") or \
                (args[1] if len(args) >= 2 else None)
            base = kwargs.get("base_currency") or \
                kwargs.get("base") or kwargs.get("to_currency")

            def fmt_amount(x: Any) -> str:
                try:
                    return f"{float(x):.{amount_precision}f}"
                except Exception:
                    return "n/a"

            def fmt_rate(x: Any) -> str:
                try:
                    return f"{float(x):.{rate_precision}f}"
                except Exception:
                    return "n/a"

            rate_val: Optional[float] = None

            try:
                result = func(self, *args, **kwargs)

                #если вернулась тройка (old, new, rate)
                if isinstance(result, tuple) and len(result) >= 3:
                    try:
                        rate_val = float(result[2])
                    except Exception:
                        rate_val = None

                msg = (
                    f"{action} user='{user_repr}' "
                    f"currency='{currency}' amount={fmt_amount(amount)} "
                )
                if rate_val is not None:
                    msg += f"rate={fmt_rate(rate_val)} "
                if base:
                    msg += f"base='{base}' "
                msg += "result=OK"

                if verbose and isinstance(result, tuple) and len(result) >= 2:
                    msg += f" old={fmt_amount(result[0])} new={fmt_amount(result[1])}"

                logger.info(msg)
                return result

            except Exception as exc:
                logger.info(
                    f"{action} user='{user_repr}' currency='{currency}' "
                    f"amount={fmt_amount(amount)} "
                    f"result=ERROR error_type={type(exc).__name__} "
                    f"error_message='{exc}'"
                )
                raise
        return wrapper
    return decorator