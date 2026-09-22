# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-22

### Added

- Initial release.
- `SalesTaxClient` (sync) with zero runtime dependencies.
- `AsyncSalesTaxClient` (async, requires `[async]` extra).
- Resources: `client.tax`, `client.rates`, `client.jurisdictions`.
- Automatic retries with exponential backoff, jitter, and `Retry-After` support.
- Full error hierarchy: `RateLimitError`, `ValidationError`, `TimeoutError`, and more.
- Lifecycle hooks: `on_request`, `on_response`, `on_retry`.
- Batch chunking via `calculate_batch_chunked()`.
- PEP 561 `py.typed` marker; `mypy --strict` clean.