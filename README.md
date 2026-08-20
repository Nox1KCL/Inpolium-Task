# Steam API Service

## Клонування репозиторію

Склонуйте проєкт у зручну директорію:

```
git clone https://github.com/Nox1KCL/Inpolium-Task
cd Inpolium-Task
```

Далі всі команди виконуються із кореня склонованого проєкту (де лежить `pyproject.toml`).

---

## 1. Основні дані про проєкт

Проєкт є асинхронним REST API сервісом для отримання даних з магазину Steam. Реалізовано три методи скрейпінгу: базовий HTTP-запит, headless-браузер для динамічного DOM та non-headless запуск для взаємодії користувача.

### Технологічний стек

- Мова: Python 3.13
- Фреймворк API: FastAPI
- Зберігання даних: PostgreSQL (через asyncpg та SQLAlchemy 2.0)
- Скрейпінг: Playwright (headless & non-headless), HTTPX
- Телеметрія та логування: OpenTelemetry (VictoriaMetrics, Jaeger, Grafana), Loguru
- Пакетний менеджер: uv
- Інфраструктура: Docker, Docker Compose

### Архітектура та основні рішення

| Рішення | Опис |
| :--- | :--- |
| **Modular Routing** | Маршрути розділені за версіями (`api/v1/router.py`) для забезпечення масштабованості. |
| **Dependency Injection** | Сесії бази даних та конфігурації передаються через `Depends()`, що ізолює бізнес-логіку та спрощує тестування. |
| **DTO Pattern** | Використання Pydantic моделей для суворої валідації вхідних даних та серіалізації вихідних (відділення від ORM-моделей). |
| **Background Tasks** | Non-headless браузер запускається у фоновій задачі для уникнення блокування HTTP-відповіді. |
| **Гарантія транзакцій** | Запис в історію та фіксація телеметрії виконуються у блоці `finally`, що гарантує збереження логів навіть при 500-х помилках. |

---

## 2. Підготовка та сетап середовища

### Вимоги до середовища

- Python 3.13+
- PostgreSQL 17+ (для локального запуску)
- Утиліта uv
- Docker та Docker Compose (для контейнеризації)
- ОС: Linux (бажано)

> **Примітка щодо ОС:** Для роботи проєкту рекомендується використовувати Linux. Docker та всі команди нижче (зокрема `cp`, `source`, сценарії запуску) найстабільніше працюють саме під Linux/macOS. Якщо у вас встановлена Windows, рекомендується підняти віртуальну машину з Linux (наприклад, через WSL2 або Hyper‑V/VirtualBox), оскільки Docker-контейнери та shell-команди орієнтовані на Linux-оточення. Під Windows можна використовувати WSL2, де Docker і команди працюватимуть так само, як у звичайному Linux.

### Конфігурація файлів

Перед запуском необхідно налаштувати конфігураційні файли. За замовчуванням програма очікує їх за визначеними шляхами.

1. Створіть файл `.env` у кореневій директорії проєкту на основі `.env.example`:

   ```
   cp .env.example .env
   ```

2. Створіть файл `config.toml` у директорії `src/task/config/` на основі `config-example.toml`:

   ```
   cp src/task/config/config-example.toml src/task/config/config.toml
   ```

> **Примітка:** Файли `.env` та `config.toml` містять чутливі дані та виключені з контролю версій (`.gitignore`). Їх заповнення є обов'язковим.

### Встановлення залежностей

Рекомендується використання пакетного менеджера uv для ізоляції та швидкості.

```
# Встановлення залежностей проєкту згідно з pyproject.toml / uv.lock
uv sync --no-dev

# Активація віртуального середовища
source .venv/bin/activate
```

### Встановлення браузера та системних залежностей

Для коректної роботи Playwright необхідно встановити двійкові файли браузера Chromium.

```
# Встановлення Chromium та необхідних системних бібліотек
uv run playwright install --with-deps chromium
```

## 3. Запуск проєкту

Проєкт підтримує два режими запуску: локальний (необхідний для виконання методу non_headless) та запуск через Docker Compose.

### Варіант А: Локальний запуск (підтримує non-headless вікна)

Оскільки ізольовані Docker-контейнери не мають доступу до графічного сервера хост-системи, для тестування методу відкриття видимого браузера API необхідно запускати локально.

