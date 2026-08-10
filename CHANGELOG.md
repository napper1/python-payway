# Changelog

## 0.0.8

- Add opt-in transport retries to `Client` via `max_retries` and `retry_delay`
  constructor kwargs, following PayWay's retry guidance: resend on connection
  errors, timeouts and HTTP 429/503 (honouring `Retry-After`), never on other
  status codes, and never for a POST without an `Idempotency-Key`.
- Behaviour is unchanged unless `max_retries` is set — the default (`max_retries=0`)
  keeps the existing single-attempt behaviour.

## 0.0.7

- Simplify model serialization, raise minimum Python to 3.11.
