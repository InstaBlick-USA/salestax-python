# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-23

### Changed

**BREAKING:** Redesigned the SDK to match the public OpenAPI contract.

- Replaced `client.tax`, `client.rates`, `client.jurisdictions` with
  `client.calculations`, `client.transactions`, `client.transactions.adjustments`,
  `client.batches`, and `client.coverage`.
- Request and response shapes now use snake_case matching the OpenAPI spec.
- Money and quantity are decimal strings, matching the wire format.
- Idempotency-Key is validated client-side against `[A-Za-z0-9][A-Za-z0-9._:-]{7,254}`.
- Error bodies are parsed as RFC 9457 problem+json. Field-level errors
  populate `err.param` from `errors[0].pointer`.
- Base URL is now `https://api.salestaxcalculatorapi.com` (no `/v1` suffix).
- Added `expand="audit"` request option on all readable endpoints.

### Added

- `client.transactions` and `client.transactions.adjustments` resources.
- `client.batches` resource for async batch polling.
- `client.coverage` resource for pre-calculation qualification checks.

### Removed

- `client.tax.calculate`, `client.tax.calculate_batch`, `client.tax.calculate_batch_chunked`
- `client.rates.get`
- `client.jurisdictions.list`
- `salestax/utils.py` (chunk helper no longer needed)

## [0.1.0] - 2026-09-22

### Added

- Initial release.
- `SalesTaxClient` (sync) with zero runtime dependencies.
- `AsyncSalesTaxClient` (async, requires `[async]` extra).
- Automatic retries with exponential backoff, jitter, and `Retry-After` support.
- Full error hierarchy: `RateLimitError`, `ValidationError`, `TimeoutError`, and more.
- Lifecycle hooks: `on_request`, `on_response`, `on_retry`.
- PEP 561 `py.typed` marker; `mypy --strict` clean.