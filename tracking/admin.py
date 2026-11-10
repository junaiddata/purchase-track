from django.contrib import admin
from django.utils.html import format_html
from .models import (
    IgnoreList, ItemMaster, Quotation, QuotationItem, Shipment, Supplier, Manufacturer, UserProfile, Release,
    AlabamaBrand, AlabamaItemMaster, AlabamaQuotation, AlabamaQuotationItem, AlabamaShipment, AlabamaRelease,
)

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
    list_display = ('user', 'role', 'company')
    list_filter = ('role', 'company')
    search_fields = ('user__username', 'user__email')

@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('quotation_item', 'quantity_released', 'release_date', 'expected_arrival_date')
@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(IgnoreList)
class IgnoreListAdmin(admin.ModelAdmin):
    list_display = ('item_code',)
    search_fields = ('item_code',)


# ---------------------------------------------------------------------------
# Alabama (separate tables with the same structure as Junaid's)
# ---------------------------------------------------------------------------
@admin.register(AlabamaBrand)
class AlabamaBrandAdmin(admin.ModelAdmin):
    """Brands imported for Alabama. Add a brand here (exact ManufacturerName from the Alabama stock API)
    and the next Alabama import brings in its items."""
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(AlabamaItemMaster)
class AlabamaItemMasterAdmin(admin.ModelAdmin):
    list_display = ('item_code', 'item_description', 'item_firm', 'item_stock', 'total_qty', 'reorder_override')
    search_fields = ('item_code', 'item_description', 'item_firm')
    list_filter = ('item_firm',)

class AlabamaQuotationItemInline(admin.TabularInline):
    model = AlabamaQuotationItem
    extra = 1
    raw_id_fields = ('item',)

@admin.register(AlabamaQuotation)
class AlabamaQuotationAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'supplier_name', 'created_at', 'status')
    inlines = [AlabamaQuotationItemInline]

@admin.register(AlabamaRelease)
class AlabamaReleaseAdmin(admin.ModelAdmin):
    list_display = ('quotation_item', 'quantity_released', 'release_date', 'expected_arrival_date')

@admin.register(AlabamaShipment)
class AlabamaShipmentAdmin(admin.ModelAdmin):
    list_display = ('quotation_item', 'quantity_received', 'received_date')
