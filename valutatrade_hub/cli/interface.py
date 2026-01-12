# valutatrade_hub/cli/interface.py
from __future__ import annotations

import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    NotLoggedInError,
    WalletAppError,
)
from valutatrade_hub.core.usecases import WalletApp

# Parser Service
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def _safe_input(prompt: str) -> str:
    """
    Чтение ввода с обработкой ошибок кодировки.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    data = sys.stdin.buffer.readline()
    if not data:
        raise EOFError
    enc = sys.stdin.encoding or "utf-8"
    return data.decode(enc, errors="replace").strip()

def _parse_flags(tokens: List[str]) -> Tuple[str, Dict[str, str]]:
    """
    Парсит команду и флаги из списка.
    """
    if not tokens:
        return "", {}
    cmd = tokens[0]
    args: Dict[str, str] = {}
    i = 1
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("--"):
            key = t[2:]
            val = ""
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                val = tokens[i + 1]
                i += 2
            else:
                i += 1
            args[key] = val
        else:
            i += 1
    return cmd, args

def _safe_float(val: str) -> float:
    """
    Безопасная конвертация строки в float
    """
    try:
        return float(val)
    except (TypeError, ValueError):
        raise ValueError("Некорректное число для --amount")

def _safe_int(val: str) -> int:
    """
    Безопасная конвертация строки
    """
    try:
        return int(val)
    except (TypeError, ValueError):
        raise ValueError("Некорректное число для --top")

def _format_money(value: float) -> str:
    from valutatrade_hub.infra.settings import SettingsLoader
    settings = SettingsLoader()
    precision = settings.get("MONEY_PRECISION", 2)
    return f"{value:,.{precision}f}"

def _format_portfolio_output(
        username: str, 
        rows: list[tuple[str, float, float]], 
        total: float, base: str
    ) -> str:
    """
    список кортежей (currency, balance, value_in_base)
    """
    from valutatrade_hub.infra.settings import SettingsLoader
    settings = SettingsLoader()
    amount_precision = settings.get("AMOUNT_PRECISION", 4)
    
    lines: list[str] = []
    lines.append(f"Портфель пользователя '{username}' (база: {base}):")
    for cur, balance, value_in_base in rows:
        # как в ТЗ: - BTC: 0.0500 -> 2965.00 USD
        lines.append(f"- {cur}: {balance:.{amount_precision}f} -> "
                     f"{_format_money(value_in_base)} {base}"
                     )
    lines.append("-" * 36)
    lines.append(f"ИТОГО: {_format_money(total)} {base}")
    return "\n".join(lines)

def _init_parser():
    """
    Инициализирует Parser Service компоненты.
    """
    config = ParserConfig()
    data_dir = Path("data")
    storage = RatesStorage(data_dir=data_dir)

    coingecko = CoinGeckoClient(config=config)
    exchangerate = ExchangeRateApiClient(config=config)

    updater = RatesUpdater(clients=[coingecko, exchangerate], storage=storage)
    return updater, storage

def run_cli() -> None:
    """
    Запускает CLI интерфейс ValutaTrade Hub.
    
    Инициализирует WalletApp и запускает бесконечный цикл обработки команд.
    Обрабатывает все исключения и выводит сообщения об ошибках.
    """
    app = WalletApp()

    print("ValutaTrade Hub. Напишите 'help' для списка команд.")

    while True:
        try:
            raw = _safe_input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            return

        if not raw:
            continue

        try:
            tokens = shlex.split(raw)
        except ValueError:
            print("Ошибка: некорректный ввод.")
            continue

        cmd, args = _parse_flags(tokens)

        #базовые команды
        if cmd == "exit":
            print("Выход.")
            return

        if cmd == "help":
            print(
                "Команды:\n"
                "  register --username <str> --password <str>\n"
                "  login --username <str> --password <str>\n"
                "  show-portfolio [--base <str>]\n"
                "  buy --currency <str> --amount <float>\n"
                "  sell --currency <str> --amount <float>\n"
                "  get-rate --from <str> [--to <str>]\n"
                "\n"
                "  update-rates [--source <coingecko|exchangerate>]\n"
                "  show-rates [--currency <str>] [--top <int>] [--base <str>]\n"
                "\n"
                "  logout\n"
                "  help\n"
                "  exit"
            )
            continue

        #команды
        try:
            if cmd == "register":
                username = args.get("username", "")
                password = args.get("password", "")

                user_id = app.register(username=username, password=password)
                masked_password = "*" * len(password)

                print(
                f"Пользователь '{username}' зарегистрирован (id={user_id}). "
                f"Войдите: login --username {username} --password {masked_password}."
                )
                continue

            if cmd == "login":
                username = args.get("username", "")
                password = args.get("password", "")
                app.login(username=username, password=password)
                print(f"Вы вошли как '{username}'")
                continue

            if cmd == "logout":
                app.logout()
                print("Вы вышли из аккаунта.")
                continue

            if cmd == "show-portfolio":
                base = args.get("base", "USD")
                username, rows, total = app.show_portfolio(base_currency=base)
                print(_format_portfolio_output(username=username, \
                                               rows=rows, total=total, base=base))
                continue

            if cmd == "buy":
                from valutatrade_hub.infra.settings import SettingsLoader
                settings = SettingsLoader()
                amount_precision = settings.get("AMOUNT_PRECISION", 4)
                rate_precision = settings.get("RATE_PRECISION", 2)
                
                currency = (args.get("currency") or "").upper()
                amount = _safe_float(args.get("amount", "0") or "0")

                old_balance, new_balance, rate = app.buy(currency_code=currency, \
                                                         amount=amount)

                base = "USD"
                cost = float(amount) * float(rate)

                print(f"Покупка выполнена: "
                      f"{float(amount):.{amount_precision}f} {currency} "
                      f"по курсу {float(rate):.{rate_precision}f} {base}/{currency}"
                      )
                print("Изменения в портфеле:")
                print(f"- {currency}: было "
                      f"{float(old_balance):.{amount_precision}f} "
                      f"-> стало {float(new_balance):.{amount_precision}f}"
                      )
                print(f"Оценочная стоимость покупки: {_format_money(cost)} {base}")
                continue


            if cmd == "sell":
                from valutatrade_hub.infra.settings import SettingsLoader
                settings = SettingsLoader()
                amount_precision = settings.get("AMOUNT_PRECISION", 4)
                rate_precision = settings.get("RATE_PRECISION", 2)
                
                currency = (args.get("currency") or "").upper()
                amount = _safe_float(args.get("amount", "0") or "0")

                old_balance, new_balance, rate = app.sell(currency_code=currency, \
                                                          amount=amount)

                base = "USD"
                proceeds = float(amount) * float(rate)

                print(f"Продажа выполнена: "
                      f"{float(amount):.{amount_precision}f} {currency} "
                      f"по курсу {float(rate):.{rate_precision}f} {base}/{currency}"
                      )
                print("Изменения в портфеле:")
                print(f"- {currency}: было "
                      f"{float(old_balance):.{amount_precision}f} "
                      f"-> стало {float(new_balance):.{amount_precision}f}"
                      )
                print(f"Оценочная выручка: {_format_money(proceeds)} {base}")
                continue

            if cmd == "get-rate":
                from valutatrade_hub.infra.settings import SettingsLoader
                settings = SettingsLoader()
                rate_precision = settings.get("RATE_PRECISION", 2)
                
                from_cur = (args.get("from") or "").upper()
                to_cur = (args.get("to") or "USD").upper()
                
                #получаем детальную информацию о курсе
                details = app.get_rate_detailed(currency_code=from_cur, \
                                                base_currency=to_cur)
                
                #форматируем вывод
                print(f"Курс {details['from']} → {details['to']}: "
                      f"{details['rate']:.2f} (обновлено: {details['updated_at']})"
                      )
                print(f"Обратный курс {details['to']} → {details['from']}: "
                      f"{details['rate_inverse']:.6f}"
                      )
                continue

        #обработка исключений
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
            continue
            
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print("Доступные валюты: USD, EUR, GBP, RUB, BTC, ETH, SOL")
            continue
            
        except ApiRequestError as e:
            print(f"Ошибка: {e}")
            print("Повторите попытку позже или проверьте подключение к интернету.")
            continue
            
        except NotLoggedInError as e:
            print(f"Ошибка: {e}")
            continue
            
        except AuthError as e:
            print(f"Ошибка: {e}")
            continue
            
        except WalletAppError as e:
            print(f"Ошибка: {e}")
            continue
            
        except ValueError as e:
            print(f"Ошибка: {e}")
            continue
            
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            continue

        #Parser Service
        if cmd == "update-rates":
            source = (args.get("source") or "").strip().lower() or None

            try:
                updater, storage = _init_parser()
                updater.run_update(source=source)

            except ApiRequestError as e:
                print(f"ERROR: {e}")

            continue

        if cmd == "show-rates":
            try:
                updater, storage = _init_parser()
                cache = storage.load()

                if not cache or "pairs" not in cache:
                    print("Локальный кеш курсов пуст. "
                          "Выполните 'update-rates', чтобы загрузить данные."
                          )
                    continue

                pairs: Dict[str, Any] = cache.get("pairs", {})
                updated_at = cache.get("last_refresh", "")

                currency = (args.get("currency") or "").upper().strip()
                base = (args.get("base") or "").upper().strip()
                top_raw = args.get("top") or ""
                top_n = _safe_int(top_raw) if top_raw else None

                items: List[Tuple[str, float]] = []
                for pair, obj in pairs.items():
                    p = str(pair).upper()
                    if currency and not (p.startswith(currency + "_") \
                                         or p.endswith("_" + currency)):
                        continue
                    if base and not p.endswith("_" + base):
                        continue
                    try:
                        items.append((p, float(obj.get("rate", 0.0))))
                    except Exception:
                        continue

                if not items:
                    if currency:
                        print(f"Курс для '{currency}' не найден в кеше.")
                    else:
                        print("В кеше нет данных по заданным фильтрам.")
                    continue

                if top_n is not None:
                    items.sort(key=lambda x: x[1], reverse=True)
                    items = items[:top_n]
                else:
                    items.sort(key=lambda x: x[0])

                print(f"Rates from cache (updated at {updated_at}):")
                for k, v in items:
                    print(f"- {k}: {v}")

            except ValueError as e:
                print(f"Ошибка: {e}")
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")

            continue

        print("Неизвестная команда. Напишите 'help'.")