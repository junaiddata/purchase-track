# Purchase Tracking System

## Project Handbook

- A business application for tracking purchase quotations, ordered items, shipment releases, received stock, and purchase planning.
- Designed for purchase, logistics, sales, and management teams.
- Helps staff see what is ordered, what is on the way, what is still pending at the factory, and what has already been received.

---

# App Name and Purpose

## Purchase Tracking System

- Tracks purchase quotations from draft stage through delivery completion.
- Connects item master stock, purchase order quantities, shipment releases, and received quantities in one place.
- Gives sales and management teams a clear view of incoming stock by brand or manufacturer.
- Supports Excel uploads, PDF/Excel exports, local purchase analysis, and stock synchronization.

---

# Business Problem Solved

- Purchase and logistics teams need a single view of order progress.
- Sales teams need to know when stock is arriving before committing to customers.
- Management needs visibility on pending factory quantities, in-transit shipments, received stock, current stock, sold quantity, and reorder needs.
- Manual spreadsheet tracking can become outdated, duplicated, or inconsistent.
- This app centralizes the information and reduces dependency on separate files and verbal updates.

---

# High-Level Process Flow

1. Admin uploads or syncs item master data.
2. Admin creates a purchase quotation with supplier/brand, manufacturer, currency, item quantities, rates, and expected dates.
3. Admin confirms the quotation when it becomes an active purchase order reference.
4. Admin records releases when goods leave the supplier or factory.
5. Sales and logistics teams monitor goods "On The Way" and "Pending at Factory".
6. Admin marks releases or item quantities as received.
7. The app updates received quantities, balances, and completed status.
8. Management reviews reports, consolidated views, reorder quantities, and local purchase analysis.

---

# Main User Roles

## Admin

- Full operational access.
- Can manage quotations, releases, receipts, manufacturers, item uploads, stock sync, local purchase analysis, reorder quantities, and reports.
- Can see commercial details such as rates, amounts, sold stock, and totals.

## Salesman

- Sales-facing tracking access.
- Can view purchase tracking by firm or brand.
- Can see incoming shipments, received history, pending factory quantities, and current stock.
- Does not see restricted commercial rate/amount details.

---

# Login and Access

- Users sign in with their username and password.
- After login, the app sends users to the correct area based on their role.
- Admin users land on the main dashboard.
- Salesman users land on the sales tracking firm selection page.
- If a user profile is missing, the system can create a default Salesman profile during login.

---

# Main Dashboard

## What Admins See

- Total Items: number of item master records available in the system.
- Draft / Pending: number of quotations still in draft status.
- In Transit: number of shipment releases that have not yet been received.
- Recent Quotations: latest quotation references with supplier, date, and status.
- Quick Actions:
  - Sync Stock API
  - Manage Quotations
  - Sales View
  - Purchase Report

---

# Important Records in Simple Language

- Item Master: the main list of products/items, including code, description, brand/firm, stock, sold quantity, cost, price, UPC, UOM, and reorder quantity.
- Manufacturer: parent company or manufacturer name used to group purchase quotations.
- Supplier/Firm: brand or firm name, optionally with a logo.
- Quotation: purchase order reference containing supplier/brand, manufacturer, currency, status, and item lines.
- Quotation Item: one item line inside a quotation, including ordered quantity, rate, and expected delivery date.
- Release: quantity shipped from supplier/factory, including release date, expected arrival date, and truck/container information.
- Shipment: received quantity record after goods arrive.
- Local Purchase Item: planning record imported from Excel for local purchase analysis.

---

# Quotation Statuses

- Draft: quotation is being prepared and can still be edited or deleted.
- Confirmed: quotation is active and included in sales tracking, pending factory quantities, and consolidated reports.
- Completed: all items are received, or the quotation is manually marked complete.
- Cancelled: quotation is no longer active.

---

# Purchase Quotation Module

## Purpose

- Creates and tracks purchase quotation references.
- Stores supplier or brand, manufacturer, currency, item list, ordered quantity, rates, and expected dates.
- Shows progress for every line item:
  - Ordered quantity
  - Quantity in transit
  - Quantity still to release
  - Quantity received
  - Remaining balance
  - Total value

---

# Creating a Quotation

