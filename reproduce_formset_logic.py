import os
import django
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'purchase_tracking.settings')
django.setup()

from tracking.forms import QuotationItemFormSet, QuotationItemForm
from tracking.models import ItemMaster, Quotation

def test_formset_validation():
    # 1. Ensure we have at least one item
    item = ItemMaster.objects.first()
    if not item:
        item = ItemMaster.objects.create(item_code='TEST001', item_description='Test Item', item_firm='TestFirm')
        print("Created test item.")
    
    print(f"Testing with Item ID: {item.id}")

    # 2. Simulate POST data for 1 valid item
    data = {
        'items-TOTAL_FORMS': '1',
        'items-INITIAL_FORMS': '0',
        'items-MIN_NUM_FORMS': '0',
        'items-MAX_NUM_FORMS': '1000',
        
        'items-0-item': str(item.id),
        'items-0-quantity_ordered': '10',
        'items-0-rate': '100',
        'items-0-expected_delivery_date': '2025-12-31',
    }

    # 3. Instantiate FormSet
    formset = QuotationItemFormSet(data=data)
    
    # 4. Check Validation
    is_valid = formset.is_valid()
    print(f"Formset Valid: {is_valid}")
    
    if not is_valid:
        print("Errors:", formset.errors)
        for form in formset:
            print(f"Form Errors: {form.errors}")
            # Check the queryset of the item field
            print(f"Item Queryset Count: {form.fields['item'].queryset.count()}")

if __name__ == "__main__":
    test_formset_validation()
