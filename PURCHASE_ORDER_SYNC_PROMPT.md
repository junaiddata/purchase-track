# Purchase Order Sync Implementation Prompt

Use this prompt in Cursor to implement the Purchase Order sync process using the same architecture as Sales Orders.

---

## Prompt for Cursor

```
I need to implement a Purchase Order sync system that follows the exact same architecture and process as the Sales Order sync system. The Purchase Order API has the same structure as the Sales Order API, with the same fields.

**IMPORTANT**: Reference these existing Sales Order files to understand the implementation pattern:
- API Client: `salesorder/so/api_client.py` (see `fetch_open_salesorders()`, `fetch_salesorders_by_date()`, `_map_api_response_to_model()`)
- PC Sync Script: `salesorder/sync_salesorders_pc.py`
- Django Command: `salesorder/so/management/commands/sync_salesorders_api.py`
- VPS Receive Endpoint: `salesorder/so/sap_salesorder_views.py` (see `sync_salesorders_api_receive()` function starting at line 977)
- Models: `salesorder/so/models.py` (see `SAPSalesorder` and `SAPSalesorderItem` models)

Please implement the following components:

1. **API Client Methods** (in `so/api_client.py`):
   - Add `fetch_open_purchaseorders()` - fetches all open purchase orders with pagination
   - Add `fetch_purchaseorders_by_date(single_date)` - fetches POs for a specific date with pagination
   - Add `fetch_purchaseorders_by_docnum(docnum)` - fetches a single PO by document number
   - Add `_map_purchaseorder_api_response(api_order)` - maps API response to model format (same structure as sales orders)
   - Update base URL to use Purchase Order API endpoint: `http://192.168.1.103/IntegrationApi/api/PurchaseOrder`

2. **Models** (in `so/models.py`):
   - Create `SAPPurchaseOrder` model with fields matching `SAPSalesorder`:
     - `po_number` (CharField, unique, like `so_number`)
     - `internal_number` (CharField, nullable)
     - `posting_date` (DateField)
     - `supplier_code` (CharField, like `customer_code`)
     - `supplier_name` (CharField, like `customer_name`)
     - `supplier_address` (TextField, like `customer_address`)
     - `supplier_phone` (CharField, like `customer_phone`)
     - `vat_number` (CharField)
     - `bp_reference_no` (CharField)
     - `salesman_name` (CharField) - or `purchaser_name` if different
     - `discount_percentage` (DecimalField)
     - `document_total` (DecimalField)
     - `row_total_sum` (DecimalField)
     - `vat_sum` (DecimalField)
     - `total_discount` (DecimalField)
     - `status` (CharField, choices: 'O' for Open, 'C' for Closed)
     - `closing_remarks` (TextField, nullable)
     - `created_at`, `updated_at` (DateTimeField)
   - Create `SAPPurchaseOrderItem` model with fields matching `SAPSalesorderItem`:
     - `purchaseorder` (ForeignKey to `SAPPurchaseOrder`)
     - `line_no` (IntegerField)
     - `item_no` (CharField)
     - `description` (CharField)
     - `quantity` (DecimalField)
     - `price` (DecimalField)
     - `row_total` (DecimalField)
     - `row_status` (CharField, choices: 'O', 'C')
     - `manufacture` (CharField)
     - `job_type` (CharField)
     - `remaining_open_quantity` (DecimalField)
     - `pending_amount` (DecimalField)

3. **PC Sync Script** (create new file `salesorder/sync_purchaseorders_pc.py`):
   - Reference the implementation in `salesorder/sync_salesorders_pc.py` as a template
   - Implement the same structure with these updates:
     - Import: `from so.api_client import SAPAPIClient`
     - Configuration: `VPS_BASE_URL`, `VPS_API_KEY`, `SYNC_INTERVAL_MINUTES = 7`
     - Log file: `logs/sync_purchaseorders.log`
     - In `sync_purchaseorders()` function:
       - Call `client.fetch_open_purchaseorders()` instead of `fetch_open_salesorders()`
       - Call `client.fetch_purchaseorders_by_date(date)` instead of `fetch_salesorders_by_date(date)`
       - Call `client._map_purchaseorder_api_response(api_order)` instead of `_map_api_response_to_model(api_order)`
       - Variable names: `purchase_orders` instead of `orders`, `po_number` instead of `so_number`
       - VPS endpoint: `f"{VPS_BASE_URL}/sappurchaseorders/sync-api-receive/"`
       - Payload key: `"purchase_orders"` instead of `"orders"`, `"api_po_numbers"` instead of `"api_so_numbers"`
     - Keep the same scheduling logic using `schedule` library (every 7 minutes)
     - Keep the same filtering logic (call `client._filter_ho_customers()` or create supplier filter if needed)
     - Keep the same error handling and logging structure
     - Keep the same command-line arguments (`--once`, `--days-back`, `--interval`)

