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
    supplier_name = forms.MultipleChoiceField(
        required=True,
        widget=forms.SelectMultiple(attrs={
            'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6',
            'size': '5'
        }),
        help_text="Select one or more brands/firms"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get distinct firms from ItemMaster
        firms = ItemMaster.objects.values_list('item_firm', flat=True).distinct().order_by('item_firm')
        # Create choices list: [('FirmA', 'FirmA'), ...]
        firm_choices = [(firm, firm) for firm in firms if firm]
        
        self.fields['supplier_name'].choices = firm_choices
        
        # If editing, set initial value from comma-separated string
        if self.instance and self.instance.pk and self.instance.supplier_name:
            selected_firms = [firm.strip() for firm in self.instance.supplier_name.split(',') if firm.strip()]
            self.initial['supplier_name'] = selected_firms
    
    def clean_supplier_name(self):
        # Convert list to comma-separated string for storage
        selected_firms = self.cleaned_data.get('supplier_name', [])
        if not selected_firms:
            raise forms.ValidationError("Please select at least one brand/firm.")
        return ', '.join(selected_firms)
        
        # Add nice styling to manufacturer select
        self.fields['manufacturer'].widget.attrs.update({'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'})
        self.fields['manufacturer'].empty_label = "Select Manufacturer"

    class Meta:
        model = Quotation
        fields = ['reference_number', 'supplier_name', 'manufacturer', 'currency', 'status']
        widgets = {
            'reference_number': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 pl-10 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
            # supplier_name widget handled in __init__
            'currency': forms.Select(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
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

class ReleaseEditForm(forms.ModelForm):
    """Form to edit expected arrival date and container info of an existing release."""
    class Meta:
        model = Release
        fields = ['expected_arrival_date', 'container_info']
        widgets = {
            'expected_arrival_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'
            }),
            'container_info': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6',
                'placeholder': 'e.g. Container #1234, Truck #55'
            }),
        }


class ReleaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.quotation_item = kwargs.pop('quotation_item', None)
        super().__init__(*args, **kwargs)
        
        # Set max attribute on quantity_released field if we have the item
        if self.quotation_item:
            balance_to_release = self.quotation_item.balance_to_release
            if balance_to_release > 0:
                self.fields['quantity_released'].widget.attrs['max'] = balance_to_release
                self.fields['quantity_released'].widget.attrs['min'] = 1
    
    def clean_quantity_released(self):
        quantity_released = self.cleaned_data.get('quantity_released')
        
        if self.quotation_item and quantity_released is not None:
            balance_to_release = self.quotation_item.balance_to_release
            
            if quantity_released <= 0:
                raise forms.ValidationError("Quantity released must be greater than 0.")
            
            if quantity_released > balance_to_release:
                raise forms.ValidationError(
                    f"Cannot release more than available balance. Available to release: {balance_to_release}"
                )
        
        return quantity_released
    
    class Meta:
        model = Release
        fields = ['quantity_released', 'release_date', 'expected_arrival_date', 'container_info']
        widgets = {
             'release_date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'expected_arrival_date': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'quantity_released': forms.NumberInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6'}),
             'container_info': forms.TextInput(attrs={'class': 'block w-full rounded-md border-0 py-1.5 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-brand-600 sm:text-sm sm:leading-6', 'placeholder': 'e.g. Container #1234, Truck #55'}),
        }
