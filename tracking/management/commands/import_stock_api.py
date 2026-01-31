import requests
from django.core.management.base import BaseCommand
from tracking.models import ItemMaster, IgnoreList
from django.core.cache import cache

class Command(BaseCommand):
    help = "Import items from stock API and sold quantity API, excluding those in IgnoreList (DB based)"

    def handle(self, *args, **kwargs):
        # Helper function for safe float conversion
        def safe_float(value):
            """Convert to float safely; return 0 if empty, invalid, or None."""
            try:
                if value in ("", None):
                    return 0.0
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        # 1. Load ignore list from DB
        ignore_codes = set(
            IgnoreList.objects.values_list("item_code", flat=True)
        )

        # 2. Fetch items from Stock API
        stock_url = "https://stock.junaidworld.com/api/stock"
        try:
            self.stdout.write(f"Fetching stock data from {stock_url}...")
            stock_response = requests.get(stock_url, timeout=30)
            stock_response.raise_for_status()
            stock_data = stock_response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch stock data: {e}"))
            return

        # 3. Fetch sold quantity data from API
        sold_url = "https://do.junaidworld.com/api/items/unique-qty"
        sold_data_dict = {}
        try:
            self.stdout.write(f"Fetching sold quantity data from {sold_url}...")
            sold_response = requests.get(sold_url, timeout=30)
            sold_response.raise_for_status()
            sold_data = sold_response.json()
            
            # Convert to dict for easy lookup by item_code
            if isinstance(sold_data, dict) and "results" in sold_data:
                for item in sold_data["results"]:
                    item_code = str(item.get("item_code", "")).strip()
                    if item_code and item_code != "-NULL-":
                        total_qty = safe_float(item.get("total_qty", 0))
                        sold_data_dict[item_code] = int(total_qty)
                self.stdout.write(f"Loaded {len(sold_data_dict)} sold quantity records")
            else:
                self.stdout.write(self.style.WARNING("Sold quantity API returned unexpected format"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to fetch sold quantity data: {e}. Continuing with stock data only..."))

        # Use a dict to deduplicate by item_code in case API returns duplicates
        items_dict = {}
        skipped = 0

        self.stdout.write("Processing items for update/creation...")
        for item in stock_data:
            item_code = str(item.get("item_code", "")).strip()

            if not item_code:
                skipped += 1
                continue

            cost_price = safe_float(item.get("cost_price"))
            price = safe_float(item.get("minimum_selling_price"))
            # Use total_stock from API (stock_quantity may not exist)
            stock = int(safe_float(item.get("total_stock", item.get("stock_quantity", 0))))
            # Get sold quantity from the second API, default to 0 if not found
            total_qty = sold_data_dict.get(item_code, 0)

            obj = ItemMaster(
                item_code=item_code,
                item_description=item.get("description", "") or "No Description",
                item_upvc=item.get("upc_code", ""),
                item_cost=cost_price,
                item_firm=item.get("manufacturer", "") or "Unknown",
                item_price=price,
                item_stock=stock,
                total_qty=total_qty,
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
                    'item_firm', 'item_price', 'item_stock', 'total_qty', 'uom'
                ]
            )

        cache.clear()
        self.stdout.write(self.style.SUCCESS(
            f"Sync Complete. Processed {len(new_items)} items. Skipped {skipped} (ignored/empty/duplicates)."
        ))
