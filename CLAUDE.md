# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

Async FastAPI shop API: PostgreSQL via asyncpg, Redis cache, RabbitMQ + Celery for mail,
Stripe for top-ups, WebSocket notifications for admins.

The rules each layer must follow are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Commands

```bash
docker compose up --build        # whole stack, API on :8000, needs .env (see .env.example)
pytest tests/                    # suite; creates its own database, see Tests
ruff check .                     # lint, must be clean before a PR
alembic upgrade head             # apply migrations
alembic revision --autogenerate -m "what changed"
alembic downgrade -1             # roll one step back
```

Running the suite outside Docker needs the container names replaced by localhost:

```powershell
$env:DB_HOST="localhost"; $env:REDIS_URL="redis://localhost:6380"
$env:RABBITMQ_URL="amqp://guest:guest@localhost:5672//"
```

## How the pieces talk

```mermaid
flowchart LR
    subgraph Browser
        UI[Next.js 16 SPA<br/>shop · profile · admin]
    end

    subgraph Backend
        API[FastAPI<br/>router → service → UnitOfWork → repository]
        WORKER[Celery worker<br/>Gmail SMTP]
    end

    subgraph Data
        PG[(PostgreSQL 15)]
        REDIS[(Redis 7<br/>cache only)]
        MQ[(RabbitMQ<br/>broker)]
    end

    subgraph External
        STRIPE[Stripe]
        GEMINI[Gemini]
    end

    UI -- HTTPS --> API
    UI -. WSS /ws/admin, superadmin .-> API
    API --> PG
    API -- read, INCR on write --> REDIS
    API -- queues mail --> MQ --> WORKER --> PG
    API -- PaymentIntent --> STRIPE
    STRIPE -- webhook, retried --> API
    API -- search, recommendations, chat, descriptions --> GEMINI
```

Redis is a cache and nothing else: it is not the broker and holds no task results.

## Request flow

Every request walks the same four layers. Nothing skips a layer.

```
HTTP
 │
 ▼
app/router_*.py        endpoints only - validation via DTO, auth via Annotated deps,
 │                     no business logic, no SQL
 ▼
services/*.py          all business rules, @staticmethod, always inside `async with UnitOfWork()`
 │
 ▼
database/unit_of_work  one session + every repository; commits on clean exit, rolls back on error
 │
 ▼
repositories/*.py      SQLAlchemy queries only, no rules, no HTTP
 │
 ▼
PostgreSQL
```

Two rules that the code depends on:

- **The UnitOfWork owns the transaction.** A service never commits by hand.
- **Side effects go after the block.** Mail (`.delay()`), WebSocket broadcasts and cache
  invalidation happen *after* `async with` exits, never inside it - a rollback would
  otherwise have already mailed the client about an order that never existed.

### One request end to end

`POST /order/{id}/checkout` shows every rule above in one trace:

```
router_orders          CurrentClient dependency decodes the JWT, loads the client
   │                   DTO validates the path, nothing else happens here
   ▼
OrderService.checkout
   │
   ├─ async with UnitOfWork() ──────────────── transaction opens
   │     order    = uow.order.get_order(id)         is it mine? already paid?
   │     client   = uow.client.get_client_with_lock  SELECT ... FOR UPDATE
   │     balance >= total                            else NotEnoughMoneyError
   │     client.balance -= total
   │     for line in sorted(lines, key=product_id):  same order everywhere,
   │         uow.product.decrease_stock(...)          so two carts cannot deadlock
   │         line.price_at_purchase = price           what a refund will pay back
   │     uow.transaction.create_transaction(purchase)
   │     order.status = completed
   └─ exit ─────────────────────────────────── COMMIT (or ROLLBACK, and stop here)

   send_order_status_email.delay(...)     ─┐
   send_new_order_notification.delay(...)  ├─ only now: the order is real
   connection.broadcast(...)               │
   cache.invalidate("order")              ─┘  INCR order version
```

Everything below the commit line is unreachable if the transaction failed. That is
the whole reason the side effects sit outside the `async with`.

## Data model

```
Client ──< Order ──< OrderProduct >── Product >── Category
  │                    (quantity,          │
  │                     price_at_purchase) │
  ├──< Transaction                         │
  └──< Review >─────────────────────────────
        unique (client_id, product_id)

client_products   association table, Client <-> Product
ProcessedStripeEvent   event_id PK - the guard against crediting one payment twice
```

