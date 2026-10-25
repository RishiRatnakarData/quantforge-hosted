-- Source: validated market_prices view/table. No interpolation or forward filling.
-- Compute returns per asset; ensure prices represent a consistent vendor-specified basis.
SELECT
    date,
    symbol,
    adjusted_close / LAG(adjusted_close) OVER (
        PARTITION BY symbol ORDER BY date
    ) - 1.0 AS simple_return
FROM market_prices
ORDER BY date, symbol;
