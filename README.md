# Backend System – Online Shop

**Backend system** for managing an online shop, built with Python and FastAPI.
Supports clients, products, orders, and transactions, demonstrating **CRUD operations**, **JWT authentication**, **database migrations** with Alembic, and **clean backend architecture**.

---

## Technologies
- Python 3.11
- FastAPI
- SQLAlchemy (async ORM)
- Alembic (Database migrations)
- PostgreSQL
- Docker & Docker Compose
- Redis (caching)
- JWT (PyJWT)
- bcrypt / passlib

---

## Project Structure

```
├── app/              # Routers (FastAPI endpoints)
├── services/         # Business logic
├── repositories/     # Database queries
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── core/             # Config, custom exceptions
├── database/         # Session, Unit of Work
├── utils/            # Password hashing, JWT dependencies
├── alembic/          # Migrations
├── Dockerfile
└── docker-compose.yml
```

---

## Key Concepts Demonstrated
- Clean Architecture: Repository + Service pattern
- Async backend with SQLAlchemy + PostgreSQL
- Unit of Work pattern
- JWT authentication (register, login, protected endpoints)
- Password hashing with bcrypt
- CRUD operations for clients, products, orders, and transactions
- Database migrations with Alembic
- Dockerized environment

---

## How to Run

1. **Clone the repository**
```bash
git clone https://github.com/bogdan0089/OnlineShop.git
cd "Project Online Shop"
```

2. **Create virtual environment**
```bash
python -m venv .venv
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
```

4. **Run with Docker**
```bash
docker compose up --build
```

API available at: `http://localhost:8000/docs`


## API Endpoints

Auth:
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /auth/register | 🔓 | Register new client |
| POST | /auth/client_login | 🔓 | Login, get access + refresh token |
| POST | /auth/refresh | 🔓 | Refresh access token |

Client:
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /client/create_client | 🔓 | Create client |
| GET | /client/me | 🔒 | Get my profile |
| GET | /client/me/stats | 🔒 | My statistics (orders, spent) |
| GET | /client/me/orders | 🔒 | My orders |
| GET | /client/all_clients | 🔓 | List all clients |
| GET | /client/{id} | 🔒 | Get client by ID |
| PUT | /client/{id} | 🔒 | Update client |
| DELETE | /client/{id} | 🔒 | Delete client |
| POST | /client/{id}/deposit | 🔒 | Deposit balance |
| POST | /client/{id}/withdraw | 🔒 | Withdraw balance |
| GET | /client/{id}/orders/count | 🔒 | Count client orders |

Product: 
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /product/ | 🔓 | Create product |
| GET | /product/all | 🔓 | List all products |
| GET | /product/search?name= | 🔓 | Search by name |
| GET | /product/filter?min_price=&max_price= | 🔓 | Filter by price |
| GET | /product/{id} | 🔓 | Get product by ID |
| PUT | /product/{id} | 🔓 | Update product |
| DELETE | /product/{id} | 🔓 | Delete product |

Order:
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /order/create_orders | 🔓 | Create order |
| POST | /order/orders | 🔒 | Create order with product |
| GET | /order/get_orders | 🔓 | List orders (pagination) |
| GET | /order/orders/{id} | 🔒 | Get order by ID |
| PUT | /order/order_update/{id} | 🔒 | Update order title |
| PUT | /order/{id}/status | 🔒 | Update order status |
| GET | /order/order/{id}/total_price | 🔒 | Get order total price |
| GET | /order/order_with_products/{id} | 🔒 | Order with products |
| POST | /order/{id}/products/{product_id} | 🔒 | Add product to order |
| DELETE | /order/{id}/order/{product_id}/product | 🔒 | Remove product from order |
| POST | /order/{id}/checkout | 🔒 | Checkout order |
| POST | /order/{id}/refund | 🔒 | Cancel order with refund |

Transaction:
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /transaction/create_transaction | 🔓 | Create transaction |
| GET | /transaction/me/transactions | 🔒 | My transactions (pagination) |
| GET | /transaction/{id} | 🔒 | Get transaction by ID |
| GET | /transaction/{client_id}/transactions | 🔒 | Client transactions |