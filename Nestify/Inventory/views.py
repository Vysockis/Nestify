from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from Nestify.decorators import family_member_required
from django.utils import timezone
from .models import Item, ItemOperation, ItemType
from datetime import datetime

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
    
    # Jei ne POST metodas - grąžinti klaidos žinutę
    return JsonResponse({'error': 'Neteisingas užklausos metodas'}, status=400)

@login_required
@family_member_required
def api_items(request):
    family = request.user.getFamily()
    
    # Filtruoti pagal tipą, jei nurodyta
    item_type = request.GET.get('type')
    if item_type and item_type in [ItemType.FOOD, ItemType.MEDICINE]:
        base_items = Item.objects.filter(family=family, item_type=item_type)
    else:
        base_items = Item.objects.filter(family=family)
    
    # Gauti visas operacijas
    operations = ItemOperation.objects.filter(item__in=base_items).order_by('-exp_date')
    
    items_data = []
    
    # Grupuoti operacijas pagal prekę, kad būtų patogu rodyti sąraše
    grouped_operations = {}
    for op in operations:
        if op.item.id not in grouped_operations:
            grouped_operations[op.item.id] = {
                'item': op.item,
                'operations': [],
                'total_qty': 0
            }
        grouped_operations[op.item.id]['operations'].append(op)
        grouped_operations[op.item.id]['total_qty'] += op.qty
    
    # Sukurti duomenis kiekvienai operacijai
    for item_id, data in grouped_operations.items():
        item = data['item']
        
        for op in data['operations']:
            exp_date = op.exp_date
            
            # Ar baigiasi galiojimas
            is_expiring_soon = False
            is_expired = False
            is_expiring_very_soon = False
            
            if exp_date:
                today = timezone.now().date()
                days_until_expiry = (exp_date - today).days
                is_expiring_soon = days_until_expiry <= 7 and days_until_expiry >= 0
                is_expired = exp_date < today
                is_expiring_very_soon = days_until_expiry <= 3 and days_until_expiry >= 0
            
            items_data.append({
                'id': op.id,  # Operacijos ID, ne prekės
                'item_id': item.id,  # Prekės ID
                'name': item.name,
                'type': item.get_item_type_display(),
                'type_value': item.item_type,
                'qty': op.qty,  # Šios konkrečios operacijos kiekis
                'exp_date': exp_date.strftime('%Y-%m-%d') if exp_date else None,
                'is_expired': is_expired,
                'is_expiring_soon': is_expiring_soon,
                'is_expiring_very_soon': is_expiring_very_soon
            })
    
    # Rūšiuoti pagal galiojimo datą (pirmi, kurių galiojimas baigsis greičiausiai)
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
