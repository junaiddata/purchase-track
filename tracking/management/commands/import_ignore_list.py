import pandas as pd
from django.core.management.base import BaseCommand
from tracking.models import IgnoreList

class Command(BaseCommand):
    help = "Import item codes from Excel into IgnoreList model"

    def handle(self, *args, **kwargs):
        excel_file = "ignore_list.xlsx"  # Assumes file is in project root
        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Could not read {excel_file}: {e}"))
            return

        # Ensure item_code column exists
        # Normalizing column names to lowercase just in case
        df.columns = [c.lower().strip() for c in df.columns]
        
        if "item_code" not in df.columns:
            self.stdout.write(self.style.ERROR("Excel file must contain 'item_code' column"))
            return

        # Clean + get codes
        codes = df["item_code"].astype(str).str.strip().unique()

        added, skipped = 0, 0
        for code in codes:
            if not code or code == 'nan':
                continue
            obj, created = IgnoreList.objects.get_or_create(item_code=code)
            if created:
                added += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported {added} codes into IgnoreList, skipped {skipped} (already existed)"
        ))
