# FastAPI E-Commerce Backend

![CI](https://github.com/bogdan0089/fastapi-ecommerce-backend/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?logo=stripe&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?logo=amazonaws&logoColor=white)

Production-ready async REST API for a full-featured e-commerce platform. Built with FastAPI and PostgreSQL, it covers the complete shopping flow — from browsing and cart management to checkout, payments, and order tracking — with JWT auth, RBAC, Redis caching, Celery async tasks, Stripe payments, real-time WebSocket notifications, and AI-powered features via Google Gemini.

**Live demo:** https://bohdan-shop.duckdns.org  
**Swagger UI:** https://bohdan-shop.duckdns.org/docs  
**Frontend repo:** https://github.com/bogdan0089/ecommerce-frontend

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 + FastAPI | Async web framework |
| PostgreSQL 15 + SQLAlchemy 2.0 | Async ORM + database |
| Alembic | Database migrations |
| Redis 7 | Caching + Celery result backend |
| RabbitMQ | Celery message broker |
| Celery | Background email tasks |
| PyJWT + bcrypt / passlib | Authentication + password hashing |
| Stripe | Payment processing |
| WebSocket | Real-time admin notifications |
| Google Gemini | AI search, recommendations, chat, product descriptions |
| Docker + Docker Compose | Containerization |
| GitHub Actions | CI/CD — automated testing and deployment to AWS EC2 |

---

## Project Structure

```
fastapi-ecommerce-backend/
├── app/              # Routers — HTTP endpoints only, no business logic
├── services/         # Business logic — all @staticmethod methods
├── repositories/     # Raw SQLAlchemy queries only
├── models/           # ORM models: Client, Order, Product, Transaction, Category, OrderProduct
├── schemas/          # Pydantic v2 — request validation and response serialization
├── core/             # Config, 30+ custom exceptions, enums (Role, OrderStatus, etc.), shared field validators
├── database/         # Async session, Unit of Work pattern
├── utils/            # JWT dependencies, WebSocket connection manager, structured logger
├── alembic/          # Database migrations
├── tests/            # pytest integration tests
├── celery_app.py     # Celery tasks (email sending)
├── Dockerfile
└── docker-compose.yml
```

---

## Architecture

```
Router → Service → UnitOfWork → Repository → DB
```

- **Router** — handles HTTP only, delegates everything to services
- **Service** — all business logic, `@staticmethod` methods, always uses `UnitOfWork`
- **UnitOfWork** — async context manager, opens session, auto-commits on success, auto-rollbacks on exception
- **Repository** — raw SQLAlchemy queries, no logic
- **Models** — 6 ORM models with One-to-Many and Many-to-Many relationships

---

## Key Features

- **Auth & Security** — JWT access + refresh token flow, bcrypt, email verification via UUID token stored in Redis (24h TTL), forgot/reset password via email
- **RBAC** — 3 roles (`client` / `moderator` / `superadmin`) with role-based endpoint protection
- **Product Moderation** — `pending → accept / rejected` workflow, reviewed by moderator or superadmin
- **Soft Delete** — clients soft-deleted via `is_active` flag; data preserved, hidden from all queries
- **Caching** — Redis with 60s TTL on list/stats endpoints, wildcard invalidation on every write
- **Pagination** — all list endpoints support `limit` and `offset`
- **Order Flow** — checkout validates stock, deducts balance, creates `purchase` transaction; refund restores balance and creates `refund` transaction
- **Stripe Payments** — PaymentIntent flow; client creates intent, Stripe confirms via webhook, balance topped up automatically
- **WebSocket** — persistent admin connection, broadcasts checkout notifications to all connected admins in real time
- **Async Tasks** — Celery + RabbitMQ for background email sending (verification, password reset, order status change)
- **Product Quantity** — checkout validates available stock, returns HTTP 400 if insufficient
- **Pessimistic Locking** — `SELECT ... FOR UPDATE` on all balance-changing operations to prevent race conditions
- **Order State Machine** — enforced transitions (`pending → completed / cancelled`, `completed → cancelled` only)
- **Rate Limiting** — Redis-based per-IP counter on login and forgot-password endpoints; max 5 requests / 60s, returns HTTP 429
- **AI Integration** — Google Gemini powers 4 features: semantic product search that returns the matching products themselves, personalized recommendations from purchase history, a store assistant chatbot, and AI-generated product descriptions for admins
- **Structured Logging** — `utils/logger.py` with `get_logger` utility outputs timestamped logs to stdout; all services log key business events at `INFO` level, not-found cases at `WARNING`; plain reads are intentionally skipped to keep logs clean
- **CI/CD** — GitHub Actions runs ruff, migration checks and 104 integration tests on every push and PR; on merge to `main` automatically deploys to AWS EC2 via SSH

---

## CI/CD Pipeline

```
git push / pull request
        ↓
GitHub Actions — CI
  • spins up PostgreSQL 15 + Redis 7 + RabbitMQ 3
  • runs ruff
  • runs alembic migrations, then alembic check
  • downgrades to base and upgrades again
  • runs pytest (104 tests)
        ↓
merge to main
        ↓
deploy job in the same workflow, gated on lint + test
  • connects to AWS EC2 via SSH
  • git pull origin main
  • docker compose up --build -d
```

---

## Data Models

| Model | Description |
|-------|-------------|
| `Client` | User account with balance, role, soft-delete |
| `Product` | Product with status, quantity, category |
| `Order` | Order with state machine, linked to client |
| `OrderProduct` | M2M — order ↔ products with quantity |
| `Transaction` | Financial record (deposit / withdraw / purchase / refund) |
| `Category` | Product category |

---

## Balance and the demo top-up

Real money goes through Stripe: the client creates a PaymentIntent, Stripe
confirms it, and the webhook credits the balance.

`POST /client/{id}/deposit` credits a balance without any payment. A client may
call it for their own account, and only for their own — anyone else's requires
superadmin. This is deliberate: the project is a portfolio build with no real
checkout, and reviewers need a way to try the cart, checkout and refund flow
without entering card details. The frontend exposes it as "Demo top-up" next to
the Stripe form, labelled as such.

If this ever becomes a real store, restrict both `/deposit` and `/withdraw` to
superadmin and leave Stripe as the only way in.

---

## Roles

| Role | Access |
|------|--------|
| `client` | Own resources only |
| `moderator` | Moderate products (approve / reject) |
| `superadmin` | Full access to all resources + WebSocket admin panel |

> First superadmin must be set directly in the database:
> ```sql
> UPDATE clients SET role='superadmin' WHERE email='your@email.com';
> ```

---

## API Endpoints

> 🔓 Public &nbsp; 🔒 Authenticated &nbsp; 🔑 Superadmin &nbsp; 🛡 Moderator (superadmin or moderator)

**Auth**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /auth/register | 🔓 | Register new client |
| POST | /auth/client_login | 🔓 | Login — returns access + refresh token |
| POST | /auth/refresh | 🔓 | Refresh access token |
| POST | /auth/change_password | 🔒 | Change password |
| POST | /auth/change_role/{client_id} | 🔑 | Change client role |
| GET | /auth/verify/{token} | 🔓 | Verify email |
| POST | /auth/resend_verification | 🔓 | Send the verification link again |
| POST | /auth/forgot_password | 🔓 | Send password reset email |
| POST | /auth/reset_password | 🔓 | Reset password via token |

**Client**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | /client/me | 🔒 | Get my profile |
| GET | /client/me/stats | 🔒 | My stats (orders, total spent, balance) |
| GET | /client/me/orders | 🔒 | My orders with pagination |
| GET | /client/get_clients | 🔑 | List all clients |
| GET | /client/{id} | 🔒 | Get client by ID |
| PUT | /client/{id} | 🔒 | Update name / age / address |
| DELETE | /client/{id} | 🔒 | Soft delete account |
| POST | /client/{id}/deposit | 🔒 | Credit own balance — demo top-up, see note below |
| POST | /client/{id}/withdraw | 🔒 | Debit own balance |
| GET | /client/{id}/orders/count | 🔒 | Count client orders |

**Product**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /product/ | 🔒 | Create product (status: pending) |
| GET | /product/all | 🔓 | List accepted products |
| GET | /product/admin/all | 🔑 | List all products (any status) |
| GET | /product/search?name= | 🔓 | Search by name |
| GET | /product/filter?min_price=&max_price= | 🔓 | Filter by price range |
| GET | /product/color/{color} | 🔓 | Filter by color |
| GET | /product/{id} | 🔓 | Get product by ID |
| PUT | /product/{id} | 🔑 | Update product |
| DELETE | /product/{id} | 🔑 | Delete product |
| PATCH | /product/{id}/moderate | 🛡 | Approve or reject product |

**Order**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /order/create_orders | 🔒 | Create empty order |
| POST | /order/orders | 🔒 | Create order with product |
| GET | /order/get_orders | 🔑 | List all orders |
| GET | /order/{id}/orders | 🔒 | Get order by ID |
| PUT | /order/order_update/{id} | 🔒 | Update order title |
| PUT | /order/{id}/status | 🔒 | Update order status |
| GET | /order/order/{id}/total_price | 🔒 | Get order total |
| GET | /order/order_with_products/{id} | 🔒 | Order with products list |
| POST | /order/{id}/products/{product_id} | 🔒 | Add product to order |
| DELETE | /order/{id}/order/{product_id}/product | 🔒 | Remove product from order |
| POST | /order/{id}/checkout | 🔒 | Checkout — deducts balance, validates stock |
| POST | /order/{id}/refund | 🔒 | Cancel order and refund balance |

**Transaction**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | /transaction/me/transactions | 🔒 | My transactions |
| GET | /transaction/{id} | 🔒 | Get transaction by ID |
| GET | /transaction/{client_id}/transactions | 🔒 | Client transactions |

**Payment (Stripe)**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /payment/create | 🔒 | Create PaymentIntent, returns client_secret |
| POST | /payment/webhook | 🔓 | Stripe webhook — tops up balance on success |

**Category**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /category/create | 🔑 | Create category |
| GET | /category/admin | 🔓 | List all categories |

**AI**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | /ai/recommendations | 🔒 | Personalized recommendations based on purchase history |
| GET | /ai/search?q= | 🔒 | Semantic AI search across product catalog |
| POST | /ai/chat | 🔒 | Store assistant chatbot |
| POST | /ai/generate-description | 🔑 | AI-generated product description for admin |

**WebSocket**
| Type | URL | Auth | Description |
|------|-----|------|-------------|
| WS | /ws/admin?token= | 🔑 JWT in query | Real-time checkout notifications for admins |

---

## Running Locally

**1. Clone and configure**
```bash
git clone https://github.com/bogdan0089/fastapi-ecommerce-backend.git
cd fastapi-ecommerce-backend
cp .env.example .env
# fill in the required values in .env
```

**2. Start with Docker**
```bash
docker compose up --build
```

API: `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

> Alembic migrations run automatically on startup.

**3. Run tests**
```bash
pytest tests/ -v
```

**4. Stripe webhook (local testing)**
```bash
stripe listen --forward-to localhost:8000/payment/webhook
```

**5. Migrations (manual)**
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
```

---

## Docker Services

| Service | Image | Role |
|---------|-------|------|
| `db` | postgres:15 | Primary database |
| `redis` | redis:7 | Cache + Celery result backend |
| `rabbitmq` | rabbitmq:3 | Celery message broker |
| `backend_system_app` | Dockerfile | Runs migrations then uvicorn on :8000 |
| `celery_worker` | Dockerfile | Runs Celery worker for email tasks |