1. Admin selects "Create Quotation".
2. Admin enters the quotation reference number.
3. Admin selects one or more supplier/brand names.
4. Admin optionally selects the manufacturer.
5. Admin selects the currency.
6. Admin adds item lines manually or uploads items from Excel.
7. Admin enters quantity, rate, and expected delivery date.
8. Admin saves the quotation as Draft or confirms it when ready.

---

# Quotation Excel Item Upload

## Used During Quotation Creation

- Admin can upload an Excel file to populate quotation item lines.
- The upload reads item code, quantity, and rate.
- The app matches item codes against the Item Master.
- Valid items are inserted into the quotation form.
- Warnings are shown for missing item codes or invalid quantities/rates.
- This reduces manual entry for large purchase orders.

---

# Quotation List and Search

- Admin can view all quotations in one list.
- Filters are available by status:
  - All
  - Draft
  - Confirmed
  - Completed
  - Cancelled
- Search works by quotation reference or supplier/brand name.
- Status can be updated from the list.
- Each quotation opens into a detailed tracking page.

---

# Quotation Detail Page

## What It Shows

- Quotation reference, supplier/brand, manufacturer, currency, and status.
- Total items and total amount.
- Line-level order progress:
  - Ordered
  - In Transit
  - To Release
  - Received
  - Balance
- Admin actions:
  - Edit Draft quotation
  - Delete Draft quotation
  - Release item quantity
  - Receive item quantity

---

# Release Workflow

## When Goods Leave the Supplier or Factory

1. Admin opens a quotation item.
2. Admin selects "Release".
3. Admin enters quantity released.
4. Admin enters release date.
5. Admin enters expected arrival date.
6. Admin records truck or container information.
7. The app moves that quantity into "In Transit".

Rule: the app prevents releasing more than the available balance.

---

# Receiving Workflow

## When Goods Arrive

1. Admin opens the quotation item or sales tracking page.
2. Admin receives a specific release or records a received shipment manually.
3. Admin confirms received quantity and date.
4. The app creates a receipt record.
5. The release becomes received.
6. The item balance is reduced.
7. If all items in the quotation are fully received, the quotation can automatically become Completed.

---

# Sales Tracking Module

## Purpose

- Gives sales and logistics staff a brand-wise view of purchase order progress.
- Helps teams answer customer and branch questions about incoming material.
- Users select a firm/brand, then see:
  - On The Way
  - Received History
  - Pending Orders at Factory
  - Current stock
  - Expected arrival dates

---

# Sales Tracking Page

## Main Sections

- On The Way: released quantities that are not yet received.
- Received History: delivered releases with received dates.
- Pending Orders at Factory: confirmed order quantities not yet released.
- Search: supports normal text search and multiple item codes.
- Export PDF: creates a firm-wise PDF report.
- Admin-only display: rates, amounts, sold stock, and grand totals.

---

# Salesman Daily Workflow

1. Sign in to the app.
2. Select the required firm or brand.
3. Search by item code, UPC, description, quotation reference, or container.
4. Check if the item is on the way, already received, or still pending at factory.
5. Review expected arrival date and current stock.
6. Export PDF if a shareable update is needed.
7. Contact purchase/logistics team if expected dates or receipt status look incorrect.

---

# Admin Daily Workflow

1. Sign in and review dashboard counts.
2. Sync stock data if needed.
3. Review recent quotations and draft quotations.
4. Create new quotations or update draft quotations.
5. Confirm active purchase orders.
6. Record releases when shipment details are available.
7. Update arrival dates or container details when they change.
8. Receive arrived releases or item quantities.
9. Review consolidated purchase report and update reorder quantities.
10. Export reports for management or operations meetings.

---

# Consolidated Purchase Report

## Purpose

- Provides a firm-wise planning report across all confirmed and completed quotation items.
- Combines shipment timing, pending quantity, local open quantity, stock, sold quantity, and reorder quantity.
- Useful for purchase planning, stock review, and management reporting.

---

# Consolidated Report Columns

- Item Code and Item Name.
- Arrival date columns showing quantities arriving on each date.
- In Transit: released quantity not yet received.
- Pending at Factory: confirmed order quantity not yet released.
- Total Qty Ordered: in transit plus pending at factory.
- Local Open Qty: external local open quantity from configured API.
- Import + Local: combined import and local open quantity.
- Stock: current stock from item master.
- Sold Stock: visible to Admin users.
- Reorder Qty: editable planning quantity.

