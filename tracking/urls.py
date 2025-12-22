from django.urls import path
from . import views

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
    path('receive-item/<int:pk>/', views.receive_item, name='receive_item'),
    path('sales/', views.sales_dashboard, name='sales_dashboard'),
    path('sales/track/', views.sales_firm_track, name='sales_firm_track'),
    path('api/items-by-firm/', views.get_items_by_firm, name='get_items_by_firm'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Manufacturer Management
    path('manufacturers/', views.manufacturer_list, name='manufacturer_list'),
    path('manufacturers/add/', views.manufacturer_create, name='manufacturer_create'),
    path('manufacturers/<int:pk>/edit/', views.manufacturer_edit, name='manufacturer_edit'),
    path('manufacturers/<int:pk>/delete/', views.manufacturer_delete, name='manufacturer_delete'),
    path('manufacturers/upload/', views.manufacturer_upload, name='manufacturer_upload'),
    path('run-stock-import/', views.run_stock_import, name='run_stock_import'),
]
