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

- **Backend**: FastAPI, SQLite
- **Frontend**: Streamlit
- **Testing**: pytest, pytest-cov
- **Quality**: flake8, bandit, radon, locust
- **CI/CD**: GitHub Actions

## Development & Contribution

### Prerequisites
- Python 3.10+
- Poetry

### Setup

```bash
# Clone repository
git clone https://github.com/DeliverInno/deliverinno.git
cd deliverinno

# Switch to dev branch
git checkout dev

# Install dependencies
poetry install # if you have some problem, add --no-root

# Install pre-commit hooks
poetry run pre-commit install
```

## How to Run (for Users)

**Requirements:**
Docker and Docker Compose must be installed.

### 1. Clone the repository and switch to the main branch

```bash
git clone https://github.com/DeliverInno/deliverinno.git
cd deliverinno
git checkout main
```
### 2 Run with Docker
```
docker compose up --build
```

Access:
- **Frontend (Streamlit)**: http://localhost:8501
- **Backend (FastAPI)**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs

## Project Structure

```
deliverinno/
├── .github/workflows/        # CI/CD pipeline
├── src/
│   ├── api/                  # FastAPI application
│   │   ├── main.py
│   │   ├── dependencies.py   # JWT auth, DB connections
│   │   └── routers/          # Endpoints (auth, buyer, seller)
│   ├── core/
│   │   └── database.py       # SQLite setup
│   ├── services/
│   │   ├── buyer_service.py
│   │   └── seller_service.py
│   ├── shared/models/        # Pydantic models
│   └── streamlit/            # Streamlit frontend
│       ├── streamlit_app.py
│       ├── login.py
│       ├── register.py
│       ├── config.py
│       ├── buyer/            # Buyer pages
│       └── seller/           # Seller pages
├── tests/
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── e2e/                  # End-to-end tests
│   ├── streamlit/            # Streamlit component tests
│   └── performance/          # Load tests
├── data/                     # SQLite database
├── .bandit                   # Bandit security config
├── .dockerignore             # Docker ignore rules
├── .flake8                   # Flake8 linting config
├── .gitignore               # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hooks config
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Docker image definition
├── LICENSE                  # MIT License
├── poetry.lock              # Locked dependency versions
├── pyproject.toml           # Poetry dependencies & config
├── pytest.ini               # pytest configuration
└── README.md                # This file
```

## Database

### Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts (seller/buyer) |
| `products` | Product catalog |
| `cart_items` | Shopping cart items |
| `orders` | Order headers |
| `order_items` | Order line items with snapshot pricing |

### Working with the Database

View database contents:
```bash
sqlite3 data/deliverinno.db
.tables
SELECT * FROM users;
.quit
```

Reset database:
```bash
rm data/deliverinno.db
docker compose down && docker compose up --build
```

## API Endpoints

### Auth
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token

### Buyer
- `GET /buyer/products` - Get all available products
- `GET /buyer/cart` - Get cart contents
- `POST /buyer/cart` - Add item to cart
- `GET /buyer/orders` - Get order history
- `POST /buyer/orders` - Place order

### Seller
- `GET /seller/products` - Get your product
- `POST /seller/products` - Create product
- `PUT /seller/products/{id}` - Update product
- `DELETE /seller/products/{id}` - Delete product

### Service
- `GET /health` - Health check

**Full documentation**: http://localhost:8000/docs

### Seller Flow

1. **Register as seller**
   - Go to the registration page, choose "seller" role.
   - After registration, you are automatically logged in and redirected to the seller dashboard.

2. **Add product**
   - On the dashboard, fill in product name, description, price, and quantity.
   - Click "Create" to add the product to your catalog.

3. **Edit product**
   - In the product list, click "Edit" next to a product.
   - Update details and save changes.

4. **Delete product**
   - In the product list, click "Delete" to remove a product from your catalog.

---

### Buyer Flow

1. **Register as buyer**
   - Go to the registration page, choose "buyer" role.
   - After registration, you are automatically logged in and redirected to the buyer catalog.

2. **Browse products**
   - View the catalog of available products (with quantity > 0).

3. **Add to cart**
   - Click "Add to cart" on a product card.
   - Specify quantity and confirm.

4. **View cart**
   - Open the "Shopping cart" page to see all items added.

5. **Place order**
   - On the cart page, click "Make order" to create an order from the cart.
   - The cart will be cleared after a successful order.

6. **View order history**
   - Go to the "Order history" page to see all previous orders and their statuses.

## Testing

```bash
# Run all tests with coverage
poetry run pytest tests/ --cov=src --cov-fail-under=80 -v

# Run specific test suites
poetry run pytest tests/unit/ -v          # Unit tests
poetry run pytest tests/integration/ -v   # Integration tests
poetry run pytest tests/e2e/ -v          # E2E tests
```

## Quality Checks

```bash
# Style check
poetry run flake8 src/

# Security scan
poetry run bandit -r src/ -ll

# Complexity analysis
poetry run radon cc -a -s src/

# Maintainability index
poetry run radon mi -s src/

# Performance Testing for Windows
.\tests\performance\run_perf.ps1C

# Performance Testing for Mac/Linux
.\tests\performance\run_perf.sh
```

## Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| demo_seller | demo123 | Seller |
| demo_buyer | demo123 | Buyer |

## Git Workflow

```bash
# Make changes
git add .

# Commit (pre-commit hooks will run)
git commit -m "Your message"

# Skip hooks if needed (not recommended)
git commit --no-verify -m "message"
```

## Troubleshooting

**Port already in use?**
```bash
lsof -i :8000
kill -9 <PID>
```

**Database locked?**
```bash
rm data/deliverinno.db
docker compose restart
```

**Dependency conflicts?**
```bash
poetry cache clear . --all
poetry install --no-cache
```

---
