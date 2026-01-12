# ValutaTrade Hub

**Учебный проект торговой платформы для управления криптовалютами и фиатными валютами.**

## Описание

ValutaTrade Hub — это это комплексная платформа, которая позволяет пользователям регистрироваться, управлять своим виртуальным портфелем фиатных и криптовалют, совершать сделки по покупке/продаже, а также отслеживать актуальные курсы в реальном времени. 

## Старт

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/leonid6011/finalproject_Krylasov_Leonid_M25-555
cd 
```

2. Установите зависимости:
```bash
make install
# или
poetry install
```

3. Настройте API-ключ для фиатных валют:
```bash
export EXCHANGERATE_API_KEY="ваш_ключ_с_exchangerate-api.com"
```

4. Запустите приложение:
```bash
make project
# или
poetry run project
```

## Демонстрация
[![asciicast](https://asciinema.org/a/3oGVnbiCcyMYACZu.svg)](https://asciinema.org/a/3oGVnbiCcyMYACZu)

## Структура проекта

```
finalproject_fixed/
├── pyproject.toml              # Конфигурация Poetry
├── Makefile                    # Команды для разработки
├── .gitignore                  # Исключения для Git
├── main.py                     # Точка входа
├── README.md                   # Документация
├── data/                       # Данные
│   ├── users.json              # Пользователи
│   ├── portfolios.json         # Портфели
│   ├── rates.json              # Кэш курсов
│   └── exchange_rates.json     # История курсов
├── logs/                       # Логи
│   └── actions.log             # Логи действий
└── valutatrade_hub/
    ├── cli/                    # CLI интерфейс
    ├── core/                   # Бизнес-логика
    ├── infra/                  # Инфраструктура
    ├── parser_service/         # Сервис обновления курсов
    ├── decorators.py           # Декораторы
    └── logging_config.py       # Настройка логирования
```

## Использование

### Основные команды

#### Регистрация и вход
```bash
> register --username alice --password 1234
> login --username alice --password 1234
```

#### Обновление курсов валют
```bash
> update-rates # все курсы
> update-rates --source coingecko # только криптовалюты
> update-rates --source exchangerate # только фиатные валюты
```

#### Просмотр курсов
```bash
> show-rates # все курсы
> show-rates --currency BTC # курс для BTC
> show-rates --top 3 # топ-3 курса по обороту
> show-rates --base EUR # курс в EUR
```

#### Получение курса пары
```bash
> get-rate --from BTC # BTC к USD
> get-rate --from EUR --to BTC # EUR к BTC
```

#### Покупка и продажа
```bash
> buy --currency BTC --amount 0.05 # купить 0.05 BTC
> sell --currency BTC --amount 0.05 # продать 0.05 BTC
```
#### Портфель
```bash
> show-portfolio # в USD
> show-portfolio --base EUR # в EUR
```
#### Выход
```bash
> logout
> exit
```
## Логирование

Все действия логируются в `logs/actions.log`:

## Поддерживаемые валюты

**Фиатные:** USD, EUR, GBP, RUB  
**Криптовалюты:** BTC, ETH, SOL

## Безопасность

- Пароли хешируются (SHA-256 + соль)
- Валидация всех входных данных

## Обработка ошибок

Все исключения обрабатываются с понятными сообщениями:
- `InsufficientFundsError` — недостаточно средств
- `CurrencyNotFoundError` — неизвестная валюта
- `ApiRequestError` — ошибка API
- `NotLoggedInError` — не авторизован

## Автор
Леонид Крыласов
