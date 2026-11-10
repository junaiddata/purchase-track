"""
Utility functions for the tracking app.
"""
import requests
from django.conf import settings


def fetch_local_open_qty_map():
    """Fetch item_code -> total_qty from external API. Returns dict."""
    url = getattr(settings, 'ITEM_TOTALS_API_URL', '') or ''
    url = url.strip()
    if not url:
        return {}
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {}
        data = r.json()
        # Support both {"items": [...]} and root-level array [...]
        items = data.get('items', []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = []
        result = {}
        for i in items:
            if not isinstance(i, dict):
                continue
            # Support item_code, itemCode, ItemCode
            code = (i.get('item_code') or i.get('itemCode') or i.get('ItemCode') or '')
            # Support total_qty, totalQty, TotalQty
            qty = i.get('total_qty') or i.get('totalQty') or i.get('TotalQty') or 0
            code = str(code).strip()
            if code:
                result[code] = int(qty) if qty is not None else 0
        return result
    except Exception:
        return {}


SAP_QUOTED_YEAR = 2026
SAP_QUOTED_MONTHS = (7, 8, 9)  # Jul, Aug, Sep


def fetch_sap_quoted_qty_map(company=None):
    """Fetch item_code -> SAP quoted qty summed over Jul-Sep 2026. Read-only; returns {} on failure.

    Each company has its own endpoint, API key and cache entry (see companies.py); default is Junaid.
    """
    import logging
    from django.core.cache import cache
    from .companies import JUNAID

    company = company or JUNAID
    url = (getattr(settings, company.sap_quoted_url_setting, '') or '').strip()
    key = (getattr(settings, company.sap_quoted_key_setting, '') or '').strip()
    if not url or not key:
        return {}

    cache_key = company.sap_quoted_cache_key
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = {}
    try:
        for month in SAP_QUOTED_MONTHS:
            r = requests.get(
                url,
                headers={'X-API-Key': key},
                params={'year': SAP_QUOTED_YEAR, 'month': month},
                timeout=15,
            )
            if r.status_code != 200:
                logging.getLogger(__name__).warning('SAP quoted qty API (%s) returned HTTP %s', company.name, r.status_code)
                return {}
            data = r.json()
            if not isinstance(data, dict) or not data.get('success'):
                logging.getLogger(__name__).warning('SAP quoted qty API (%s) returned an unexpected response', company.name)
                return {}
            for i in data.get('results', []):
                code = str(i.get('item_code') or '').strip()
                if code:
                    result[code] = result.get(code, 0) + float(i.get('quoted_qty') or 0)
    except Exception:
        return {}

    cache.set(cache_key, result, 300)
    return result


def calc_reorder_qty(sold_qty, percent=30):
    """Reorder Qty on Sold Stock: `percent`% of the sold quantity, rounded up."""
    import math
    try:
        sold = float(sold_qty or 0)
    except (TypeError, ValueError):
        return 0
    if sold <= 0:
        return 0
    # Integer maths avoids float error (e.g. 10 * 30 / 100 staying exact)
    return int(math.ceil(round(sold * percent, 6) / 100))


def effective_reorder_qty(item):
    """Reorder Qty on Sold Stock for an ItemMaster: the admin override if one is set
    (including an explicit 0), otherwise the calculated value."""
    override = getattr(item, 'reorder_override', None)
    if override is not None:
        return override
    return calc_reorder_qty(item.total_qty)
