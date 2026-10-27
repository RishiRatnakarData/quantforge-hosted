# QuantForge V6.5.2 — Historical market-data feed access

## Change

Owner-only historical equity requests continue to prefer split-adjusted SIP bars. When a SIP request returns Alpaca's sanitized HTTP 403 feed/endpoint-denied error, the analysis retries **every selected equity** on the free IEX feed. All equity assets in a single request therefore use the same source. Crypto bars continue to use the existing Alpaca crypto endpoint.

The result now includes `equity_feed` and accurately labels IEX-only coverage in `source` and `coverage` fields. IEX reflects one US exchange, not consolidated market activity; prices and estimated portfolio statistics can differ from SIP. If IEX is denied too, the request still fails. An authentication failure, rate limit, malformed data, or other unexpected error is never disguised as a successful fallback.

## Security boundaries

No additional API credentials, subscriptions, portfolio mutations, provider redistribution, or frontend public market-data access. Existing Supabase MFA and authorization protect the research endpoint. Local tests must pass before publication.
