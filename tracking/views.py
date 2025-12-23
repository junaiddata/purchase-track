import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from .models import ItemMaster, Quotation, QuotationItem, Release, Shipment, Manufacturer
from .forms import UploadItemForm, QuotationForm, QuotationItemFormSet, ShipmentForm, ReleaseForm, ManufacturerForm, UploadManufacturerForm
from django.http import JsonResponse
import json
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .decorators import admin_required, sales_required
from django.core.management import call_command
from io import StringIO

@login_required
@admin_required
def dashboard(request):
    """
    Main dashboard view. Redirects based on user group (future).
    For now, nice landing page.
    """
    # Fetch recent quotations
    recent_quotations = Quotation.objects.all().order_by('-created_at')[:5]
    
    # Calculate stats
    total_items = ItemMaster.objects.count()
    pending_quotations = Quotation.objects.filter(status='DRAFT').count()
    
    # Incoming shipments (In Transit) - Release objects not received
    incoming_shipments = Release.objects.filter(is_received=False).count()

    context = {
        'recent_quotations': recent_quotations,
        'total_items': total_items,
        'pending_quotations': pending_quotations,
        'incoming_shipments': incoming_shipments,
    }
    return render(request, 'tracking/dashboard.html', context)

@login_required
@admin_required
def update_quotation_status(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    
    if request.method == 'POST':
        # Check if it's a form submission or JSON
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                new_status = data.get('status')
                if new_status in dict(Quotation.STATUS_CHOICES):
                    quotation.status = new_status
                    quotation.save()
                    return JsonResponse({'success': True})
                return JsonResponse({'success': False, 'error': 'Invalid status'})
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        else:
            # Standard form submission (e.g. from the list page Save button)
            new_status = request.POST.get('status')
            if new_status in dict(Quotation.STATUS_CHOICES):
                quotation.status = new_status
                quotation.save()
                messages.success(request, f"Status for {quotation.reference_number} updated to {quotation.get_status_display()}.")
            else:
                messages.error(request, "Invalid status selected.")
            
            return redirect('quotation_list') # Redirect back to the list
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@never_cache
@login_required
@admin_required
def quotation_list(request):
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    quotes = Quotation.objects.all().order_by('-created_at')
    
    # helper for filter
    if status_filter != 'all':
        # exact match for status keys
        quotes = quotes.filter(status=status_filter.upper())

    # Search Logic
    if search_query:
        quotes = quotes.filter(
            models.Q(reference_number__icontains=search_query) |
            models.Q(supplier_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(quotes, 100) # 10 quotes per page
    page = request.GET.get('page')
    try:
        quotes_page = paginator.page(page)
    except PageNotAnInteger:
        quotes_page = paginator.page(1)
    except EmptyPage:
        quotes_page = paginator.page(paginator.num_pages)
    
    return render(request, 'tracking/quotation_list.html', {
        'quotes': quotes_page, 
        'filter': status_filter,
        'search': search_query
    })

@login_required
@admin_required
def release_item(request, pk):
    item = get_object_or_404(QuotationItem, pk=pk)
    
    if request.method == 'POST':
        form = ReleaseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                release = form.save(commit=False)
                release.quotation_item = item
                release.save()
                
                # Update item? (quantity calculations are dynamic properties)
                messages.success(request, f"Release created for {item.item.item_code}!")
                return redirect('quotation_detail', pk=item.quotation.pk)
    else:
        # Pre-fill specific initial data if needed
        form = ReleaseForm(initial={'quantity_released': item.balance_to_release})

    return render(request, 'tracking/release_item.html', {
        'form': form,
        'item': item
    })

@login_required
@admin_required
def receive_release(request, pk):
    # This view confirms that a Release (truck) has arrived
    release = get_object_or_404(Release, pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            release.is_received = True
            release.save()
            
            # Auto-create a Shipment record to log this receipt officially?
            # Or just mark release as received?
            # If we want to maintain the Shipment model as the source of "Stock", we should create one.
            Shipment.objects.create(
                quotation_item=release.quotation_item,
                quantity_received=release.quantity_released,
                received_date=pd.Timestamp.now().date(), # Default to today
                remarks=f"Auto-received from Release {release.container_info}"
            )
            
            messages.success(request, "Release marked as Received and Stock updated.")
            return redirect('quotation_detail', pk=release.quotation_item.quotation.pk)

    return render(request, 'tracking/receive_release_confirm.html', {'release': release})

@login_required
@admin_required
def create_quotation(request):
    if request.method == 'POST':
        print("DEBUG: POST keys received:", list(request.POST.keys()))
        print("DEBUG: POST items-0-item:", request.POST.get('items-0-item'))
        print("DEBUG: POST items-0-quantity_ordered:", request.POST.get('items-0-quantity_ordered'))
        
        form = QuotationForm(request.POST)
        formset = QuotationItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            print("DEBUG: Forms are valid")
            print(f"DEBUG: Total Forms: {formset.total_form_count()}")
            for i, f in enumerate(formset):
                print(f"DEBUG: Form {i} cleaned_data: {f.cleaned_data}")
                print(f"DEBUG: Form {i} has_changed: {f.has_changed()}")

            try:
                with transaction.atomic():
                    quotation = form.save()
                    quotation.created_by = request.user
                    quotation.save()
                    print(f"DEBUG: Quotation saved: {quotation.pk}")
                    
                    formset.instance = quotation
                    items = formset.save()
                    print(f"DEBUG: Items saved: {len(items)}")
                    
                    messages.success(request, f"Quotation {quotation.reference_number} created successfully!")
                    return redirect('dashboard')
            except Exception as e:
                print(f"Transaction Error: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error creating quotation: {str(e)}")
        else:
             print("DEBUG: Validation FAILED")
             print("Form Errors:", form.errors)
             print("Formset Errors:", formset.errors)
             print("POST Data (partial):", {k: v for k, v in request.POST.items() if 'item' in k})
             
             if formset.errors:
                 messages.error(request, f"Item Errors: {formset.errors}")
             messages.error(request, "Please correct the errors below.")
    else:
        form = QuotationForm()
        formset = QuotationItemFormSet()
        
    return render(request, 'tracking/create_quotation.html', {
        'form': form,
        'formset': formset
    })

@login_required
@admin_required
def quotation_detail(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    
    # Try to get supplier logo
    supplier_logo = None
    try:
        from .models import Supplier
        supplier = Supplier.objects.filter(name=quotation.supplier_name).first()
        if supplier and supplier.logo:
            supplier_logo = supplier.logo
    except:
        pass
    
    return render(request, 'tracking/quotation_detail.html', {
        'quotation': quotation,
        'supplier_logo': supplier_logo,
    })

@login_required
@admin_required
def edit_quotation(request, pk):
    """Edit an existing quotation and its items."""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    # Prevent editing confirmed/completed quotations
    if quotation.status in ['CONFIRMED', 'COMPLETED']:
        messages.warning(request, "Cannot edit a confirmed or completed quotation.")
        return redirect('quotation_detail', pk=pk)
    
    if request.method == 'POST':
        form = QuotationForm(request.POST, instance=quotation)
        formset = QuotationItemFormSet(request.POST, instance=quotation)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    messages.success(request, f"Quotation {quotation.reference_number} updated successfully!")
                    return redirect('quotation_detail', pk=pk)
            except Exception as e:
                messages.error(request, f"Error updating quotation: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = QuotationForm(instance=quotation)
        formset = QuotationItemFormSet(instance=quotation)
    
    return render(request, 'tracking/edit_quotation.html', {
        'form': form,
        'formset': formset,
        'quotation': quotation,
    })

@login_required
@admin_required
def delete_quotation(request, pk):
    """Delete a quotation."""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    # Prevent deleting confirmed/completed quotations
    if quotation.status in ['CONFIRMED', 'COMPLETED']:
        messages.warning(request, "Cannot delete a confirmed or completed quotation.")
        return redirect('quotation_detail', pk=pk)
    
    if request.method == 'POST':
        reference = quotation.reference_number
        quotation.delete()
        messages.success(request, f"Quotation {reference} deleted successfully!")
        return redirect('quotation_list')
    
    return render(request, 'tracking/delete_quotation.html', {
        'quotation': quotation,
    })

@login_required
@admin_required
def receive_item(request, pk):
    item = get_object_or_404(QuotationItem, pk=pk)
    
    # Get pending releases (In Transit) for this item to offer "Quick Receive"
    pending_releases = item.releases.filter(is_received=False)

    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)
            shipment.quotation_item = item
            shipment.save()
            messages.success(request, f"Received {shipment.quantity_received} of {item.item.item_code}")
            
            # Check if fully received and update status if needed?
            # For now, just redirect
            return redirect('quotation_detail', pk=item.quotation.pk)
    else:
        form = ShipmentForm()
    
    return render(request, 'tracking/receive_item.html', {
        'form': form,
        'item': item,
        'pending_releases': pending_releases
    })

@login_required
@admin_required
def upload_items(request):
    if request.method == 'POST':
        form = UploadItemForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file)
                
                # Basic validation: check required columns
                required_columns = ['Item Code', 'Item Description', 'Firm', 'Stock', 'UOM']
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, f"Missing required columns. Expected: {', '.join(required_columns)}")
                    return render(request, 'tracking/upload_items.html', {'form': form})
                
                success_count = 0
                errors = []

                for index, row in df.iterrows():
                    try:
                        code = str(row['Item Code']).strip()
                        desc = str(row['Item Description']).strip()
                        firm = str(row['Firm']).strip()
                        stock = row['Stock'] if pd.notna(row['Stock']) else 0
                        uom = str(row['UOM']).strip()
                        
                        ItemMaster.objects.update_or_create(
                            item_code=code,
                            defaults={
                                'item_description': desc,
                                'item_firm': firm,
                                'item_stock': stock,
                                'uom': uom
                            }
                        )
                        success_count += 1
                    except Exception as e:
                        errors.append(f"Row {index+2}: {str(e)}")
                
                messages.success(request, f"Successfully processed {success_count} items.")
                if errors:
                    messages.warning(request, f"Encountered {len(errors)} errors. First few: {'; '.join(errors[:3])}")
                    
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = UploadItemForm()
    
    return render(request, 'tracking/upload_items.html', {'form': form})

@never_cache
@login_required
@sales_required
def sales_dashboard(request):
    """
    Landing page for Sales. Select Firm.
    """
    # Get firms that have active QuotationItems (either pending release or in transit)
    # We want distinct firm names.
    firm_names = QuotationItem.objects.annotate(
        total_received=Coalesce(Sum('shipments__quantity_received'), 0)
    ).filter(
        models.Q(quotation__status='CONFIRMED') &
        models.Q(quantity_ordered__gt=models.F('total_received'))
    ).values_list('item__item_firm', flat=True).distinct()
    
    # Get supplier logos for these firms
    from .models import Supplier
    suppliers = {s.name: s for s in Supplier.objects.filter(name__in=firm_names)}
    
    # Build list of firms with their logos
    firms_with_logos = [
        {'name': firm, 'logo': suppliers.get(firm).logo if suppliers.get(firm) and suppliers.get(firm).logo else None}
        for firm in firm_names
    ]
    
    return render(request, 'tracking/sales_landing.html', {'firms': firms_with_logos})

@never_cache
@login_required
@sales_required
def sales_firm_track(request):
    firm_name = request.GET.get('firm')
    if not firm_name:
        return redirect('sales_dashboard')
        
    # 1. Incoming (On The Way)
    # Changed from grouping to flat list for Table view
    in_transit_releases = Release.objects.filter(
        quotation_item__item__item_firm=firm_name,
        is_received=False
    ).select_related(
        'quotation_item__item', 
        'quotation_item__quotation',
        'quotation_item__quotation__manufacturer'
    ).order_by('container_info', 'expected_arrival_date')

    # 2. Received (History) with Pagination
    received_queryset = Release.objects.filter(
        quotation_item__item__item_firm=firm_name,
        is_received=True
    ).select_related(
        'quotation_item__item', 
        'quotation_item__quotation'
    ).order_by('-release_date')
    
    paginator = Paginator(received_queryset, 30) # Show 15 records per page
    page_number = request.GET.get('page')
    received_releases = paginator.get_page(page_number)
    
    # 3. Pending (At Factory)
    all_firm_items = QuotationItem.objects.filter(
        item__item_firm=firm_name,
        quotation__status='CONFIRMED'
    ).select_related('item', 'quotation', 'quotation__manufacturer').order_by('expected_delivery_date')
    
    # Filter for items with balance > 0
    pending_items = [item for item in all_firm_items if item.balance_to_release > 0]
    
    # Get supplier logo
    supplier_logo = None
    try:
        from .models import Supplier
        supplier = Supplier.objects.filter(name=firm_name).first()
        if supplier and supplier.logo:
            supplier_logo = supplier.logo
    except:
        pass
    
    return render(request, 'tracking/sales_firm_track.html', {
        'firm': firm_name,
        'in_transit_releases': in_transit_releases, # Updated context variable
        'received_releases': received_releases,
        'pending_items': pending_items,
        'supplier_logo': supplier_logo,
    })

@never_cache
@login_required
def get_items_by_firm(request):
    firm = request.GET.get('firm')
    if not firm:
        return JsonResponse({'items': []})
    
    items = ItemMaster.objects.filter(item_firm=firm).values('id', 'item_code', 'item_description', 'item_upvc').order_by('item_code')
    return JsonResponse({'items': list(items)})

# Manufacturer Management
@login_required
@admin_required
def manufacturer_list(request):
    manufacturers = Manufacturer.objects.all()
    return render(request, 'tracking/manufacturer_list.html', {
        'manufacturers': manufacturers
    })

@login_required
@admin_required
def manufacturer_create(request):
    if request.method == 'POST':
        form = ManufacturerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Manufacturer added successfully!")
            return redirect('manufacturer_list')
    else:
        form = ManufacturerForm()
    return render(request, 'tracking/manufacturer_form.html', {
        'form': form,
        'title': 'Add Manufacturer'
    })

@login_required
@admin_required
def manufacturer_edit(request, pk):
    manufacturer = get_object_or_404(Manufacturer, pk=pk)
    if request.method == 'POST':
        form = ManufacturerForm(request.POST, instance=manufacturer)
        if form.is_valid():
            form.save()
            messages.success(request, "Manufacturer updated successfully!")
            return redirect('manufacturer_list')
    else:
        form = ManufacturerForm(instance=manufacturer)
    return render(request, 'tracking/manufacturer_form.html', {
        'form': form,
        'title': 'Edit Manufacturer'
    })

@login_required
@admin_required
def manufacturer_delete(request, pk):
    manufacturer = get_object_or_404(Manufacturer, pk=pk)
    if request.method == 'POST':
        name = manufacturer.name
        manufacturer.delete()
        messages.success(request, f"Manufacturer {name} deleted successfully!")
        return redirect('manufacturer_list')
    return render(request, 'tracking/manufacturer_confirm_delete.html', {
        'manufacturer': manufacturer
    })

@login_required
@admin_required
def manufacturer_upload(request):
    if request.method == 'POST':
        form = UploadManufacturerForm(request.POST, request.FILES)
        if form.is_valid():
            import pandas as pd
            file = request.FILES['file']
            try:
                df = pd.read_excel(file)
                # Expecting a column 'Manufacturer' or 'Name'
                column_name = None
                for col in ['Manufacturer', 'Name', 'manufacturer', 'name']:
                    if col in df.columns:
                        column_name = col
                        break
                
                if not column_name:
                    messages.error(request, "Could not find a 'Manufacturer' or 'Name' column in Excel.")
                    return render(request, 'tracking/manufacturer_upload.html', {'form': form})
                
                count = 0
                for _, row in df.iterrows():
                    name = str(row[column_name]).strip()
                    if name and name != 'nan':
                        Manufacturer.objects.get_or_create(name=name)
                        count += 1
                
                messages.success(request, f"Successfully imported {count} manufacturers!")
                return redirect('manufacturer_list')
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = UploadManufacturerForm()
    return render(request, 'tracking/manufacturer_upload.html', {'form': form})

@login_required
@admin_required
def run_stock_import(request):
    out = StringIO()
    try:
        call_command('import_stock_api', stdout=out)
        output = out.getvalue()
        messages.success(request, output)
    except Exception as e:
        messages.error(request, f"Error importing stock data: {str(e)}")
    finally:
        out.close()
    return redirect('dashboard')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect based on role
                try:
                    if not hasattr(user, 'profile'):
                        # Auto-create if missing (self-healing)
                        from .models import UserProfile
                        UserProfile.objects.create(user=user, role='SALESMAN') # Default to Salesman or safe default
                        # Reload user
                        user.refresh_from_db()

                    if user.is_superuser:
                         return redirect('dashboard')
                         
                    if hasattr(user, 'profile') and user.profile.role == 'SALESMAN':
                        return redirect('sales_dashboard')
                    else:
                        # Admin or no profile defaults to dashboard
                        return redirect('dashboard')
                except Exception:
                    # Fallback
                    return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'tracking/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
