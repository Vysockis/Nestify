from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from Nestify.decorators import family_member_required
from django.utils import timezone
from .models import Item, ItemOperation, ItemType
from datetime import datetime
import json

@login_required
@family_member_required
def inventory_dashboard(request):
    return render(request, 'inventory/dashboard.html', {
        'active_page': 'inventory',
        'item_types': ItemType.choices
    })

@login_required
@family_member_required
def item_list(request):
    family = request.user.getFamily()
    items = Item.objects.filter(family=family)
    
    item_type = request.GET.get('type')
    if item_type and item_type in [ItemType.FOOD, ItemType.MEDICINE]:
        items = items.filter(item_type=item_type)
    
    return render(request, 'inventory/items.html', {
        'items': items,
        'active_page': 'inventory',
        'selected_type': item_type,
        'item_types': ItemType.choices
    })

@login_required
@family_member_required
def add_item(request):
    if request.method == 'POST':
        family = request.user.getFamily()
        
        name = request.POST.get('name')
        item_type = request.POST.get('item_type')
        qty = int(request.POST.get('qty', 1))
        exp_date_str = request.POST.get('exp_date')
        
        if not name or not item_type:
            return JsonResponse({'error': 'Būtina užpildyti pavadinimą ir tipą'}, status=400)
        
        # Find or create the item (product definition)
        item, created = Item.objects.get_or_create(
            family=family,
            name=name,
            item_type=item_type,
            defaults={
                'statistics_qty': 0
            }
        )
        
        # Update statistics qty
        item.statistics_qty += qty
        item.save()
        
        # Create the item operation (actual inventory instance with its own expiry date)
        exp_date = None
        if exp_date_str:
            try:
                exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Neteisingas galiojimo datos formatas'}, status=400)
        
        # Always create a new inventory operation - this allows same product with different exp dates
        ItemOperation.objects.create(
            item=item,
            qty=qty,
            exp_date=exp_date,
            price=0
        )
        
        return JsonResponse({'success': True, 'redirect': '/inventory/items/'})
    
    return render(request, 'inventory/add_item.html', {
        'active_page': 'inventory',
        'item_types': ItemType.choices
    })

@login_required
@family_member_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, family=request.user.getFamily())
    
    if request.method == 'POST':
        name = request.POST.get('name')
        item_type = request.POST.get('item_type')
        
        if not name or not item_type:
            return JsonResponse({'error': 'Būtina užpildyti pavadinimą ir tipą'}, status=400)
        
        item.name = name
        item.item_type = item_type
        item.save()
        
        return JsonResponse({'success': True, 'redirect': '/inventory/items/'})
    
    return render(request, 'inventory/edit_item.html', {
        'item': item,
        'active_page': 'inventory',
        'item_types': ItemType.choices
    })

@login_required
@family_member_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, family=request.user.getFamily())
    
    if request.method == 'POST':
        item.delete()
        return redirect('inventory:items')
    
    return render(request, 'inventory/delete_item.html', {
        'item': item,
        'active_page': 'inventory'
    })

@login_required
@family_member_required
def delete_contract(request, item_id):
    # Get the contract item and verify it belongs to user's family
    item = get_object_or_404(Item, id=item_id, family=request.user.getFamily(), item_type=ItemType.CONTRACTS)
    
    if request.method == 'POST':
        item.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Neteisingas užklausos metodas'}, status=400)

@login_required
@family_member_required
def delete_operation(request, operation_id):
    # Gauti operaciją ir patikrinti, ar ji priklauso vartotojo šeimai
    operation = get_object_or_404(ItemOperation, id=operation_id, item__family=request.user.getFamily())
    
    if request.method == 'POST':
        # Atnaujinti prekės statistinius duomenis
        item = operation.item
        item.statistics_qty -= operation.qty
        if item.statistics_qty < 0:
            item.statistics_qty = 0
        item.save()
        
        # Ištrinti operaciją
        operation.delete()
        
        # Patikrinti, ar liko operacijų susietų su šia preke
        remaining_operations = ItemOperation.objects.filter(item=item).count()
        if remaining_operations == 0:
            # Jei neliko operacijų, ištrinti ir pačią prekę
            item.delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Neteisingas užklausos metodas'}, status=400)

