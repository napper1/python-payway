# Changelog

## 0.0.9

- Add `search_transactions_by_customer()`, `search_transactions_by_receipt()` and
  `search_transactions_by_order()`, matching PayWay's three documented search paths.
  Parameters are passed as query params and an optional `page` supports pagination.
- **Breaking:** remove `search_transactions(query)`. It built `GET /transactions<query>`, and
  `/transactions` only accepts POST, so any query that wasn't a `/search-*` path failed with
  405 Method Not Allowed. Use the three methods above instead.
- Add an optional `page` argument to `list_customers()`, so results past the first 20
  customers can be reached.
- **Breaking:** `constants.TOKEN_URL` now holds `/single-use-tokens`, the endpoint PayWay
  actually documents. The old value, `/single-use-tokens-redirect`, is not a PayWay endpoint
  and was unused. `constants.TOKEN_NO_REDIRECT` is removed — use `TOKEN_URL`.
- **Breaking:** remove the unused `constants.OWN_BANK_ACCOUNTS_URL`.

## 0.0.8

- Add opt-in transport retries to `Client` via `max_retries` and `retry_delay`
  constructor kwargs, following PayWay's retry guidance: resend on connection
  errors, timeouts and HTTP 429/503 (honouring `Retry-After`), never on other
  status codes, and never for a POST without an `Idempotency-Key`.
- Behaviour is unchanged unless `max_retries` is set — the default (`max_retries=0`)
  keeps the existing single-attempt behaviour.

## 0.0.7

- Simplify model serialization, raise minimum Python to 3.11.