---

# Reorder Quantity Workflow

1. Admin opens the consolidated purchase report for a firm.
2. Admin reviews stock, sold quantity, in-transit quantity, pending factory quantity, and local open quantity.
3. Admin enters a reorder quantity against each item.
4. The value auto-saves after typing.
5. Admin can reset all reorder quantities for that firm to zero when starting a new planning cycle.

---

# Consolidated Exports

- Excel Export: creates a spreadsheet version of the consolidated purchase report.
- PDF Export: creates a printable management report.
- Search filters are applied to exports when the user searches before exporting.
- Multi-code searches preserve the user's search order in exported reports.
- These exports are useful for meetings, supplier follow-ups, and purchase review files.

---

# Manufacturer Management

## Purpose

- Maintains the list of parent manufacturers used on quotations and reports.
- Admin can:
  - View manufacturers
  - Add a manufacturer
  - Edit a manufacturer
  - Delete a manufacturer
  - Import manufacturers from Excel

Excel import expects a column named "Manufacturer" or "Name".

---

# Item Master Upload

## Purpose

- Updates the central item list used in quotations and tracking.
- Admin uploads an Excel file with required columns:
  - Item Code
  - Item Description
  - Firm
  - Stock
  - UOM
- Existing item codes are updated.
- New item codes are created.
- Rows with problems are reported back to the user.

---

# Stock Sync Automation

## Purpose

- Keeps stock and sold quantity data current without waiting for page loads.
- The background stock import fetches:
  - Stock data from the stock API.
  - Sold quantity data from the sold quantity API.
- Item Master is updated with current stock, cost, selling price, UPC, manufacturer/firm, UOM, and sold quantity.
- The command can be run manually from the dashboard using "Sync Stock API".
- It can also be scheduled every 5 minutes using Windows Task Scheduler or cron.

---

# Ignore List

## Purpose

- Maintains item codes that should be ignored during API-based stock sync.
- Item codes can be imported from `ignore_list.xlsx`.
- The Excel file must contain an `item_code` column.
- This prevents unwanted or excluded items from entering the item master process.

---

# Local Purchase Analysis Module

## Purpose

- Helps purchase teams review local purchase requirements from Excel analysis files.
- Admin uploads a multi-sheet Excel file.
- Each accepted sheet becomes a brand analysis page.
- Supported sheet names include:
  - HEPWORTH
  - RAKTherm
  - VERA-PUMP
  - PEGLER
  - OTHERS

---

# Local Purchase Upload Process

1. Admin opens Local Purchase Analysis.
2. Admin selects "Upload New Analysis".
3. Admin uploads the multi-sheet Excel file.
4. The app reads accepted brand sheets only.
5. Existing records for that brand are replaced.
6. New analysis rows are created.
7. Admin selects a brand to review the analysis table.

---

# Local Purchase Analysis Screen

## What Users Can Review

- Item code, UPC, and description.
- Current stock by location or branch group.
- Sold quantity history.
- Channel quantities such as CONTG, TRDG, and Stores.
- 2025 sold quantity and average 15-day sales.
- Stock sufficiency in months.
- LPO given, open sales order quantity, calculated requirement, and final stock requirement.
- Value, cost, and additional planning quantities.

---

# Local Purchase Filters and Sorting

- Search by item code, UPC, or description.
- Quick filters:
  - All items
  - Critical Stock
  - Required
  - High Value
- Sort by most table columns.
- Pagination keeps large brand files manageable.
- The screen refreshes results without forcing the user to reload the whole page.

---

# Reports and Analytics

- Dashboard overview:
  - Total items
  - Draft quotations
  - In-transit shipment count
  - Recent quotations
- Sales tracking PDF:
  - Firm-wise shipment pipeline
  - Optional received history
  - Admin-only rate/amount option
- Consolidated Excel/PDF:
  - Arrival matrix
  - In-transit and pending quantities
  - Local open quantity
  - Stock, sold stock, and reorder quantity
- Local Purchase Analysis:
  - Critical stock and requirement review.

---

# Background and Automation Processes

- Stock import can run every 5 minutes through scheduler/cron.
- Manual stock import is available from the admin dashboard.
- External local open quantity can be pulled from a configured item totals API.
- Public item totals API returns total ordered quantity by item code, combining:
  - In-transit quantity
  - Pending-at-factory quantity