`price_at_purchase` is what a refund pays back. The product's current price is irrelevant
by then - it may have changed since the order.

Money is `Numeric(10, 2)` everywhere in the database and `Decimal` in Python. Output DTOs
expose it as `float` so the JSON the frontend receives stays unchanged.

## Layers in detail

| Path | Holds |
|---|---|
| `app/router_*.py` | 10 routers: ai, auth, category, client, orders, payment, products, review, transaction, websocket |
| `app/main.py` | app wiring, CORS, `GET /health` (503 when Postgres or Redis is down) |
| `services/` | business logic |
| `repositories/` | queries: category, client, order, product, review, stripe_event, transaction |
| `models/models.py` | ORM models |
| `schemas/<resource>/` | `input_dto.py` and `output_dto.py`, Pydantic v2, split on purpose |
| `core/exceptions.py` | custom `HTTPException` subclasses - raise these, never a bare `HTTPException` |
| `core/enum.py` | `Role`, `OrderStatus`, `ProductStatus`, `TransactionType` |
| `utils/dependencies.py` | `CurrentClient`, `CurrentAdmin` (superadmin), `CurrentModerator` (superadmin or moderator), `Limit`, `Offset`, `RateLimit` |
| `utils/cache.py` | versioned cache keys |
| `utils/connection_manager.py` | WebSocket fan-out to admins |

**Catalogue** - `GET /product/catalogue` is the one endpoint the shop screen needs: name,
`category_id` and a price range, paged, answering `{items, total, price_ceiling}`. It exists
because the screen used to pull 200 products and filter them in the browser - correct only
while the catalogue stays small. Two queries: the page itself (`joinedload` on the category,
a many-to-one, so it rides along in the same round trip), and one aggregate carrying both the
total and the ceiling. The count applies the price filter so paging is right; the ceiling does
not, so dragging the price slider cannot move the end of its own track.

**Paging** - every list endpoint takes `limit: Limit` and `offset: Offset` from
`utils/dependencies.py`, which bound them to 1..`MAX_PAGE_SIZE` (200) and 0.. and answer 422
outside that. Unbounded, `?limit=1000000` on a public endpoint loaded a million rows into ORM
objects; a negative offset reached Postgres and came back a 500. The ceiling is 200 because
that is the largest page the catalogue screen asks for.

## Auth and roles

JWT via PyJWT. `POST /auth/client_login` takes form data (`username`, `password`) and returns
an access and a refresh token. Login is refused until the client verifies the email
(`is_verified`). Verification and reset links are mailed through Celery, never inline.

Three roles: `client`, `moderator`, `superadmin`. Most routes allow the owner or a superadmin.
Moderators approve products: `pending` → `accept` / `rejected`, and only `accept` products
appear in public listings.

## Caching

Redis, 60s TTL, list endpoints and client stats.

Keys carry the version of their resource: `order:v3:list:limit=10:offset=0`. Writing bumps
the version with one `INCR`, so every key built before becomes unreachable and expires on its
own. Nothing is scanned and nothing is deleted - the previous version walked every key in
the database on each write.

Build keys with `cache.key(namespace, suffix)` and drop them with `cache.invalidate(namespace)`.
Namespaces: `order`, `product`, `client`, `category`, `review`.

## Integrations

**Stripe** - `POST /payment/create` opens a PaymentIntent; `POST /payment/webhook` handles
`payment_intent.succeeded`, credits the balance and records a `deposit` transaction. Stripe
retries until it gets a 2xx, so every event id is written to `processed_stripe_events` with
`ON CONFLICT DO NOTHING` and a repeat delivery credits nothing.

**Celery** - broker is **RabbitMQ**; there is no result backend, because nothing reads the
result of sending mail. Four tasks in `celery_app.py`, all Gmail SMTP, all with backoff
retries and a send timeout. Dispatched with `.delay()` from `auth_service` and `order_service`.

**WebSocket** - `WS /ws/admin?token={jwt}`, superadmin only. `ConnectionManager` broadcasts a
line to every connected admin when an order is checked out.

**Gemini** - four endpoints under `/ai`, all rate limited and client-only. `services/ai/` is
split on purpose: `provider.py` is the `LLMProvider` Protocol the services depend on,
`gemini.py` is the only file that knows the vendor, `prompts.py` holds every instruction,
`ai_service.py` holds the logic. Swapping vendors means one new class; testing means passing
a fake `provider=`.

