# Alabama company – setup & operations

The app now serves two companies from one codebase:

| | Junaid | Alabama |
|---|---|---|
| URLs | unchanged (`/`, `/consolidated/`, …) | same pages under `/alabama/` (`/alabama/consolidated/`, …) |
| Tables | original (`ItemMaster`, `Quotation`, `QuotationItem`, `Release`, `Shipment`) | **own tables** (`AlabamaItemMaster`, `AlabamaQuotation`, `AlabamaQuotationItem`, `AlabamaRelease`, `AlabamaShipment`) |
| Stock import | `python manage.py import_stock_api` (unchanged) | `python manage.py import_alabama_stock` |
| Local Open Qty + Import+Local columns | shown | hidden (Junaid-only system) |
| SAP Quoted Qty (Jul-Sep 2026) | Junaid SAP endpoint + `QUOTATION_API_KEY` | **own** endpoint + `ALABAMA_QUOTATION_API_KEY`, same months |
| Local Purchase module, public `/api/item-totals/` and `/api/consolidated-qty/` | available | not available (404) |

Shared by both companies (single tables): user logins/profiles, brand logos (`Supplier`), `Manufacturer`.
Because the two companies use different tables, the same item code / the same database id can exist in
both without ever mixing.

## Deploying
1. Back up the database.
2. `python manage.py migrate` — adds `0017` (reorder override column), `0018` (Alabama tables + a `company`
   column on user profiles, default `JUNAID`) and `0019` (seeds the first 28 Alabama brands). No Junaid
   item/quotation/release/shipment table is altered.
3. Make sure `.env` has `ALABAMA_API_KEY` (stock feed) and `ALABAMA_QUOTATION_API_KEY` (Alabama SAP quoted
   quantities). Optional overrides: `ALABAMA_STOCK_API_URL` (default
   `https://stock.junaidworld.com/api/alabama/stock?include_cost=1`) and `ALABAMA_QUOTATION_TOTALS_API_URL`
   (default `https://salesorder.junaidworld.com/alabama/api/item-quotation-totals/`). The Junaid
   `QUOTATION_API_KEY` is **not** accepted by the Alabama endpoint and is never used for Alabama.
4. If a reverse proxy is in front of Django, make sure `/alabama/` is forwarded to the app like `/`.
5. First import: `python manage.py import_alabama_stock --dry-run`, then `python manage.py import_alabama_stock`.
6. Schedule `python manage.py import_alabama_stock` as its **own** cron/task entry (like
   `schedule_stock_update.sh` does for Junaid). Junaid's schedule is untouched.

## Users
* **Admins** (role Admin or superuser) can open both companies. A "Switch to Alabama / Junaid" link appears in
  the top bar for them only (red = takes you to Alabama, blue = takes you to Junaid); Alabama pages show a
  red ALABAMA badge next to the app name.
* **Everyone else** works in the company set on their profile (Django admin → User profiles → *Company*,
  default Junaid). A Junaid user opening `/alabama/...` gets 403; an Alabama user opening a Junaid URL is
  redirected to the same page under `/alabama/`.

## Brands
Django admin → **Alabama brands**. Add the exact `ManufacturerName` from the Alabama stock API; the next
import brings in that brand's items. Matching ignores case and extra spaces.
`import_alabama_stock --prune` deletes Alabama items of brands that were removed from the list (only items
not used by any Alabama quotation).

## What the Alabama import does
* Sends `X-API-Key`; keeps only listed brands; skips placeholder rows (`-1`, `0`, empty).
* Stores stock (`StockQuantity`), cost, selling price and total sold (`SoldTotal` = 2025 + 2026).
* Never overwrites `uom`, `reorder_qty` or the admin "Reorder Qty on Sold Stock" override.
* Items of listed brands that vanish from the feed get stock 0 (never deleted) — unless the feed has fewer
  than half the usual items, in which case nothing is zeroed.
* Any fetch/format problem aborts before anything is written. `--dry-run` writes nothing.

## Rolling back
The change is additive. To remove Alabama completely: deploy the previous code, then (only if you also want
the Alabama tables gone) `python manage.py migrate tracking 0017`. Junaid data is never affected.

## SAP Quoted Qty for Alabama
* Same rule as Junaid: sums July, August and September **2026** (`SAP_QUOTED_YEAR` / `SAP_QUOTED_MONTHS` in
  `tracking/utils.py`), cached for 5 minutes, Alabama and Junaid cached separately.
* If the key is missing/wrong or the endpoint is down, pages and exports still load and the column shows no
  value; a warning is written to the log (`tracking.utils`). Nothing is cached on failure.