- Quotation status can auto-complete when all items are fully received.

---

# Data Quality Rules

- Item Code must be unique in Item Master.
- Quotation Reference Number must be unique.
- Manufacturer Name must be unique.
- Ignore List item code must be unique.
- Release quantity must be greater than zero.
- Release quantity cannot exceed the available balance.
- Quotation must have at least one selected supplier/brand.
- Draft quotations can be edited or deleted.
- Confirmed and completed quotations are protected from editing/deleting.
- Local purchase upload only accepts approved sheet names.

---

# Required Excel Formats

## Item Master Upload

- Item Code
- Item Description
- Firm
- Stock
- UOM

## Manufacturer Upload

- Manufacturer or Name

## Ignore List Upload

- item_code

## Quotation Item Upload

- Item code, quantity, and rate columns are expected.
- Item codes must already exist in Item Master.

## Local Purchase Upload

- Accepted brand sheet names and expected business columns such as CODE, UPC CODE, DESCRIPTION, stock, sales, requirement, value, and cost.

---

# Common Daily Operating Routine

1. Start the day by checking dashboard counts.
2. Run or verify stock sync.
3. Review draft and confirmed quotations.
4. Update shipment releases and expected arrival dates.
5. Receive arrived shipments immediately.
6. Check Sales Tracking for brand-wise operational updates.
7. Review the Consolidated Purchase Report for stock planning.
8. Update reorder quantities where needed.
9. Review Local Purchase Analysis for critical or required items.
10. Export PDF/Excel reports for team communication.

---

# Troubleshooting: Login and Access

- If a user cannot log in, confirm username and password.
- If a user opens the wrong page after login, check their assigned role.
- If a Salesman cannot access admin screens, that is expected.
- If an Admin cannot see admin functions, confirm the user is superuser or has Admin role.
- If a new user appears as Salesman by default, update the profile role if admin access is required.

---

# Troubleshooting: Uploads

- If item upload fails, check required column names exactly.
- If quotation Excel upload skips rows, confirm item codes exist in Item Master.
- If manufacturer upload fails, ensure the Excel file has "Manufacturer" or "Name" column.
- If local purchase upload imports fewer sheets, confirm sheet names are in the allowed list.
- If numeric values appear as zero, check the Excel cells for text, blanks, symbols, or invalid numbers.

---

# Troubleshooting: Stock and Reports

- If stock looks old, run "Sync Stock API" or check the scheduled stock update task.
- If stock sync fails, check internet/API availability and scheduler logs.
- If local open quantity is blank or zero, confirm the configured external API is reachable.
- If PDF or Excel export has too much data, use search filters before exporting.
- If rates do not show in sales PDF, confirm the user is Admin and the rate option is enabled.

---

# Troubleshooting: Shipment Status

- If an item does not appear in Sales Tracking, confirm the quotation is Confirmed.
- If a quantity is not "On The Way", confirm a release was recorded.
- If a received item still appears in transit, confirm the release was marked received.
- If a quotation does not complete automatically, check whether all item balances are fully received.
- If an arrival date is wrong, Admin can edit the release date from the tracking view.

---

# Benefits for Management

- Better visibility of incoming stock and factory pending quantities.
- Faster planning using consolidated brand-wise reports.
- Clear separation of in-transit, pending, received, stock, sold, and reorder quantities.
- Exportable PDF/Excel reports for meetings and supplier reviews.
- Reduced manual follow-up between sales, purchase, and logistics teams.
- More reliable decision-making from centralized records.

---

# Benefits for Daily Users

- Sales team can quickly answer stock arrival questions.
- Purchase team can track order progress line by line.
- Logistics team can update container/truck and received status.
- Admin team can manage quotations, releases, receipts, uploads, and master data.
- Teams can search by item code and export filtered reports.
- Less dependence on separate spreadsheets and repeated manual updates.

---

# Final Summary

- Purchase Tracking System is a business tool for purchase order visibility, shipment tracking, receiving, stock review, and planning.
- Admin users manage the full purchase and logistics workflow.
- Salesman users get a clear, controlled view of incoming and pending stock.
- Management gets consolidated reports, exports, and reorder planning data.
- The app supports daily operations from quotation creation through final receipt and reporting.

