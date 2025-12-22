from django.contrib import admin
from django.utils.html import format_html
from .models import ItemMaster, Quotation, QuotationItem, Shipment, Supplier, Manufacturer, UserProfile, Release

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo_preview')
    search_fields = ('name',)
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="40" height="40" style="object-fit: contain;" />', obj.logo.url)
        return "-"
    logo_preview.short_description = 'Logo'

@admin.register(ItemMaster)
class ItemMasterAdmin(admin.ModelAdmin):
    list_display = ('item_code', 'item_description', 'item_firm', 'item_stock')
    search_fields = ('item_code', 'item_description', 'item_firm')

class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'supplier_name', 'created_at', 'status')
    inlines = [QuotationItemInline]

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('quotation_item', 'quantity_received', 'received_date')

# User Management
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')

@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('quotation_item', 'quantity_released', 'release_date', 'expected_arrival_date')
@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
