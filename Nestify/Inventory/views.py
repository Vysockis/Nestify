from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from Nestify.decorators import family_member_required, parent_required
from django.utils import timezone
from .models import Item, ItemOperation, ItemType
from datetime import datetime
import json
from django.db import IntegrityError


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
@parent_required
def add_item(request):
    if request.method == 'POST':
        family = request.user.getFamily()

        name = request.POST.get('name')
        item_type = request.POST.get('item_type')
        qty = int(request.POST.get('qty', 1))
        exp_date_str = request.POST.get('exp_date')
        buy_date_str = request.POST.get('buy_date')

        if not name or not item_type:
            return JsonResponse(
                {'error': 'Būtina užpildyti pavadinimą ir tipą'}, status=400)

        if not exp_date_str:
            return JsonResponse(
                {'error': 'Būtina nurodyti galiojimo datą'}, status=400)

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

        # Parse buy_date
        if not buy_date_str:
            buy_date = timezone.now().date()
        else:
            try:
                buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(
                    {'error': 'Neteisingas pirkimo datos formatas'}, status=400)

        # Create the item operation (actual inventory instance with its own
        # expiry date)
        exp_date = None
        if exp_date_str:
            try:
                exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(
                    {'error': 'Neteisingas galiojimo datos formatas'}, status=400)

        try:
            print(buy_date)
            print(exp_date)
            ItemOperation.objects.create(
                item=item,
                qty=qty,
                buy_date=buy_date,
                exp_date=exp_date,
                price=0
            )
        except IntegrityError:
            return JsonResponse(
                {'error': 'Toks turto įrašas jau egzistuoja šiai datai'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        return JsonResponse({'success': True, 'redirect': '/inventory/items/'})

    return render(request, 'inventory/add_item.html', {
        'active_page': 'inventory',
        'item_types': ItemType.choices
    })


@login_required
@family_member_required
@parent_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, family=request.user.getFamily())

    if request.method == 'POST':
        name = request.POST.get('name')
        item_type = request.POST.get('item_type')

        if not name or not item_type:
            return JsonResponse(
                {'error': 'Būtina užpildyti pavadinimą ir tipą'}, status=400)

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
@parent_required
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
@parent_required
def add_contract(request):
    if request.method == 'POST':
        family = request.user.getFamily()

        name = request.POST.get('name')
        item_type = ItemType.CONTRACTS

        if not name:
            return JsonResponse(
                {'error': 'Būtina užpildyti pavadinimą'}, status=400)

        # Find or create the item (product definition)
        item, created = Item.objects.get_or_create(
            family=family,
            name=name,
            item_type=item_type,
            defaults={
                'statistics_qty': 0
            }
        )

        # Create the item operation
        ItemOperation.objects.create(
            item=item,
            qty=1,
            price=0
        )

        return JsonResponse({'success': True, 'redirect': '/inventory/items/'})

    return render(request, 'inventory/add_contract.html', {
        'active_page': 'inventory'
    })


@login_required
@family_member_required
@parent_required
def delete_contract(request, item_id):
    # Get the contract item and verify it belongs to user's family
    item = get_object_or_404(
        Item,
        id=item_id,
        family=request.user.getFamily(),
        item_type=ItemType.CONTRACTS)

    if request.method == 'POST':
        # Delete all operations for this item
        ItemOperation.objects.filter(item=item).delete()
        # Delete the item itself
        item.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)


@login_required
@family_member_required
@parent_required
def delete_operation(request, operation_id):
    # Gauti operaciją ir patikrinti, ar ji priklauso vartotojo šeimai
    operation = get_object_or_404(
        ItemOperation,
        id=operation_id,
        item__family=request.user.getFamily())

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
    if item_type and item_type in [
            ItemType.FOOD,
            ItemType.MEDICINE,
            ItemType.CONTRACTS]:
        base_items = Item.objects.filter(family=family, item_type=item_type)
    else:
        base_items = Item.objects.filter(family=family)

    # If user is a kid, exclude contracts
    if request.user.familymember_set.first(
    ) and request.user.familymember_set.first().kid:
        base_items = base_items.exclude(item_type=ItemType.CONTRACTS)

    # Gauti visas operacijas
    operations = ItemOperation.objects.filter(
        item__in=base_items).order_by('-exp_date')

    items_data = []
    today = timezone.now().date()
    for op in operations:
        exp_date = op.exp_date
        days_until_expiry = (exp_date - today).days if exp_date else None
        items_data.append({
            'id': op.id,
            'name': op.item.name,
            'type': op.item.get_item_type_display(),
            'type_value': op.item.item_type,
            'total_qty': op.qty,
            'exp_date': exp_date.strftime('%Y-%m-%d') if exp_date else None,
            'days_left': days_until_expiry,
            'is_expired': days_until_expiry is not None and days_until_expiry < 0,
            'is_expiring_soon': days_until_expiry is not None and days_until_expiry <= 7 and days_until_expiry >= 0,
            'is_expiring_very_soon': days_until_expiry is not None and days_until_expiry <= 3 and days_until_expiry >= 0
        })

    # Sort items by expiration date
    items_data.sort(key=lambda x: x.get('exp_date') or '9999-12-31')

    return JsonResponse({'items': items_data})


@login_required
@family_member_required
def api_expiring_items(request):
    family = request.user.getFamily()
    base_items = Item.objects.filter(family=family)
    if request.user.familymember_set.first(
    ) and request.user.familymember_set.first().kid:
        base_items = base_items.exclude(item_type=ItemType.CONTRACTS)

    # Get all operations
    operations = ItemOperation.objects.filter(
        item__in=base_items).order_by('exp_date')

    items_data = []
    today = timezone.now().date()

    # Create data for each operation
    for op in operations:
        exp_date = op.exp_date
        if exp_date:
            days_until_expiry = (exp_date - today).days
            # Include expired items (negative days) and items expiring in 3
            # days
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
@parent_required
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
            return JsonResponse(
                {'error': 'Kiekis turi būti teigiamas skaičius'}, status=400)

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
