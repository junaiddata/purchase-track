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