@login_required
@family_member_required
def api_items(request):
    family = request.user.getFamily()
    
    # Filtruoti pagal tipą, jei nurodyta
    item_type = request.GET.get('type')
    if item_type and item_type in [ItemType.FOOD, ItemType.MEDICINE, ItemType.CONTRACTS]:
        base_items = Item.objects.filter(family=family, item_type=item_type)
    else:
        base_items = Item.objects.filter(family=family)
    
    # Gauti visas operacijas
    operations = ItemOperation.objects.filter(item__in=base_items).order_by('-exp_date')
    
    items_data = []
    
    # Grupuoti operacijas pagal prekę
    grouped_items = {}
    for op in operations:
        item = op.item
        item_key = f"{item.id}"
        
        if item_key not in grouped_items:
            grouped_items[item_key] = {
                'id': item.id,
                'name': item.name,
                'type': item.get_item_type_display(),
                'type_value': item.item_type,
                'total_qty': 0,
                'operations': [],
                'earliest_exp_date': None,
                'is_expired': False,
                'is_expiring_soon': False,
                'is_expiring_very_soon': False
            }
        
        # Add operation details
        if op.exp_date:
            grouped_items[item_key]['operations'].append({
                'id': op.id,
                'qty': op.qty,
                'exp_date': op.exp_date
            })
            
            # Update earliest expiration date if this one is earlier
            if (not grouped_items[item_key]['earliest_exp_date'] or 
                op.exp_date < grouped_items[item_key]['earliest_exp_date']):
                grouped_items[item_key]['earliest_exp_date'] = op.exp_date
        
        # Update total quantity
        if item.item_type != ItemType.CONTRACTS:
            grouped_items[item_key]['total_qty'] += op.qty
    
    # Process expiration status for each item
    today = timezone.now().date()
    for item_data in grouped_items.values():
        exp_date = item_data['earliest_exp_date']
        if exp_date:
            days_until_expiry = (exp_date - today).days
            item_data['is_expired'] = days_until_expiry < 0
            item_data['is_expiring_soon'] = days_until_expiry <= 7 and days_until_expiry >= 0
            item_data['is_expiring_very_soon'] = days_until_expiry <= 3 and days_until_expiry >= 0
            item_data['exp_date'] = exp_date.strftime('%Y-%m-%d')
        else:
            item_data['exp_date'] = None
        
        # Clean up the data structure
        del item_data['operations']
        del item_data['earliest_exp_date']
        
        items_data.append(item_data)
    
    # Sort items by expiration date
    items_data.sort(key=lambda x: x.get('exp_date') or '9999-12-31')
    
    return JsonResponse({'items': items_data})

@login_required
@family_member_required
def api_expiring_items(request):
    family = request.user.getFamily()
    base_items = Item.objects.filter(family=family)
    
    # Get all operations
    operations = ItemOperation.objects.filter(item__in=base_items).order_by('exp_date')
    
    items_data = []
    today = timezone.now().date()
    
    # Create data for each operation
    for op in operations:
        exp_date = op.exp_date
        if exp_date:
            days_until_expiry = (exp_date - today).days
            # Include expired items (negative days) and items expiring in 3 days
            if days_until_expiry <= 3:
                items_data.append({
                    'id': op.id,
                    'name': op.item.name,
                    'type': op.item.get_item_type_display(),
                    'type_value': op.item.item_type,
                    'qty': op.qty,
                    'exp_date': exp_date.strftime('%Y-%m-%d'),
                    'days_left': days_until_expiry,
                    'is_expired': days_until_expiry < 0
                })
    
    return JsonResponse({"items": items_data}, safe=False)

@login_required
@family_member_required
def update_operation(request, operation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get the operation and verify it belongs to user's family
        operation = get_object_or_404(ItemOperation, id=operation_id)
        if operation.item.family != request.user.getFamily():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Parse the request body
        data = json.loads(request.body)
        new_qty = data.get('qty')
        
        if not new_qty or new_qty < 1:
            return JsonResponse({'error': 'Kiekis turi būti teigiamas skaičius'}, status=400)
        
        # Calculate the quantity difference
        qty_difference = new_qty - operation.qty
        
        # Update the operation quantity
        operation.qty = new_qty
        operation.save()
        
        # Update the item's statistics
        item = operation.item
        item.statistics_qty += qty_difference
        item.save()
        
        return JsonResponse({'success': True})
        
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Neteisingi duomenys'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