4. **Django Management Command** (create new file `so/management/commands/sync_purchaseorders_api.py`):
   - Reference the implementation in `salesorder/so/management/commands/sync_salesorders_api.py` as a template
   - Implement the same structure with these updates:
     - Import: `from so.api_client import SAPAPIClient`
     - Logging setup: Use `RotatingFileHandler` with `maxBytes=10*1024*1024` (10MB), `backupCount=5`
     - Log file path: `BASE_DIR / 'logs' / 'sync_purchaseorders.log'`
     - Command class: `class Command(BaseCommand)`
     - Arguments: `--days-back`, `--date`, `--docnum`, `--local-only`
     - In `handle()` method:
       - Call `client.fetch_open_purchaseorders()` instead of `fetch_open_salesorders()`
       - Call `client.fetch_purchaseorders_by_date(date)` instead of `fetch_salesorders_by_date(date)`
       - Call `client.fetch_purchaseorders_by_docnum(docnum)` instead of `fetch_salesorders_by_docnum(docnum)`
       - Call `client._map_purchaseorder_api_response(api_order)` instead of `_map_api_response_to_model(api_order)`
       - Variable names: `purchase_orders` instead of `orders`, `po_number` instead of `so_number`
       - VPS endpoint: `f"{VPS_BASE_URL}/sappurchaseorders/sync-api-receive/"`
       - Payload key: `"purchase_orders"` instead of `"orders"`, `"api_po_numbers"` instead of `"api_so_numbers"`
     - Keep the same error handling, logging, and summary output

5. **VPS Receive Endpoint** (create new file `so/sap_purchaseorder_views.py` or add to existing views file):
   - Create `sync_purchaseorders_api_receive()` view function
   - Reference the implementation in `salesorder/so/sap_salesorder_views.py` starting at line 977 (`sync_salesorders_api_receive` function)
   - Implement the following structure:
     - Use `@csrf_exempt` and `@require_POST` decorators
     - Parse JSON from request body
     - Verify API key: `data.get('api_key')` must match `settings.VPS_API_KEY`
     - Extract `purchase_orders` from `data.get('purchase_orders', [])` (instead of `orders`)
     - Extract `api_po_numbers` from `data.get('api_po_numbers', [])` (instead of `api_so_numbers`)
     - Initialize stats dict: `{'created': 0, 'updated': 0, 'closed': 0, 'total_items': 0}`
     - Use `transaction.atomic()` wrapper for all database operations
     - Fetch existing purchase orders: `SAPPurchaseOrder.objects.filter(po_number__in=po_numbers)`
     - Build `to_create` and `to_update` lists
     - Use `_dec2()` helper for Decimal conversion (2 decimal places)
     - Parse `posting_date` from string format 'YYYY-MM-DD' if needed
     - Build `defaults` dict with all model fields (replace `so_number` with `po_number`, `customer_code` with `supplier_code`, etc.)
     - Bulk create: `SAPPurchaseOrder.objects.bulk_create(to_create, batch_size=5000)`
     - Bulk update: `SAPPurchaseOrder.objects.bulk_update(to_update, fields=[...], batch_size=5000)`
     - Delete existing items: `SAPPurchaseOrderItem.objects.filter(purchaseorder__po_number__in=po_numbers).delete()`
     - Build items list and bulk create: `SAPPurchaseOrderItem.objects.bulk_create(items_to_create, batch_size=20000)`
     - Close missing POs: Find POs with `status='O'` that are not in `api_po_numbers_set`, set status to 'C', update items
     - Return JsonResponse with success status and stats
   - Update all model references:
     - `SAPSalesorder` → `SAPPurchaseOrder`
     - `SAPSalesorderItem` → `SAPPurchaseOrderItem`
     - `so_number` → `po_number`
     - `customer_code` → `supplier_code`
     - `customer_name` → `supplier_name`
     - `customer_address` → `supplier_address`
     - `customer_phone` → `supplier_phone`
   - Remove SAP PI creation logic (not applicable for Purchase Orders)
   - Skip Customer model updates (or update Supplier model if it exists)

