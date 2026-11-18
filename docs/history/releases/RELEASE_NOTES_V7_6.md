# QuantForge V7.6 - Editorial clarity, public research evidence, and navigation

## Purpose

QuantForge's public research narrative and private workspace were revised against the exact V7.5 UI source exported from the working checkout (source-manifest commit `ebf7d0054eb771c9b061dfaa31ccf09ba6589e69`). The writing is project-centered and technical without presenting the website as instructional material or promotional financial advice.

## Public website

- The Research systems page gains a data-backed comparison of annual SEC revenue growth and operating margin. The exhibit uses **only** the existing public, reviewed SEC Company Facts snapshot. It has a plotted comparison and an accessible table with fiscal end dates and source cutoff; no private price history or fabricated observations.
- A code-and-test evidence directory links methods to their real repository modules and regression tests. Advanced private algorithms can be inspected without owner authentication or exposure of personal research results.
- In-page shortcuts connect optimization, historical evaluation, SEC forecasting, investment screening, and evidence sources without adding more public navigation pages.
- Main headings and explanations were edited to describe the implemented methods and their limitations. A consistent increase in descriptive text size improves readability on desktop and small screens.

## Private workspace

- The nine existing private tabs are grouped under Portfolio & decisions, Quantitative research, and Companies & account. **Existing data-private-tab and data-private-view identifiers remain unchanged.**
- Top-level help copy is rewritten into concise descriptions of data inputs, numerical methods, and current analysis state. Several runtime-generated summaries have shorter professional titles.
- The authenticated API, MFA flow, portfolio ledger, valuation models, and trading controls are unchanged.

## Provenance and research boundaries

The public scatterplot represents historical financial facts and derived percentages, not stock returns or a factor model. Comparisons remain limited by fiscal period differences. All existing synthetic/illustrative demonstrations are still explicitly labeled. The public financial exhibit requires the official SEC snapshot that is present in the real repository at build time; the distributed ZIP deliberately does not contain or replace the snapshot.

## Testing and publication

Offline source-review validation includes the 15 focused Python tests, 104 JavaScript tests from the exported source **excluding** the proxy test whose backend file is not present in the partial export, all site JavaScript syntax checks, and a three-script CSP build audit. The full `ruff`, full `pytest`, full JavaScript suite, publication privacy check, GitHub CI (Python 3.11 and 3.12), and live desktop/mobile verification are mandatory on the actual repository before final acceptance. An offline browser walkthrough using the compiled HTML confirmed the Research systems navigation at 1400px and 390px widths, no horizontal overflow, and no JavaScript page errors. Live site confirmation with the official SEC snapshot is still required.

## No changes to

Alpaca credentials or private market-data feeds; SEC raw data and official snapshot; virtual holdings or notes; Supabase/Auth/MFA; Render/FastAPI; historical return, portfolio optimization, forecasting, or virtual accounting algorithms.
