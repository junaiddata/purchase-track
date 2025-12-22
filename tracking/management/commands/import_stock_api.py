import requests
from django.core.management.base import BaseCommand
from tracking.models import ItemMaster, IgnoreList
from django.core.cache import cache

class Command(BaseCommand):
    help = "Import items from Website A, excluding those in IgnoreList (DB based)"

    def handle(self, *args, **kwargs):
        # 1. Load ignore list from DB
        ignore_codes = set(
            IgnoreList.objects.values_list("item_code", flat=True)
        )

        # 2. Fetch items from Website A JSON API
        url = "https://stock.junaidworld.com/api/stock"
        try:
            self.stdout.write(f"Fetching data from {url}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            items_data = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch data: {e}"))
            return

        # Use a dict to deduplicate by item_code in case API returns duplicates
        items_dict = {}
        skipped = 0

        def safe_float(value):
            """Convert to float safely; return 0 if empty, invalid, or None."""
            try:
                if value in ("", None):
                    return 0.0
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        self.stdout.write("Processing items for update/creation...")
        for item in items_data:
            item_code = str(item.get("item_code", "")).strip()

            if not item_code or item_code in ignore_codes:
                skipped += 1
                continue

            cost_price = safe_float(item.get("cost_price"))
            price = safe_float(item.get("minimum_selling_price"))
            stock = int(safe_float(item.get("stock_quantity")))

            obj = ItemMaster(
                item_code=item_code,
                item_description=item.get("description", "") or "No Description",
                item_upvc=item.get("upc_code", ""),
                item_cost=cost_price,
                item_firm=item.get("manufacturer", "") or "Unknown",
                item_price=price,
                item_stock=stock,
                uom=item.get("uom", "Nos")
            )
            # This handles duplicates in the API source: last one wins
            items_dict[item_code] = obj

        new_items = list(items_dict.values())

        if new_items:
            # Efficient Upsert (PostgreSQL only)
            self.stdout.write(f"Syncing {len(new_items)} unique items (Updates and New)...")
            ItemMaster.objects.bulk_create(
                new_items,
                update_conflicts=True,
                unique_fields=['item_code'],
                update_fields=[
                    'item_description', 'item_upvc', 'item_cost', 
                    'item_firm', 'item_price', 'item_stock', 'uom'
                ]
            )

        cache.clear()
        self.stdout.write(self.style.SUCCESS(
            f"Sync Complete. Processed {len(new_items)} items. Skipped {skipped} (ignored/empty/duplicates)."
        ))