6. **URL Routing** (in `so/urls.py`):
   - Add route: `path('sappurchaseorders/sync-api-receive/', sap_purchaseorder_views.sync_purchaseorders_api_receive, name='sync_purchaseorders_api_receive')`

7. **Key Requirements**:
   - Use the same date parsing logic (supports 'YYYY-MM-DD' and 'YYYY/MM/DD')
   - Use the same Decimal conversion helpers (`_dec2`, `_dec_any`)
   - Use the same pagination logic (20 records per page)
   - Use the same error handling and logging
   - Use the same API key authentication
   - Use the same transaction.atomic() wrapper
   - Delete and recreate items (don't update individually)
   - Close missing POs that were open but not in API response
   - Serialize dates to ISO format before sending to VPS

8. **Filtering Logic**:
   - If Purchase Orders should be filtered by supplier codes (like HO/SD for customers), update `_filter_ho_customers()` or create `_filter_suppliers()` method
   - If no filtering is needed, remove the filter step

9. **Testing**:
   - Test API client methods
   - Test mapping function with sample API response
   - Test PC script with `--once --days-back 1`
   - Test Django command with `--days-back 1`
   - Verify data is saved correctly in database

Please implement all components following the exact same patterns, error handling, and optimizations as the Sales Order sync system. Make sure to:
- Use batch operations for performance
- Handle edge cases (missing data, parsing errors)
- Log all operations appropriately
- Use transactions for data integrity
- Follow the same code structure and naming conventions
```

---

## Quick Reference: Field Mappings

### Sales Order → Purchase Order

| Sales Order Field | Purchase Order Field | Notes |
|------------------|---------------------|-------|
| `so_number` | `po_number` | Document number |
| `customer_code` | `supplier_code` | Business partner code |
| `customer_name` | `supplier_name` | Business partner name |
| `customer_address` | `supplier_address` | Address field |
| `customer_phone` | `supplier_phone` | Phone field |
| `salesman_name` | `purchaser_name` or `salesman_name` | May be same or different |
| `SAPSalesorder` | `SAPPurchaseOrder` | Model name |
| `SAPSalesorderItem` | `SAPPurchaseOrderItem` | Item model name |

### API Endpoints

| Component | Sales Order | Purchase Order |
|-----------|-------------|----------------|
| API Base URL | `/api/SalesOrder` | `/api/PurchaseOrder` |
| VPS Receive | `/sapsalesorders/sync-api-receive/` | `/sappurchaseorders/sync-api-receive/` |
| Log File | `sync_salesorders.log` | `sync_purchaseorders.log` |

---

## Implementation Order

1. **Start with Models** - Create migrations and test
2. **Add API Client Methods** - Test with sample API calls
3. **Create VPS Receive Endpoint** - Test with curl/Postman
4. **Create PC Sync Script** - Test with `--once` flag
5. **Create Django Command** - Test with `--days-back 1`
6. **Add URL Routing** - Test full flow
7. **Deploy and Monitor** - Check logs for errors

---

## Common Pitfalls to Avoid

1. ❌ **Don't forget to update all variable names** (`orders` → `purchase_orders`, `so_number` → `po_number`)
2. ❌ **Don't forget to update model references** in bulk operations
3. ❌ **Don't forget to update URL endpoints** in sync scripts
4. ❌ **Don't forget to update log file paths**
5. ❌ **Don't forget to handle supplier filtering** (if needed)
6. ❌ **Don't forget to update Customer → Supplier** model updates (if applicable)
7. ❌ **Don't forget to test date parsing** with different formats
8. ❌ **Don't forget to test Decimal conversion** for financial fields

---

## Testing Checklist

- [ ] API client fetches open purchase orders correctly
- [ ] API client fetches purchase orders by date correctly
- [ ] Mapping function converts API response to model format correctly
- [ ] PC script runs without errors (`--once` mode)
- [ ] Django command runs without errors
- [ ] VPS endpoint receives and processes data correctly
- [ ] Data is saved to database correctly
- [ ] Missing POs are closed correctly
- [ ] Logging works correctly
- [ ] Error handling works correctly
- [ ] API key authentication works

---

**Ready to use! Copy the prompt above and paste it into Cursor.**
