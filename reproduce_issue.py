import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'purchase_tracking.settings')
django.setup()

from tracking.forms import QuotationItemFormSet
from tracking.models import ItemMaster

def check_formset_rendering():
    # Create dummy items if needed (though user says 6000 exist)
    count = ItemMaster.objects.count()
    print(f"Total ItemMaster count: {count}")
    
    # Instantiate the formset
    formset = QuotationItemFormSet()
    
    # Get the first form (empty extra form)
    form = formset.forms[0]
    
    # Render the 'item' field
    rendered_item = str(form['item'])
    
    # Check number of option tags
    option_count = rendered_item.count('<option')
    print(f"Number of <option> tags in 'item' widget: {option_count}")
    
    # Print the first few characters to verify structure
    print(f"Widget HTML start: {rendered_item[:200]}...")

if __name__ == "__main__":
    check_formset_rendering()