| Decision | Why |
|---|---|
| REST, not the vendor SDK | `httpx` is already a dependency, the timeout is ours, the payload stays readable. |
| One `httpx.AsyncClient` per process, closed in the app `lifespan` | A client per call discards the connection pool, so every request repeats the TCP and TLS handshake to Google. Measured: 6.1s cold, 1.5s on the reused connection. |
| 429 is **not** retried | A quota window resets in tens of seconds. Retrying inside the request burns the rest of the quota three times faster and still makes the caller wait. 408 and 5xx are retried, three attempts, backoff 0.5s then 1s. |
| `/ai/search` returns products, not prose | The model picks ids against a schema (`responseSchema`), and only ids present in the catalogue survive, so a hallucinated id cannot reach a shopper. |
| Search answers are parsed **before** they are cached | Caching the raw reply meant one malformed answer served the same error for the whole hour of its TTL. |
| AI cache keys carry `cache.version("product")` | The `ai` namespace is not bumped by a product write, so without the stamp a new arrival stayed invisible to search for an hour. |
| Prompts build from `get_catalogue()` rows, not ORM products | Nothing there is returned to a client. Full products plus their categories cost a second query and 100 identity-map entries for text thrown away after the request. `search` is the exception - it returns the products themselves. |
| `purchased_product_names()` is one `DISTINCT` query | Walking client -> orders -> order_products -> product loaded the whole purchase history to produce a handful of names, and grew with every order ever placed. Chat and recommendations are 2 queries each; they were 5. |


## Business rules worth knowing

**Checkout** - order must be unpaid, balance must cover the total, stock is taken with an
atomic `UPDATE ... WHERE quantity >= :qty` and rows are locked in `product_id` order so two
orders sharing products cannot deadlock. Each line records `price_at_purchase`.

**Refund** - only a `completed` order; pays back `price_at_purchase`, returns stock, writes a
`refund` transaction, marks the order `cancelled`.

**Client delete** - soft: `is_active=false`, and every query filters on it.

## Tests

`pytest tests/` drops and recreates `{DB_NAME}_test` and builds the schema from the models,
so a run never sees what an earlier run left behind. The development database is never touched.

Fixtures in `tests/conftest.py`: `client` (TestClient), `new_client` (registers and verifies),
`auth_headers`, and `admin_headers` in the files that need it. Redis is `FakeRedis` and Celery
tasks are `RecordingTask` - without the stub the suite opens a real AMQP connection, hangs on
retries, and sends real mail when a broker is up.

`FakeRedis` answers `None` to every read, so tests can never prove anything about caching.
`tests/cache_tests.py` uses its own in-memory fake for that instead.

## CI/CD

`.github/workflows/ci.yml`: **lint** (ruff) and **test** (`alembic upgrade head`,
`alembic check`, a full `downgrade base` round trip, then pytest on a throwaway Postgres),
then **deploy**, which needs both and runs only on a push to `main`. Deploy pulls and rebuilds
on EC2 over SSH.

## Docker services

| Service | Image | Role |
|---|---|---|
| `db` | postgres:15 | database, `pgdata` volume |
| `redis` | redis:7 | cache |
| `rabbitmq` | rabbitmq:3-management | Celery broker, UI on :15672 |
| `api` | Dockerfile | `alembic upgrade head`, then uvicorn on :8000 |
| `celery_worker` | Dockerfile | `celery -A celery_app worker` |

The tasks live in `celery_app.py` itself, which is why the worker needs no `include=`.
Move them to another module and the worker stops seeing them.

## Environment traps

- On Windows a native PostgreSQL service can hold `0.0.0.0:5432` while the container binds
  only IPv6, so `DB_HOST=localhost` reaches the native server, not the container. Check
  `Get-NetTCPConnection -LocalPort 5432` when the data looks wrong.
- CORS is **not** open: `app/main.py` allows the production origin and `settings.FRONTEND_URL`.
  A new frontend origin has to be added there.

## Frontend

Separate repository, `ecommerce-frontend/` (Next.js 16, React 19, TypeScript), deployed to
the same host. It talks to this API over HTTPS and to `/ws/admin` over WSS.
