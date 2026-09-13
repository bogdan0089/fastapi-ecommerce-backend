# Architecture

The rules the code actually follows. For the system diagram and the request trace,
see [CLAUDE.md](CLAUDE.md).

## Flow

```
HTTP    →  router  →  service  →  UnitOfWork  →  repository  →  PostgreSQL
                         ↓
                      after the commit:
                      Celery mail · WebSocket broadcast · cache invalidation
```

There is one entry point per layer and nothing skips a layer. A router never touches
a repository, a service never opens a session by hand, a repository never decides
anything.

## Layers and their rules

### `app/router_*.py` — transport
- Validates input through an input DTO, resolves the caller through an
  `Annotated` dependency (`CurrentClient`, `CurrentModerator`, `CurrentAdmin`),
  calls **one** service method, returns a `response_model`.
- Contains no business logic and no SQL.
- Raises nothing itself: services raise the typed exceptions, which are already
  `HTTPException` subclasses carrying their own status.

### `services/` — business logic
- All of it: permissions beyond the role gate, money, stock, state transitions.
- Every method is a `@staticmethod` and every one of them works inside
  `async with UnitOfWork() as uow`.
- **Never commits by hand.** The UnitOfWork commits on a clean exit.
- **Never performs a side effect inside the transaction.** Mail, WebSocket
  broadcasts and cache invalidation happen after the `async with` block, because a
  rollback must be able to undo everything that a request did.
- Raises from `core/exceptions.py` — `OrderNotFoundError`, `NotEnoughMoneyError`,
  `OutOfStockError`, `InsufficientPermissionsError` — never a bare `HTTPException`.

### `repositories/` — data access
- SQLAlchemy queries only: `get`, `list`, `create`, `update`, `decrease_stock`.
- Never commits and never rolls back; the session arrives from outside.
- No rules. A business `if` in a repository is in the wrong file.

### The rest
- `models/models.py` — ORM tables, no methods carrying logic.
- `schemas/<resource>/input_dto.py` / `output_dto.py` — input and output are separate
  types on purpose: what a client may send is not what the API gives back. ORM objects
  never reach the client.
- `core/` — config (pydantic-settings), enums, exceptions, the Redis client, and the
  field validators shared across domains so a rule like the password minimum is
  written once.
- `utils/` — dependencies, cache keys, password hashing, the WebSocket manager, logging.
- `celery_app.py` — the Celery app and its four mail tasks in one module, which is why
  the worker needs no `include=`.

## Transactions

`UnitOfWork` is the only owner of a session:

```python
async with UnitOfWork() as uow:      # opens the session, attaches every repository
    ...                              # __aexit__ commits, or rolls back on an exception
```

- One `async with` block is one transaction. Two blocks in a row are two.
- `get_client_with_lock` is `SELECT ... FOR UPDATE`: two concurrent checkouts by the
  same client cannot both read the same balance.
- Rows that a request updates in bulk are sorted by `product_id` first, so two orders
  sharing products always take their locks in the same order and cannot deadlock.

## Money

`Numeric(10, 2)` in the database, `Decimal` in Python, never `float` — a float cent is
a rounding error waiting for a busy day. Output DTOs cast to `float` at the very edge
so the JSON contract with the frontend is unchanged.

`OrderProduct.price_at_purchase` records what the client paid. A refund reads that
column, not `Product.price`, which may have moved since.

## Idempotency

Stripe retries a webhook until it receives a 2xx and can deliver the same event twice.
Every handled event id goes into `processed_stripe_events` with
`INSERT ... ON CONFLICT DO NOTHING`; if the insert changed nothing, the event was
already credited and the handler returns without touching the balance.

Stock moves the same defensive way: `UPDATE products SET quantity = quantity - :n
WHERE id = :id AND quantity >= :n`. If no row was updated, the stock was gone — read,
decide, write would have oversold it.

## Caching

Redis holds list results and client stats for 60 seconds. Keys carry the version of
their namespace:

```
order:v3:list:limit=10:offset=0
```

`cache.invalidate("order")` runs one `INCR` on `cache_version:order`. Every key built
under the old version is unreachable from that moment and expires by itself. Nothing
is scanned, nothing is deleted — the earlier implementation walked every key in the
database on each write and blocked Redis while it did.

## Errors

`core/exceptions.py` holds `HTTPException` subclasses, each with its status and message
in one place:

```python
raise OrderNotFoundError(order_id)          # 404
raise NotEnoughMoneyError(client_id)        # 400
raise InsufficientPermissionsError(...)     # 403
```

FastAPI turns them into responses on its own, so there is no mapping table to keep in
sync and no way to add an error and forget to register it.

## Tests

`pytest` drops and recreates `{DB_NAME}_test` and builds the schema from the models,
so no run inherits another run's rows. Redis is faked and Celery tasks are recorded
rather than sent — without the stub the suite opens a real AMQP connection and mails
real people.

The Redis fake answers `None` to everything, which means it can never prove a caching
rule. Anything about cache behaviour is tested against a stateful fake in
`tests/cache_tests.py` instead.

Migrations are not exercised locally; CI runs `alembic upgrade head`, `alembic check`
and a full `downgrade base` round trip on a throwaway database.
