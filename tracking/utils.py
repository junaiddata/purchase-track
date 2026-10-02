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
_SAP_QUOTED_CACHE_KEY = 'sap_quoted_qty_map_v1'


def fetch_sap_quoted_qty_map():
    """Fetch item_code -> SAP quoted qty summed over Jul-Sep 2026. Read-only; returns {} on failure."""
    from django.core.cache import cache

    url = (getattr(settings, 'QUOTATION_TOTALS_API_URL', '') or '').strip()
    key = (getattr(settings, 'QUOTATION_API_KEY', '') or '').strip()
    if not url or not key:
        return {}

    cached = cache.get(_SAP_QUOTED_CACHE_KEY)
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
                return {}
            data = r.json()
            if not isinstance(data, dict) or not data.get('success'):
                return {}
            for i in data.get('results', []):
                code = str(i.get('item_code') or '').strip()
                if code:
                    result[code] = result.get(code, 0) + float(i.get('quoted_qty') or 0)
    except Exception:
        return {}

    cache.set(_SAP_QUOTED_CACHE_KEY, result, 300)
    return result
