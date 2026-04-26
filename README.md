# FastAPI E-Commerce — Backend

**Production-ready REST API** for an e-commerce platform built with Python and FastAPI.  
Features JWT auth, role-based access control, Stripe payments, real-time WebSocket notifications, Redis caching, Celery async tasks, and a full shopping flow from browsing to checkout.

**Live demo:** https://bohdan-shop.duckdns.org  
**Frontend repo:** https://github.com/bogdan0089/ecommerce-frontend

---

## Stack

- Python 3.11 + FastAPI (async)
- PostgreSQL + SQLAlchemy (async ORM) + Alembic (migrations)
- Redis — caching + Celery broker
- Celery — background email tasks
- JWT (PyJWT) + bcrypt / passlib
- Stripe — payment processing
- WebSocket — real-time admin notifications
- Docker & Docker Compose

---

## Project Structure

```
├── app/              # Routers (FastAPI endpoints)
├── services/         # Business logic (all @staticmethod)
├── repositories/     # Raw SQLAlchemy queries
├── models/           # ORM models: Client, Order, Product, Transaction, Category, OrderProduct; association table: client_products
├── schemas/          # Pydantic v2 schemas
├── core/             # Config, custom exceptions, enums
├── database/         # Async session, Unit of Work
├── utils/            # JWT dependencies, connection manager
├── alembic/          # Database migrations
├── tests/            # pytest integration tests
├── celery_app.py     # Celery tasks (email sending)
├── Dockerfile
└── docker-compose.yml
```

---

## Key Concepts Demonstrated

- **Architecture:** Router → Service → Unit of Work → Repository → DB, strict layer separation with no cross-layer dependencies
- **Data Modeling:** 6 ORM models (Client, Order, Product, Transaction, Category, OrderProduct); One-to-Many (Client → Orders, Client → Transactions, Category → Products) and Many-to-Many (Order ↔ Products via OrderProduct with quantity, Client ↔ Products via client_products)
- **Auth & Security:** JWT access + refresh token flow, bcrypt, email verification via UUID token in Redis (24h TTL), forgot/reset password via email
- **RBAC:** 3 roles (client / moderator / superadmin) with role-based endpoint protection
- **Product Moderation:** `pending → accept / rejected` workflow, moderated by moderator or superadmin
- **Soft Delete:** Clients soft-deleted via `is_active` flag — data preserved, client hidden from all queries
- **Caching:** Redis with 60s TTL on list/stats endpoints, wildcard invalidation on every write
- **Pagination:** All list endpoints support `limit` and `offset`
- **Business Logic:** order checkout (balance deduction + purchase transaction), order refund (balance restore + refund transaction)
- **Stripe Payments:** PaymentIntent flow — client creates intent, Stripe confirms via webhook, balance topped up automatically
- **WebSocket:** persistent admin connection, broadcasts checkout notification to all connected admins in real time
- **Async Tasks:** Celery + Redis for background email sending (verification, password reset, order status change)
- **Order Status Emails:** when admin changes order status, client receives an email notification via Celery task
- **Product Quantity:** products have a `quantity` field; checkout validates available stock and raises HTTP 400 if insufficient
- **Password Validation:** minimum 8 characters enforced at registration via Pydantic validator
- **Pessimistic Locking:** `SELECT ... FOR UPDATE` on all balance-changing operations to prevent race conditions
- **Order State Machine:** enforced transitions (`create → completed/cancelled`, `completed → cancelled` only)
- **Rate Limiting:** Redis-based per-IP counter on `/auth/client_login` and `/auth/forgot_password` — max 5 requests / 60s, returns HTTP 429
- **Testing:** pytest integration tests, FakeRedis mock, NullPool async setup

---

## Roles

| Role | Access |
|------|--------|
| `client` | Own resources only |
| `moderator` | Moderate products (approve / reject) |
| `superadmin` | Full access to all resources + WebSocket admin |

> First superadmin must be set directly in the database:
> ```sql
> UPDATE clients SET role='superadmin' WHERE email='your@email.com';
> ```

---

## How to Run Locally

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
docker exec -it api pytest tests/ -v
```

**4. Stripe webhook (local)**
```bash
stripe listen --forward-to localhost:8000/payment/webhook
```

**5. Migrations (manual)**
```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
```

---

## API Endpoints

> 🔓 Public &nbsp; 🔒 Authenticated &nbsp; 🔑 Admin (superadmin) &nbsp; 🛡 Moderator (superadmin or moderator)

**Auth**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /auth/register | 🔓 | Register new client |
| POST | /auth/client_login | 🔓 | Login, returns access + refresh token |
| POST | /auth/refresh | 🔓 | Refresh access token |
| POST | /auth/change_password | 🔒 | Change password |
| POST | /auth/change_role/{client_id} | 🔑 | Change client role |
| GET | /auth/verify/{token} | 🔓 | Verify email |
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
| POST | /client/{id}/deposit | 🔒 | Deposit balance |
| POST | /client/{id}/withdraw | 🔒 | Withdraw balance |
| GET | /client/{id}/orders/count | 🔒 | Count client orders |

**Product**
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /product/ | 🔒 | Create product (status: pending, requires quantity) |
| GET | /product/all | 🔓 | List accepted products |
| GET | /product/admin/all | 🔑 | List all products (any status) |
| GET | /product/search?name= | 🔓 | Search by name |
| GET | /product/filter?min_price=&max_price= | 🔓 | Filter by price |
| GET | /product/color/{color} | 🔓 | Find by color |
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
| POST | /order/{id}/checkout | 🔒 | Checkout (deducts balance) |
| POST | /order/{id}/refund | 🔒 | Cancel and refund order |

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

**WebSocket**
| Type | URL | Auth | Description |
|------|-----|------|-------------|
| WS | /ws/admin?token= | 🔑 JWT in query | Real-time checkout notifications for admins |
