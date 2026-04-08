# DeliverInno

A simple delivery-style web application with seller and buyer functionality.

## Team

- **Sofia Palkina** - [s.palkina@innopolis.university](mailto:s.palkina@innopolis.university)
- **Amir Bairamov** - [a.bairamov@innopolis.university](mailto:a.bairamov@innopolis.university)
- **Polina Kostikova** - [p.kostikova@innopolis.university](mailto:p.kostikova@innopolis.university)
- **Bulat Gazizov** - [b.gazizov@innopolis.university](mailto:b.gazizov@innopolis.university)

## Features

### Sellers

- Register/Login
- Add, edit, and delete products
- Manage inventory

### Buyers

- Register/Login
- Browse products
- Shopping cart
- Place orders
- Order history

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Streamlit
- **Testing**: pytest, pytest-cov
- **Quality**: flake8, bandit, radon
- **CI/CD**: GitHub Actions

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry

### Installation and commands

```powershell
# Clone repository
https://github.com/DeliverInno/deliverinno.git
cd deliverinno

# Switch to dev branch
git checkout dev

# Install dependencies
poetry install # if you have some problem in this step, add --no-root

# Install pre-commit hooks
poetry run pre-commit install

# after you add your code
git add .
git commit -m "Your message"
# Skip hooks temporarily (not recommended)
git commit --no-verify -m "message"
```

## How to run

```bash
docker compose up --build
```

### Access application

- Frontend (Streamlit): http://localhost:8501

- Backend (FastAPI): http://localhost:8000

- API Docs (Swagger): http://localhost:8000/docs

## Project Structure (real)

```
deliverinno/
├── .github/
│   └── workflows/
├── src/
│   ├── __init__.py
│   ├── api/                       # FastAPI приложение
│   └── streamlit/                 # Streamlit frontend
├── tests/
│   ├── __init__.py
│   ├── unit/                      # Unit тесты
│   ├── integration/               # Интеграционные тесты API
│   ├── e2e/                       # Сквозные тесты (Streamlit)
│   ├── performance/               # Load testing
├── data/                          # Данные приложения
├── .flake8                        # Flake8 конфигурация
├── .bandit                        # Bandit конфигурация
├── .pre-commit-config.yaml        # Pre-commit hooks
├── .gitignore
├── pyproject.toml                 # Poetry конфигурация
├── README.md

```

## Project Structure (ideal)

```
deliverinno/
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI/CD pipeline
├── src/
│   ├── __init__.py
│   ├── api/                       # FastAPI приложение
│   │   ├── __init__.py
│   │   ├── main.py                # Точка входа FastAPI
│   │   ├── dependencies.py        # Dependency injection
│   │   ├── routers/               # Эндпоинты по модулям
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # /auth endpoints
│   │   │   ├── products.py        # /products endpoints
│   │   │   ├── cart.py            # /cart endpoints
│   │   │   └── orders.py          # /orders endpoints
│   │   └── models/                # Pydantic схемы (request/response)
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── product.py
│   │       ├── cart.py
│   │       └── order.py
│   ├── core/                      # Бизнес-логика и доменные модели
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite и SQLAlchemy setup
│   │   ├── config.py              # Настройки приложения
│   │   ├── security.py            # Хэширование паролей, JWT
│   │   └── exceptions.py          # Кастомные исключения
│   ├── models/                    # SQLAlchemy модели (ORM)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   └── order.py
│   ├── services/                  # Сервисный слой (бизнес-логика)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── cart_service.py
│   │   └── order_service.py
│   ├── repositories/              # Слой доступа к данным
│   │   ├── __init__.py
│   │   ├── base.py                # Базовый репозиторий
│   │   ├── user_repository.py
│   │   ├── product_repository.py
│   │   ├── cart_repository.py
│   │   └── order_repository.py
│   └── streamlit/                 # Streamlit frontend
│       ├── __init__.py
│       ├── app.py                 # Главный entry point Streamlit
│       ├── pages/                 # Многостраничный интерфейс
│       │   ├── seller_dashboard.py
│       │   ├── buyer_catalog.py
│       │   ├── cart.py
│       │   └── orders.py
│       ├── components/            # Переиспользуемые UI компоненты
│       │   ├── auth.py
│       │   └── product_card.py
│       └── utils/                 # Streamlit-specific утилиты
│           ├── session.py         # Управление сессиями
│           └── api_client.py      # Клиент для вызова FastAPI
├── tests/
│   ├── __init__.py
│   ├── unit/                      # Unit тесты
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   │   ├── test_product_service.py
│   │   │   └── test_cart_service.py
│   │   └── test_models/
│   │       └── test_validation.py
│   ├── integration/               # Интеграционные тесты API
│   │   ├── __init__.py
│   │   ├── test_auth_api.py
│   │   ├── test_products_api.py
│   │   ├── test_cart_api.py
│   │   └── test_orders_api.py
│   ├── e2e/                       # Сквозные тесты (Streamlit)
│   │   ├── __init__.py
│   │   ├── test_seller_flow.py    # Seller добавляет продукт
│   │   ├── test_buyer_flow.py     # Buyer покупает продукт
│   │   └── conftest.py            # Фикстуры для e2e
│   ├── performance/               # Load testing
│   │   └── locustfile.py
│   └── docs/                      # Тесты документации
│       └── test_openapi.py
├── migrations/                    # Alembic миграции (если понадобятся)
│   └── versions/
├── data/                          # Данные приложения
│   └── deliverinno.db             # SQLite файл (gitignored)
├── .github/
│   └── workflows/
│       └── ci.yml
├── .flake8                        # Flake8 конфигурация
├── .bandit                        # Bandit конфигурация
├── .pre-commit-config.yaml        # Pre-commit hooks
├── .gitignore
├── pyproject.toml                 # Poetry конфигурация
├── README.md
└── RELEASE_CHANGELOG.md


```

## Database

### Table Details

#### `users`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `username` | TEXT | Unique username for login |
| `password` | TEXT | SHA-256 hashed password |
| `role` | TEXT | 'seller' or 'buyer' |
| `created_at` | TIMESTAMP | Registration date |

#### `products`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `name` | TEXT | Product name |
| `description` | TEXT | Product description |
| `price` | REAL | Price per unit (≥ 0) |
| `quantity` | INTEGER | Available stock (≥ 0) |
| `seller_id` | INTEGER | Foreign key to `users.id` |
| `created_at` | TIMESTAMP | Creation date |

#### `cart_items`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `user_id` | INTEGER | Foreign key to `users.id` |
| `product_id` | INTEGER | Foreign key to `products.id` |
| `quantity` | INTEGER | Quantity in cart (> 0) |
| `added_at` | TIMESTAMP | When added to cart |

**Unique constraint**: `(user_id, product_id)` - one item per product per user

#### `orders`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `user_id` | INTEGER | Foreign key to `users.id` |
| `total_amount` | REAL | Total order amount (≥ 0) |
| `status` | TEXT | 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled' |
| `created_at` | TIMESTAMP | Order date |

#### `order_items`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `order_id` | INTEGER | Foreign key to `orders.id` |
| `product_id` | INTEGER | Foreign key to `products.id` |
| `quantity` | INTEGER | Quantity ordered (> 0) |
| `price_at_time` | REAL | Price at purchase time (snapshot) |

### Working with the Database

#### View Database Contents

SQLite CLI

```bash
sqlite3 data/deliverinno.db
# Then run SQL commands:
.tables
SELECT * FROM users;
.quit
```

### Reset Database

```
# Delete the database file
rm data/deliverinno.db

# Restart the app (will recreate with demo users)
poetry run uvicorn src.api.main:app --reload
```
