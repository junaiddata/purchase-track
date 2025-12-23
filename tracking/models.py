from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

class Supplier(models.Model):
    """Supplier/Firm with optional logo for branding."""
    name = models.CharField(max_length=100, unique=True, help_text="Supplier/Firm name (must match item_firm)")
    logo = models.ImageField(upload_to='supplier_logos/', blank=True, null=True, help_text="Supplier logo (optional)")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ItemMaster(models.Model):
    item_code = models.CharField(max_length=50, unique=True)
    item_description = models.TextField()
    item_firm = models.CharField(max_length=100, help_text="Manufacturer/Brand (e.g. PEGLER)", db_index=True)
    item_stock = models.IntegerField(default=0, help_text="Available Stock")
    uom = models.CharField(max_length=20, default="Nos")
    # New fields for API Sync
    item_upvc = models.CharField(max_length=50, blank=True, null=True, help_text="UPC Code")
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    item_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.item_code} - {self.item_description[:30]}"

class IgnoreList(models.Model):
    item_code = models.CharField(max_length=50, unique=True, help_text="Item Code to ignore during API sync")

    def __str__(self):
        return self.item_code

class Manufacturer(models.Model):
    """Parent company/manufacturer entity."""
    name = models.CharField(max_length=150, unique=True, help_text="Manufacturer name (e.g., Aalberts Group Ltd)")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Quotation(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    reference_number = models.CharField(max_length=50, unique=True)
    supplier_name = models.CharField(max_length=100, help_text="Brand/Firm name (e.g., PEGLER)")
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    def __str__(self):
        return self.reference_number

class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(ItemMaster, on_delete=models.CASCADE)
    quantity_ordered = models.IntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    expected_delivery_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.item.item_code} in {self.quotation.reference_number}"

    @property
    def quantity_received(self):
        return self.shipments.aggregate(total=Sum('quantity_received'))['total'] or 0

    @property
    def balance_quantity(self):
        return self.quantity_ordered - self.quantity_received

    @property
    def quantity_in_transit(self):
        return self.releases.filter(is_received=False).aggregate(total=Sum('quantity_released'))['total'] or 0

    @property
    def balance_to_release(self):
        return self.quantity_ordered - (self.quantity_in_transit + self.quantity_received)

class Release(models.Model):
    quotation_item = models.ForeignKey(QuotationItem, related_name='releases', on_delete=models.CASCADE)
    quantity_released = models.IntegerField()
    release_date = models.DateField()
    expected_arrival_date = models.DateField(null=True, blank=True)
    container_info = models.CharField(max_length=100, blank=True, help_text="Truck/Container No.")
    is_received = models.BooleanField(default=False)

    def __str__(self):
        return f"Release {self.quantity_released} of {self.quotation_item}"

class Shipment(models.Model):
    quotation_item = models.ForeignKey(QuotationItem, related_name='shipments', on_delete=models.CASCADE)
    quantity_received = models.IntegerField()
    received_date = models.DateField()
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Recv {self.quantity_received} for {self.quotation_item}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('SALESMAN', 'Salesman'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SALESMAN')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class LocalPurchaseItem(models.Model):
    """Model to store Local Purchase Analysis data from Excel."""
    brand = models.CharField(max_length=100, help_text="Brand/Sheet Name (e.g., HEPWORTH)", db_index=True)
    item_code = models.CharField(max_length=50)
    upc_code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Stock Columns
    current_stock_ras = models.IntegerField(default=0)
    current_stock_dip = models.IntegerField(default=0)
    sold_qty_2024 = models.IntegerField(default=0)
    
    # Channels
    contg = models.IntegerField(default=0)
    trdg = models.IntegerField(default=0)
    stores = models.IntegerField(default=0)
    
    # Analysis 2025
    total_sold_qty_2025 = models.IntegerField(default=0)
    avg_15day_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stock_sufficiency_months = models.DecimalField(max_digits=10, decimal_places=1, default=0.0)
    
    # Requirements
    lpo_given = models.IntegerField(default=0)
    open_so_qty = models.IntegerField(default=0)
    stock_reqt_calcn = models.IntegerField(default=0) # Can be negative
    stock_requirement = models.IntegerField(default=0)
    
    # Valuation
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    # Extras
    ho_per_lpo_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stock_reqt_ras_stores = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['brand', 'item_code']
        verbose_name = "Local Purchase Item"
        verbose_name_plural = "Local Purchase Items"

    def __str__(self):
        return f"{self.brand} - {self.item_code}"
