from django import forms
from django.forms import inlineformset_factory
from .models import ItemMaster, Quotation, QuotationItem, Shipment, Release, Manufacturer

class UploadItemForm(forms.Form):
    file = forms.FileField(label='Select Excel File')

class UploadManufacturerForm(forms.Form):
    file = forms.FileField(label='Select Excel File')

class ManufacturerForm(forms.ModelForm):
    class Meta:
        model = Manufacturer
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6',
                'placeholder': 'e.g., Aalberts Group Ltd'
            })
        }

class QuotationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get distinct firms from ItemMaster
        firms = ItemMaster.objects.values_list('item_firm', flat=True).distinct().order_by('item_firm')
        # Create choices list: [('', 'Select Supplier'), ('FirmA', 'FirmA'), ...]
        firm_choices = [('', 'Select Supplier')] + [(firm, firm) for firm in firms if firm]
        
        self.fields['supplier_name'].widget = forms.Select(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'})
        self.fields['supplier_name'].widget.choices = firm_choices
        
        # Add nice styling to manufacturer select
        self.fields['manufacturer'].widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'})
        self.fields['manufacturer'].empty_label = "Select Manufacturer"

    class Meta:
        model = Quotation
        fields = ['reference_number', 'supplier_name', 'manufacturer', 'status']
        widgets = {
            'reference_number': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 pl-10 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
            # supplier_name widget handled in __init__
            'status': forms.Select(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
        }

class QuotationItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Performance & Validation Fix:
        # We need to ensure the specific item submitted (or existing) is in the queryset
        # so validation passes, WITHOUT loading all 6000 items.
        
        self.fields['item'].queryset = ItemMaster.objects.none()

        if self.data:
            # Bound form (POST): Get the submitted item ID
            # self.add_prefix('item') accounts for formset prefix (e.g. items-0-item)
            item_key = self.add_prefix('item')
            item_id = self.data.get(item_key)
            if item_id:
                self.fields['item'].queryset = ItemMaster.objects.filter(pk=item_id)
        elif self.instance.pk:
            # Editing existing item (GET): Load the existing item
            self.fields['item'].queryset = ItemMaster.objects.filter(pk=self.instance.item_id)

    class Meta:
        model = QuotationItem
        fields = ['item', 'quantity_ordered', 'rate', 'expected_delivery_date']
        widgets = {
            'item': forms.Select(attrs={'class': 'block w-full rounded-md border-0 py-1.5 pl-3 pr-10 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 pl-10 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6', 'placeholder': 'Qty'}),
            'rate': forms.NumberInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 pl-10 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6', 'placeholder': '0.00'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-md border-0 py-1.5 pl-10 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
        }

QuotationItemFormSet = inlineformset_factory(
    Quotation, QuotationItem,
    form=QuotationItemForm,
    extra=1,
    can_delete=True
)

class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ['quantity_received', 'received_date', 'remarks']
        widgets = {
             'quantity_received': forms.NumberInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
        }

class ReleaseForm(forms.ModelForm):
    class Meta:
        model = Release
        fields = ['quantity_released', 'release_date', 'expected_arrival_date', 'container_info']
        widgets = {
             'release_date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'expected_arrival_date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'quantity_released': forms.NumberInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'container_info': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6', 'placeholder': 'e.g. Container #1234, Truck #55'}),
        }
