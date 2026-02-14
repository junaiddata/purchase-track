# Complete Sales Order Sync Process Documentation

This document provides a comprehensive guide to implementing the Sales Order sync process. Use this as a reference to implement the same process for Purchase Orders or any other similar entity.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Components Breakdown](#components-breakdown)
3. [Step-by-Step Implementation Guide](#step-by-step-implementation-guide)
4. [API Client Implementation](#api-client-implementation)
5. [Sync Scripts (PC & Django Management Command)](#sync-scripts)
6. [VPS Receive Endpoint](#vps-receive-endpoint)
7. [Data Mapping & Transformation](#data-mapping--transformation)
8. [Error Handling & Logging](#error-handling--logging)
9. [Edge Cases & Special Logic](#edge-cases--special-logic)
10. [Testing & Validation](#testing--validation)

---

## 🏗️ Architecture Overview

### High-Level Flow

```
┌─────────────────┐
│  Local PC       │
│  (192.168.1.103)│
└────────┬────────┘
         │
         │ 1. Fetch from SAP API
         │    (POST to /api/SalesOrder)
         ▼
┌─────────────────┐
│  SAPAPIClient   │
│  (api_client.py)│
└────────┬────────┘
         │
         │ 2. Map API response to model format
         │    (_map_api_response_to_model)
         ▼
┌─────────────────┐
│  Sync Script    │
│  (PC or Django) │
└────────┬────────┘
         │
         │ 3. Serialize dates & send to VPS
         │    (POST to /sapsalesorders/sync-api-receive/)
         ▼
┌─────────────────┐
│  VPS Server     │
│  (Django Views) │
└────────┬────────┘
         │
         │ 4. Verify API key & process data
         │    (sync_salesorders_api_receive)
         ▼
┌─────────────────┐
│  Database       │
│  (PostgreSQL)   │
└─────────────────┘
```

### Key Components

1. **API Client** (`so/api_client.py`): Handles SAP API communication, pagination, filtering, and data mapping
2. **PC Sync Script** (`sync_salesorders_pc.py`): Standalone script that runs on PC, fetches data, and sends to VPS
3. **Django Management Command** (`so/management/commands/sync_salesorders_api.py`): Alternative sync method via Django command
4. **VPS Receive Endpoint** (`so/sap_salesorder_views.py`): Django view that receives and processes synced data
5. **Models** (`so/models.py`): Database models for Sales Orders and related entities

---

## 🔧 Components Breakdown

### 1. API Client (`so/api_client.py`)

**Purpose**: Centralized client for SAP API interactions

**Key Methods**:

#### `__init__()`
- Sets base URL from Django settings (`SAP_API_BASE_URL`)
- Initializes timeout (default: 30s)
- Initializes caches for manufacturers and stock

#### `_make_request(payload, page_number=1)`
- Makes POST request to SAP API
- Handles pagination by adding `pageNumber` to payload
- Returns dict with `value` (list) and `count` (total)
- Handles timeouts and errors gracefully

#### `_fetch_all_pages(payload, records_per_page=20)`
- Fetches all pages of results automatically
- Calculates total pages from first page response
- Iterates through all pages and combines results
- Returns combined list of all records

#### `fetch_open_salesorders()`
- Fetches all open sales orders (status = "bost_Open")
- Uses `_fetch_all_pages` for pagination
- Returns list of all open orders

#### `fetch_salesorders_by_date(single_date)`
- Fetches orders for a specific date (YYYY-MM-DD format)
- Uses `_fetch_all_pages` for pagination
- Returns list of orders for that date

#### `fetch_salesorders_by_docnum(docnum)`
- Fetches a single order by document number
- Uses `_fetch_all_pages` for pagination
- Returns list containing the order (or empty)

#### `_filter_ho_customers(orders)`
- **CRITICAL**: Filters orders to only include customers starting with "HO" or "SD"
- Checks `CardCode` from order or `BusinessPartner.CardCode`
- Returns filtered list

#### `_load_manufacturer_cache(item_codes)`
- Batch loads manufacturers from `Items` model
- Avoids N+1 queries by loading all at once
- Caches results for subsequent lookups

#### `_map_api_response_to_model(api_order)`
- **CORE MAPPING FUNCTION**: Transforms SAP API response to Django model format
- Handles date parsing (multiple formats)
- Extracts nested fields (BusinessPartner, SalesPerson, DocumentLines)
- Maps status codes ("bost_Open" → "O", else → "C")
- Calculates derived fields (pending_amount, row_total_sum)
- Returns dict ready for database insertion

**Key Mapping Details**:

```python
# Header fields
so_number = str(api_order.get('DocNum', ''))
posting_date = parse_date(api_order.get('DocDate', ''))
customer_code = bp.get('CardCode', '') or api_order.get('CardCode', '')
customer_name = bp.get('CardName', '') or api_order.get('CardName', '')
vat_number = bp.get('FederalTaxID', '')
customer_address = api_order.get('Address', '')
customer_phone = bp.get('Phone1', '')
closing_remarks = api_order.get('ClosingRemarks', '').replace('\r', '\n')
salesman_name = sales_person.get('SalesEmployeeName', '')
bp_reference = api_order.get('NumAtCard', '') or api_order.get('U_PurchaseOrder', '')
is_sap_pi = api_order.get('U_PROFORMAINVOICE', '') == 'Y'
sap_pi_lpo_date = parse_date(api_order.get('U_Lpdate', ''))

# Line items
for line in document_lines:
    item_code = str(line.get('ItemCode', ''))
    manufacture = self._get_manufacturer_from_item_code(item_code)  # From cache
    remaining_open_qty = line.get('RemainingOpenQuantity', 0)
    pending_amount = remaining_open_qty * price
    row_status = "O" if line_status == "bost_Open" else "C"
```

---

### 2. PC Sync Script (`sync_salesorders_pc.py`)

**Purpose**: Standalone script that runs on PC, syncs data periodically

**Key Features**:

#### Configuration
```python
VPS_BASE_URL = os.getenv('VPS_BASE_URL', 'https://salesorder.junaidworld.com')
VPS_API_KEY = os.getenv('VPS_API_KEY', 'test')
SYNC_INTERVAL_MINUTES = 7
DEFAULT_DAYS_BACK = 3
```

#### Logging Setup
- Creates `logs/` directory
- Logs to `logs/sync_salesorders.log`
- **NOTE**: Currently uses simple append mode (no rotation) - consider adding `RotatingFileHandler` like Django command

#### `sync_salesorders(days_back)` Function
1. **Fetch Open Orders**: Calls `client.fetch_open_salesorders()` and deduplicates by DocNum
2. **Fetch Last N Days**: Loops through last N days, calls `client.fetch_salesorders_by_date()` for each
3. **Filter Customers**: Calls `client._filter_ho_customers()` to keep only HO/SD customers
4. **Map Responses**: Loops through orders, calls `client._map_api_response_to_model()` for each
5. **Serialize Dates**: Converts date objects to ISO format strings for JSON
6. **Send to VPS**: POSTs to `/sapsalesorders/sync-api-receive/` with API key
7. **Handle Response**: Parses JSON response, logs stats (created/updated/closed)

#### Scheduling
- Uses `schedule` library for periodic execution
- Runs every 7 minutes by default
- Supports `--once` flag for one-time runs
- Supports `--days-back` for custom date range

#### Command Line Arguments
```bash
python sync_salesorders_pc.py              # Service mode (every 7 min)
python sync_salesorders_pc.py --once       # One-time run
python sync_salesorders_pc.py --days-back 8 # One-time with 8 days
```

---

### 3. Django Management Command (`so/management/commands/sync_salesorders_api.py`)

**Purpose**: Alternative sync method via Django management command

**Key Features**:

#### Logging Configuration
- Uses `RotatingFileHandler` with:
  - Max file size: 10 MB
  - Backup count: 5 files
  - Total max size: ~60 MB
- Logs to `logs/sync_salesorders.log`
- Also logs to console (stdout)

#### Command Arguments
```python
--days-back N    # Number of days to fetch (default: 3)
--date YYYY-MM-DD # Single date to fetch
--docnum N       # Single document number to fetch
--local-only     # Only save to local DB (testing)
```

#### Execution Flow
1. Same as PC script: fetch open + last N days
2. Filter by HO/SD customers
3. Map API responses
4. Serialize dates
5. Send to VPS (or save locally if `--local-only`)

#### Differences from PC Script
- Uses Django's logging system (`RotatingFileHandler`)
- Can be run via `python manage.py sync_salesorders_api`
- Better integration with Django settings
- Supports more query options (date, docnum)

---

### 4. VPS Receive Endpoint (`so/sap_salesorder_views.py`)

**Purpose**: Receives synced data from PC script and saves to database

**Endpoint**: `POST /sapsalesorders/sync-api-receive/`

**Security**:
- CSRF exempt (`@csrf_exempt`) - required for external API calls
- API key verification (compares with `settings.VPS_API_KEY`)

**Request Format**:
```json
{
  "orders": [...],              // List of mapped orders
  "api_so_numbers": [...],      // List of SO numbers from API (for closing logic)
  "api_key": "...",             // API key for authentication
  "sync_metadata": {
    "api_calls": 10,
    "days_back": 3,
    "sync_time": "2026-02-13T10:30:00"
  }
}
```

**Processing Steps**:

#### Step 1: Parse & Validate
- Parse JSON from request body
- Verify API key
- Extract orders and api_so_numbers

#### Step 2: Prepare Data Structures
```python
so_numbers = [m['so_number'] for m in orders if m.get('so_number')]
api_so_numbers_set = set(api_so_numbers)  # For closing logic
existing_map = {o.so_number: o for o in SAPSalesorder.objects.filter(so_number__in=so_numbers)}
```

#### Step 3: Process Orders (Inside Transaction)
- Loop through mapped orders
- Parse dates (handle string format: 'YYYY-MM-DD')
- Build `defaults` dict for `update_or_create`
- Separate into `to_create` and `to_update` lists

**Key Fields in `defaults`**:
```python
defaults = {
    "posting_date": posting_date,
    "customer_code": mapped.get('customer_code', ''),
    "customer_name": mapped.get('customer_name', ''),
    "bp_reference_no": mapped.get('bp_reference_no', ''),
    "salesman_name": mapped.get('salesman_name', ''),
    "discount_percentage": _dec2(mapped.get('discount_percentage', 0)),
    "document_total": _dec2(mapped.get('document_total', 0)),
    "row_total_sum": _dec2(mapped.get('row_total_sum', 0)),
    "status": mapped.get('status', 'C'),
    "vat_number": mapped.get('vat_number', '') or '',
    "customer_address": mapped.get('customer_address', '') or '',
    "customer_phone": mapped.get('customer_phone', '') or '',
    "closing_remarks": mapped.get('closing_remarks', '') or '',
    "is_sap_pi": mapped.get('is_sap_pi', False),
    "internal_number": mapped.get('internal_number'),
}
```

#### Step 4: Bulk Create/Update Orders
```python
if to_create:
    SAPSalesorder.objects.bulk_create(to_create, batch_size=5000)

if to_update:
    SAPSalesorder.objects.bulk_update(to_update, fields=[...], batch_size=5000)
```

#### Step 5: Process Items
- **Delete existing items** for these sales orders (always delete and recreate)
- Build items list from mapped orders
- Use `order_id_map` to get FK relationships
- Bulk create items (batch_size=20000)

**Item Fields**:
```python
SAPSalesorderItem(
    salesorder_id=so_id,
    line_no=item_data.get('line_no', 1),
    item_no=item_data.get('item_no', ''),
    description=item_data.get('description', ''),
    quantity=_dec_any(item_data.get('quantity', 0)),
    price=_dec_any(item_data.get('price', 0)),
    row_total=_dec_any(item_data.get('row_total', 0)),
    row_status=item_data.get('row_status', 'C'),
    job_type=item_data.get('job_type', ''),
    manufacture=item_data.get('manufacture', ''),
    remaining_open_quantity=_dec_any(item_data.get('remaining_open_quantity', 0)),
    pending_amount=_dec_any(item_data.get('pending_amount', 0)),
)
```

#### Step 6: Close Missing Orders
- Find orders that were previously open but not in API response
- Set status to 'C' (closed)
- Update all items: `row_status='C'`, `remaining_open_quantity=0`, `pending_amount=0`

```python
previously_open_orders = SAPSalesorder.objects.filter(
    status__in=['O', 'OPEN'],
    so_number__isnull=False
).exclude(so_number__in=api_so_numbers_set)

for order in previously_open_orders:
    order.status = 'C'
    order.save(update_fields=['status'])
    SAPSalesorderItem.objects.filter(salesorder=order).update(
        row_status='C',
        remaining_open_quantity=Decimal('0'),
        pending_amount=Decimal('0')
    )
```

#### Step 7: Create/Update SAP PIs
- Loop through orders where `is_sap_pi=True`
- Create `SAPProformaInvoice` with `pi_number = so_number` (not `so_number-SAP`)
- Set `pi_date = salesorder.posting_date`
- Set `lpo_date = sap_pi_lpo_date` from API
- Set `remarks = salesorder.closing_remarks`
- Delete existing PI lines and recreate from SO items

#### Step 8: Update Customer Model
- Update `Customer` model with address, phone, VAT number from API
- Use `get_or_create` to handle new customers
- Truncate phone number if exceeds field max_length

#### Step 9: Return Response
```json
{
  "success": true,
  "stats": {
    "created": 10,
    "updated": 5,
    "closed": 2,
    "total_items": 150,
    "sap_pis_created": 3,
    "sap_pis_updated": 1
  },
  "message": "Synced 15 orders successfully"
}
```

---

## 📊 Data Mapping & Transformation

### API Response Structure

```json
{
  "DocNum": "126000942",
  "DocEntry": "12345",
  "DocDate": "2026-02-13",
  "BusinessPartner": {
    "CardCode": "HO001",
    "CardName": "Customer Name",
    "FederalTaxID": "VAT123456",
    "Phone1": "+971501234567"
  },
  "SalesPerson": {
    "SalesEmployeeName": "John Doe",
    "SalesEmployeeCode": "EMP001"
  },
  "Address": "123 Main St, Dubai",
  "NumAtCard": "PO-12345",
  "U_PROFORMAINVOICE": "Y",
  "U_Lpdate": "2026-02-15",
  "ClosingRemarks": "Order completed\r\nThank you",
  "DocumentStatus": "bost_Open",
  "DocTotal": 10000.00,
  "VatSum": 500.00,
  "TotalDiscount": 100.00,
  "DiscountPercent": 1.0,
  "DocumentLines": [
    {
      "LineNum": 0,
      "ItemCode": "900985",
      "ItemDescription": "PPR COSMO F/TEE 25X1/2",
      "Quantity": 10,
      "Price": 100.00,
      "LineTotal": 1000.00,
      "LineStatus": "bost_Open",
      "RemainingOpenQuantity": 5
    }
  ]
}
```

### Mapped Model Format

```python
{
  'so_number': '126000942',
  'internal_number': '12345',
  'posting_date': date(2026, 2, 13),
  'customer_code': 'HO001',
  'customer_name': 'Customer Name',
  'salesman_name': 'John Doe',
  'bp_reference_no': 'PO-12345',
  'vat_number': 'VAT123456',
  'customer_address': '123 Main St, Dubai',
  'customer_phone': '+971501234567',
  'closing_remarks': 'Order completed\nThank you',
  'is_sap_pi': True,
  'sap_pi_lpo_date': date(2026, 2, 15),
  'document_total': 9500.00,  # Pending total
  'row_total_sum': 9000.00,    # Subtotal
  'discount_percentage': 1.0,
  'discount_percentage_display': 1.0,
  'vat_sum': 500.00,
  'total_discount': 100.00,
  'doc_total_full': 10000.00,
  'status': 'O',
  'items': [
    {
      'line_no': 1,
      'item_no': '900985',
      'description': 'PPR COSMO F/TEE 25X1/2',
      'quantity': 10,
      'price': 100.00,
      'row_total': 1000.00,
      'row_status': 'O',
      'manufacture': 'COSMO - PPR',
      'job_type': '',
      'remaining_open_quantity': 5,
      'pending_amount': 500.00
    }
  ]
}
```

### Date Parsing Logic

```python
def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_str, '%Y/%m/%d').date()
        except (ValueError, TypeError):
            logger.warning(f"Could not parse date: {date_str}")
            return None
```

### Decimal Conversion

```python
def _dec2(x) -> Decimal:
    """Convert to Decimal with 2 decimal places"""
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return Decimal("0.00")
        return Decimal(str(x)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")

def _dec_any(x) -> Decimal:
    """Convert to Decimal (any precision)"""
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return Decimal("0")
        return Decimal(str(x))
    except Exception:
        return Decimal("0")
```

---

## 🛡️ Error Handling & Logging

### API Client Errors

- **Timeout**: Logs error, returns `None`
- **Request Exception**: Logs error with payload, returns `None`
- **Unexpected Error**: Logs exception, returns `None`

### Sync Script Errors

- **API Fetch Failure**: Logs error, continues with empty list
- **Mapping Error**: Logs error for specific order, continues with others
- **VPS Send Failure**: Logs error, returns failure status
- **HTTP Error**: Logs status code and response body (truncated)

### VPS Receive Errors

- **Invalid API Key**: Returns 401 with error message
- **No Orders**: Returns 400 with error message
- **Database Error**: Logs exception, returns 500 with error details
- **Transaction Rollback**: Automatically handled by `transaction.atomic()`

### Logging Best Practices

1. **Log Levels**:
   - `INFO`: Normal operations, progress updates
   - `WARNING`: Non-critical issues (missing data, parsing failures)
   - `ERROR`: Critical failures (API errors, database errors)

2. **Log Format**:
   ```python
   '[{timestamp}] [{level}] {message}'
   ```

3. **Log Rotation**:
   - Use `RotatingFileHandler` for Django commands
   - Consider adding rotation to PC script (currently appends forever)

---

## 🎯 Edge Cases & Special Logic

### 1. Customer Filtering (HO/SD Only)

**Logic**: Only sync orders where `CardCode` starts with "HO" or "SD"

**Implementation**:
```python
def _filter_ho_customers(self, orders: List[Dict]) -> List[Dict]:
    filtered = []
    for order in orders:
        card_code = order.get('CardCode', '') or order.get('BusinessPartner', {}).get('CardCode', '')
        if isinstance(card_code, str):
            card_code_upper = card_code.strip().upper()
            if card_code_upper.startswith('HO') or card_code_upper.startswith('SD'):
                filtered.append(order)
    return filtered
```

### 2. Deduplication by DocNum

**Logic**: When fetching multiple date ranges, deduplicate by `DocNum`

**Implementation**:
```python
seen_docnums = set()
for order in orders:
    docnum_val = order.get('DocNum')
    if docnum_val and docnum_val not in seen_docnums:
        all_orders.append(order)
        seen_docnums.add(docnum_val)
```

### 3. Closing Missing Orders

**Logic**: If an order was open in DB but not in API response, mark it as closed

**Implementation**:
```python
previously_open_orders = SAPSalesorder.objects.filter(
    status__in=['O', 'OPEN'],
    so_number__isnull=False
).exclude(so_number__in=api_so_numbers_set)

for order in previously_open_orders:
    order.status = 'C'
    order.save(update_fields=['status'])
    SAPSalesorderItem.objects.filter(salesorder=order).update(
        row_status='C',
        remaining_open_quantity=Decimal('0'),
        pending_amount=Decimal('0')
    )
```

### 4. SAP PI Creation

**Logic**: If `U_PROFORMAINVOICE=Y`, create a Proforma Invoice with same number as SO

**Implementation**:
```python
if is_sap_pi:
    sap_pi = SAPProformaInvoice.objects.create(
        pi_number=so_number,  # Same as SO number
        salesorder=salesorder,
        sequence=0,  # SAP PIs use sequence 0
        status='ACTIVE',
        is_sap_pi=True,
        pi_date=salesorder.posting_date,
        lpo_date=sap_pi_lpo_date,
        remarks=salesorder.closing_remarks,
    )
```

### 5. Manufacturer Lookup

**Logic**: Batch load manufacturers from `Items` model to avoid N+1 queries

**Implementation**:
```python
# Preload all manufacturers
all_item_codes = set()
for order in all_orders:
    for line in order.get('DocumentLines', []):
        all_item_codes.add(str(line.get('ItemCode')))

self._load_manufacturer_cache(list(all_item_codes))

# Then use cache during mapping
manufacture = self._get_manufacturer_from_item_code(item_code)
```

### 6. Date Serialization for JSON

**Logic**: Convert date objects to ISO format strings before sending to VPS

**Implementation**:
```python
def serialize_order(order):
    serialized = order.copy()
    if 'posting_date' in serialized and serialized['posting_date']:
        if hasattr(serialized['posting_date'], 'isoformat'):
            serialized['posting_date'] = serialized['posting_date'].isoformat()
    return serialized
```

### 7. Closing Remarks Line Breaks

**Logic**: Replace `\r` with `\n` for proper line breaks

**Implementation**:
```python
closing_remarks = str(api_order.get('ClosingRemarks', '')).strip()
if closing_remarks:
    closing_remarks = closing_remarks.replace('\r', '\n')
```

---

## ✅ Testing & Validation

### Manual Testing Steps

1. **Test API Client**:
   ```python
   from so.api_client import SAPAPIClient
   client = SAPAPIClient()
   orders = client.fetch_open_salesorders()
   print(f"Fetched {len(orders)} orders")
   ```

2. **Test Mapping**:
   ```python
   mapped = client._map_api_response_to_model(orders[0])
   print(mapped)
   ```

3. **Test PC Script (One-Time)**:
   ```bash
   python sync_salesorders_pc.py --once --days-back 1
   ```

4. **Test Django Command**:
   ```bash
   python manage.py sync_salesorders_api --days-back 1
   ```

5. **Test VPS Endpoint** (using curl):
   ```bash
   curl -X POST https://salesorder.junaidworld.com/sapsalesorders/sync-api-receive/ \
     -H "Content-Type: application/json" \
     -d '{"orders": [...], "api_so_numbers": [...], "api_key": "..."}'
   ```

### Validation Checklist

- [ ] Orders are fetched correctly from API
- [ ] Customer filtering (HO/SD) works
- [ ] Date parsing handles multiple formats
- [ ] Mapping preserves all required fields
- [ ] Decimal conversion is accurate
- [ ] Bulk operations are efficient (batch sizes)
- [ ] Missing orders are closed correctly
- [ ] SAP PIs are created/updated correctly
- [ ] Customer model is updated with address/phone
- [ ] Error handling logs appropriately
- [ ] API key authentication works
- [ ] Transaction rollback works on errors

---

## 📝 Implementation Checklist for Purchase Orders

When implementing the same process for Purchase Orders, follow this checklist:

### 1. Models
- [ ] Create `SAPPurchaseOrder` model (similar to `SAPSalesorder`)
- [ ] Create `SAPPurchaseOrderItem` model (similar to `SAPSalesorderItem`)
- [ ] Add all required fields (matching API response)
- [ ] Create migrations

### 2. API Client
- [ ] Create `fetch_open_purchaseorders()` method
- [ ] Create `fetch_purchaseorders_by_date()` method
- [ ] Create `fetch_purchaseorders_by_docnum()` method
- [ ] Create `_map_purchaseorder_api_response()` method
- [ ] Update `_filter_ho_customers()` if needed (or create supplier filter)
- [ ] Update base URL to Purchase Order API endpoint

### 3. Sync Scripts
- [ ] Create `sync_purchaseorders_pc.py` (copy from `sync_salesorders_pc.py`)
- [ ] Update all references (SalesOrder → PurchaseOrder)
- [ ] Update VPS endpoint URL
- [ ] Create Django management command `sync_purchaseorders_api.py`

### 4. VPS Receive Endpoint
- [ ] Create `sync_purchaseorders_api_receive()` view
- [ ] Update URL routing
- [ ] Update model references
- [ ] Update field mappings
- [ ] Test API key authentication

### 5. Testing
- [ ] Test API client methods
- [ ] Test mapping function
- [ ] Test PC script (one-time run)
- [ ] Test Django command
- [ ] Test VPS endpoint
- [ ] Validate data in database

### 6. Logging
- [ ] Configure log file paths
- [ ] Add rotation for PC script (if needed)
- [ ] Test log output

### 7. Deployment
- [ ] Deploy to VPS
- [ ] Configure cron/scheduler for PC script
- [ ] Monitor logs for errors
- [ ] Verify sync is working

---

## 🔑 Key Takeaways

1. **Always filter by customer/supplier codes** (HO/SD) before processing
2. **Use batch operations** (bulk_create, bulk_update) for performance
3. **Delete and recreate items** (don't try to update individual items)
4. **Handle date parsing** with multiple format support
5. **Use Decimal for financial fields** (not float)
6. **Serialize dates to ISO format** before sending to VPS
7. **Close missing orders** that were open but not in API response
8. **Use transactions** for atomic operations
9. **Log everything** (errors, warnings, progress)
10. **Test thoroughly** before deploying

---

## 📚 Additional Resources

- Django ORM: https://docs.djangoproject.com/en/stable/topics/db/queries/
- Django Transactions: https://docs.djangoproject.com/en/stable/topics/db/transactions/
- Python `requests` library: https://requests.readthedocs.io/
- Python `schedule` library: https://schedule.readthedocs.io/

---

**End of Documentation**
