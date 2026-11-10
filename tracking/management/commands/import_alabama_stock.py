import re
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tracking.models import AlabamaBrand, AlabamaItemMaster

# Placeholder item codes the stock app emits for non-items
JUNK_CODES = {'', '-1', '0', '-NULL-'}
MAX_MONEY = Decimal('99999999.99')      # ItemMaster cost/price columns are max_digits=10, decimal_places=2


def norm_brand(value):
    """Brand names are matched ignoring case, surrounding spaces and repeated spaces."""
    return re.sub(r'\s+', ' ', str(value or '').strip()).upper()


def to_int(value):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0


def to_money(value):
    """Rounded to 2 decimals; 0 if empty/invalid/too large for the column."""
    try:
        d = Decimal(str(value if value not in (None, '') else 0)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return Decimal('0.00')
    return d if abs(d) <= MAX_MONEY else Decimal('0.00')


class Command(BaseCommand):
    help = ("Import Alabama items (stock, cost, price, total sold) from the Alabama stock API into the Alabama "
            "item table. Only brands listed under 'Alabama brands' are imported. Junaid's data is not touched.")

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Fetch and report, but do not write anything.')
        parser.add_argument('--prune', action='store_true',
                            help="Also delete Alabama items of brands that are no longer in 'Alabama brands' "
                                 "(only items that are not used by any Alabama quotation).")

    def handle(self, *args, **options):
        dry = options['dry_run']
        url = (getattr(settings, 'ALABAMA_STOCK_API_URL', '') or '').strip()
        key = (getattr(settings, 'ALABAMA_API_KEY', '') or '').strip()
        if not url or not key:
            raise CommandError('ALABAMA_STOCK_API_URL / ALABAMA_API_KEY are not configured.')

        brands = {norm_brand(b) for b in AlabamaBrand.objects.values_list('name', flat=True)}
        if not brands:
            raise CommandError("No brands configured: add brands under 'Alabama brands' in the admin first.")

        # 1. Fetch (any problem aborts before anything is written)
        self.stdout.write('Fetching Alabama stock data...')
        try:
            resp = requests.get(url, headers={'X-API-Key': key}, timeout=60)
            if resp.status_code == 401:
                raise CommandError('Alabama stock API rejected the API key (401).')
            resp.raise_for_status()
            payload = resp.json()
        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Failed to fetch Alabama stock data: {e}')

        rows = payload.get('items') if isinstance(payload, dict) else None
        if not isinstance(rows, list) or (isinstance(payload, dict) and payload.get('ok') is False):
            raise CommandError('Alabama stock API returned an unexpected response; nothing was changed.')

        # 2. Keep only the approved brands (dict de-duplicates item codes: last one wins)
        wanted = {}
        junk = other_brand = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            code = str(row.get('ItemCode') or '').strip()
            if code in JUNK_CODES:
                junk += 1
                continue
            brand = re.sub(r'\s+', ' ', str(row.get('ManufacturerName') or '').strip())
            if norm_brand(brand) not in brands:
                other_brand += 1
                continue
            upc = str(row.get('UpcCode') or '').strip()
            wanted[code[:50]] = {
                'item_description': (row.get('Description') or '').strip() or 'No Description',
                'item_upvc': '' if upc in ('', '0') else upc[:50],        # column allows 50 chars
                'item_cost': to_money(row.get('CostPrice')),
                'item_firm': brand[:100],
                'item_price': to_money(row.get('SellingPrice')),
                'item_stock': to_int(row.get('StockQuantity')),
                'total_qty': to_int(row.get('SoldTotal')),                # total sold (2025 + 2026)
            }

        if not wanted:
            raise CommandError('No items matched the configured brands; nothing was changed.')

        existing = dict(AlabamaItemMaster.objects.values_list('item_code', 'id'))
        created = sum(1 for c in wanted if c not in existing)
        updated = len(wanted) - created

        # 3. Items of approved brands that disappeared from the feed: stock -> 0 (never deleted).
        #    Skipped when the feed looks incomplete, so a bad response cannot wipe all stock.
        missing_ids = []
        known_brand_rows = [
            (i, c) for i, c, f in AlabamaItemMaster.objects.values_list('id', 'item_code', 'item_firm')
            if norm_brand(f) in brands
        ]
        missing_ids = [i for i, c in known_brand_rows if c not in wanted]
        skip_zeroing = bool(known_brand_rows) and len(wanted) < 0.5 * len(known_brand_rows)

        self.stdout.write(
            f'Feed: {len(rows)} items | other brands skipped: {other_brand} | placeholder rows skipped: {junk} | '
            f'to import: {len(wanted)} ({created} new, {updated} existing)'
        )
        if skip_zeroing and missing_ids:
            self.stdout.write(self.style.WARNING(
                f'Feed has far fewer items than before ({len(wanted)} vs {len(known_brand_rows)}); '
                f'NOT zeroing stock of {len(missing_ids)} missing items.'))
            missing_ids = []

        if dry:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN - nothing written. Would zero stock of {len(missing_ids)} missing items.'))
            return

        with transaction.atomic():
            objs = [AlabamaItemMaster(item_code=code, **vals) for code, vals in wanted.items()]
            AlabamaItemMaster.objects.bulk_create(
                objs,
                update_conflicts=True,
                unique_fields=['item_code'],
                # uom, reorder_qty and reorder_override are never overwritten by the import
                update_fields=['item_description', 'item_upvc', 'item_cost', 'item_firm', 'item_price',
                               'item_stock', 'total_qty'],
            )
            zeroed = 0
            if missing_ids:
                zeroed = AlabamaItemMaster.objects.filter(id__in=missing_ids).exclude(item_stock=0).update(item_stock=0)
            pruned = 0
            if options['prune']:
                stale = [i for i, c, f in AlabamaItemMaster.objects.values_list('id', 'item_code', 'item_firm')
                         if norm_brand(f) not in brands]
                pruned = AlabamaItemMaster.objects.filter(id__in=stale, alabamaquotationitem__isnull=True).delete()[0]

        msg = f'Alabama sync complete. {len(wanted)} items processed ({created} new, {updated} updated).'
        if zeroed:
            msg += f' Stock set to 0 for {zeroed} items missing from the feed.'
        if pruned:
            msg += f' Removed {pruned} unused items of brands no longer enabled.'
        self.stdout.write(self.style.SUCCESS(msg))