> **Щодо телеметрії:** для коректної роботи телеметрії (Jaeger, VictoriaMetrics, Grafana) локально також варто підняти ці сервіси. API та його метрики використовують OTLP-ендпоінти з `.env` (`TRACES_ENDPOINT` → Jaeger, `METRICS_ENDPOINT` → VictoriaMetrics); якщо вони недоступні, експорт телеметрії буде надсилатись у «нікуди». Саме тому нижче піднімається вся інфраструктура, окрім `app`.

1. Підніміть всю інфраструктуру (PostgreSQL, Jaeger, VictoriaMetrics, Grafana), виключивши сервіс `app`, через Docker Compose:

   ```
   cd deploy
   docker-compose --env-file ../.env up -d --scale app=0
   cd ..
   ```

2. Запустіть FastAPI сервер:

   ```
   cd src
   uv run opentelemetry-instrument uvicorn task.__main__:app --host 0.0.0.0 --port 8000
   ```

### Варіант Б: Запуск через Docker Compose (повна ізоляція)

Цей варіант розгортає повну інфраструктуру: API, PostgreSQL, Jaeger, VictoriaMetrics та Grafana.

> **Увага:** у цьому режимі non_headless сценарій працюватиме у фоні без відображення графічного вікна.

```
cd deploy
docker-compose --env-file=../.env up -d --build
```

Доступні сервіси після запуску:

| Сервіс | URL |
| :--- | :--- |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Grafana (метрики) | http://localhost:3000 |
| Jaeger (трейсинг) | http://localhost:16686 |

## 4. Перелік ендпоїнтів та приклади запитів

Базовий шлях (Base URL): `http://localhost:8000/steam/api/v1`

> **Примітка:** Усі ендпоїнти можна зручно тестувати через Swagger UI за адресою http://localhost:8000/docs — там можна заповнювати параметри та виконувати запити безпосередньо з браузера.

### 1. HTTP пошук без браузера

```
POST /games/search/basic
```

Параметри: `term` (string), `results_limit` (integer).

```
curl -X 'POST' \
  'http://localhost:8000/steam/api/v1/games/search/basic?term=Portal%202&results_limit=5' \
  -H 'accept: application/json' \
  -d ''
```

### 2. Headless-скрейпінг (динамічний DOM)

```
POST /games/search/expanded
```

Параметри: `term` (string), `reviews_count` (integer).
Тіло запиту: JSON словник параметрів (обов'язкове, може бути порожнім `{}`).

```
curl -X 'POST' \
  'http://localhost:8000/steam/api/v1/games/search/expanded?term=Portal%202&reviews_count=3' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### 3. Non-headless браузер

```
POST /games/open
```

Параметри: `term` (string).
Тіло запиту: JSON словник параметрів (обов'язкове, може бути порожнім `{}`).

```
curl -X 'POST' \
  'http://localhost:8000/steam/api/v1/games/open?term=Portal%202' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### 4. Отримання історії

```
GET /history
```

Параметри: `skip` (integer, обов'язковий), `limit` (integer, за замовчуванням 50).

```
curl -X 'GET' \
  'http://localhost:8000/steam/api/v1/history?skip=0&limit=50' \
  -H 'accept: application/json'
```

### 5. Отримання запису за ID

```
GET /history/{history_id}
```

```
curl -X 'GET' \
  'http://localhost:8000/steam/api/v1/history/1' \
  -H 'accept: application/json'
```

## 6. Зупинка та очищення

### Зупинити сервіси (без видалення даних)

```
cd deploy
docker compose down
```

Зупиняє та видаляє контейнери й мережі, але зберігає томи (volumes) — дані PostgreSQL, Grafana, Jaeger та VictoriaMetrics лишаються на місці.

### Зупинити та повністю очистити (видалити всі дані)

```
cd deploy
docker compose down -v
```

Окрім зупинки видаляє також томи, тобто **усі накопичені дані** в PostgreSQL, Grafana, Jaeger та VictoriaMetrics буде втрачено.

### Видалити «порожні» або невикористовувані контейнери, мережі та образи

```
docker system prune
```

Може запросити підтвердження. Використовуй обережно — видаляє невикористані ресурси Docker загалом, а не лише цього проєкту. Щоб прибрати лише образи без томів і «висячих» (dangling) контейнерів, додай відповідні прапори (наприклад, `docker image prune`).
