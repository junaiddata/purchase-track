from django.urls import path
from . import views
from . import export_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('quotation/<int:pk>/update-status/', views.update_quotation_status, name='update_quotation_status'),
    path('upload-items/', views.upload_items, name='upload_items'),
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('create-quotation/', views.create_quotation, name='create_quotation'),
    path('quotation/<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('quotation/<int:pk>/edit/', views.edit_quotation, name='edit_quotation'),
    path('quotation/<int:pk>/delete/', views.delete_quotation, name='delete_quotation'),
    path('release-item/<int:pk>/', views.release_item, name='release_item'),
    path('receive-release/<int:pk>/', views.receive_release, name='receive_release'),
    path('release/<int:pk>/edit/', views.edit_release, name='edit_release'),
    path('receive-item/<int:pk>/', views.receive_item, name='receive_item'),
    path('sales/', views.sales_dashboard, name='sales_dashboard'),
    path('sales/track/', views.sales_firm_track, name='sales_firm_track'),
    path('sales/track/export/pdf/', export_views.export_sales_track_pdf, name='export_sales_track_pdf'),
    path('consolidated/', views.consolidated_view, name='consolidated_view'),
    path('api/update-reorder-qty/', views.update_reorder_qty, name='update_reorder_qty'),
    path('api/reset-reorder-qty/', views.reset_reorder_qty, name='reset_reorder_qty'),
    path('consolidated/export/excel/', export_views.export_consolidated_excel, name='export_consolidated_excel'),
    path('consolidated/export/pdf/', export_views.export_consolidated_pdf, name='export_consolidated_pdf'),
    path('api/items-by-firm/', views.get_items_by_firm, name='get_items_by_firm'),
    path('api/item-totals/', views.api_item_totals, name='api_item_totals'),
    path('api/upload-quotation-items/', views.upload_quotation_items_excel, name='upload_quotation_items_excel'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Manufacturer Management
    path('manufacturers/', views.manufacturer_list, name='manufacturer_list'),
    path('manufacturers/add/', views.manufacturer_create, name='manufacturer_create'),
    path('manufacturers/<int:pk>/edit/', views.manufacturer_edit, name='manufacturer_edit'),
    path('manufacturers/<int:pk>/delete/', views.manufacturer_delete, name='manufacturer_delete'),
    path('manufacturers/upload/', views.manufacturer_upload, name='manufacturer_upload'),
    path('run-stock-import/', views.run_stock_import, name='run_stock_import'),
    
    # Local Purchase Module
    path('local-purchase/', views.local_purchase_dashboard, name='local_purchase_dashboard'),
    path('local-purchase/list/', views.local_purchase_list, name='local_purchase_list'),
    path('local-purchase/upload/', views.local_purchase_upload, name='local_purchase_upload'),
]
