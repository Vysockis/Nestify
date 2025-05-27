from django.http import JsonResponse
from Nestify.decorators import parent_required
from List import models as lModels
from collections import defaultdict
from . import models
from datetime import datetime
from django.utils import timezone
from calendar import monthrange
from django.shortcuts import render
import pytesseract
import os
import traceback  # Added for debug tracing
import re
from PIL import Image
import io
import tempfile
from pdf2image import convert_from_bytes
import json
from decimal import Decimal

# Create your views here.


@parent_required
def dashboard(request):
    """API endpoint to fetch family list and items."""

    try:
        startYear = int(request.GET.get('startYear'))
        startMonth = int(request.GET.get('startMonth'))
        endYear = int(request.GET.get('endYear'))
        endMonth = int(request.GET.get('endMonth'))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid date parameters"}, status=400)

    user = request.user
    family = user.getFamily()

    start_date = datetime(startYear, startMonth, 1, 0, 0,
                          0, tzinfo=timezone.get_current_timezone())

    last_day = monthrange(endYear, endMonth)[1]
    end_date = datetime(
        endYear,
        endMonth,
        last_day,
        23,
        59,
        59,
        tzinfo=timezone.get_current_timezone())

    operation_list = lModels.List.get_family_list_finance(
        family).order_by("-datetime")

    newest = get_newest_operations(operation_list)

    # Filter by date range and get all operations
    date_filtered_operations = operation_list.filter(
        datetime__gte=start_date, datetime__lte=end_date)
    all_operations = get_all_operations(date_filtered_operations)

    # Continue with other processing
    chart = get_chart(date_filtered_operations)
    pie = get_pie(date_filtered_operations)

    payload = {
        "chart": chart,
        "pie": pie,
        "newest": newest,
        "all_operations": all_operations
    }

    return JsonResponse({"data": payload}, safe=False)


@parent_required
def scan_receipt(request):
    """API endpoint to scan receipt and extract relevant information."""
    print("\n====== RECEIPT SCANNING STARTED ======")
    print(f"Request method: {request.method}")

    if request.method != 'POST':
        print("Error: Only POST method is allowed")
        return JsonResponse(
            {"error": "Only POST method is allowed"}, status=405)

    try:
        # Get receipt image from request
        print("Looking for receipt_image in request.FILES...")
        receipt_image = request.FILES.get('receipt_image')

        if not receipt_image:
            print("Error: No receipt image provided in request")
            return JsonResponse(
                {"error": "No receipt image provided"}, status=400)

        print(f"Receipt image found: {receipt_image.name}, size: {receipt_image.size} bytes, content type: {receipt_image.content_type}")  # type: ignore

        # Process image data
        print("Reading image data...")
        image_data = receipt_image.read()
        print(f"Read {len(image_data)} bytes of image data")

        # Set Tesseract path directly to the installed location
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        print(f"Setting Tesseract path to: {tesseract_path}")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Check if Tesseract is accessible
        if not os.path.exists(tesseract_path):
            print(f"ERROR: Tesseract not found at {tesseract_path}")
            return JsonResponse({
                "error": f"Tesseract OCR not found at {tesseract_path}. Please verify installation."
            }, status=500)
        else:
            print(f"Tesseract executable found at: {tesseract_path}")

        # Check if the file is a PDF
        is_pdf = receipt_image.name.lower().endswith('.pdf')
        print(f"Is PDF format: {is_pdf}")

        try:
            # Try to perform actual OCR
            print("Starting OCR processing...")
            text = ""
            if is_pdf:
                print("Processing PDF file...")
                # Convert PDF to images
                with tempfile.TemporaryDirectory() as path:
                    images = convert_from_bytes(
                        image_data, dpi=300, output_folder=path)
                    print(f"Converted PDF to {len(images)} images")
                    for i, img in enumerate(images):
                        print(f"Processing PDF page {i + 1}...")
                        page_text = pytesseract.image_to_string(
                            img, lang='lit')
                        text += page_text + "\n"
            else:
                print("Processing image file...")
                # Process regular image
                image = Image.open(io.BytesIO(image_data))
                # Save original dimensions for debugging
                orig_width, orig_height = image.size
                print(f"Image dimensions: {orig_width}x{orig_height}")

                # Convert to grayscale to improve OCR
                if image.mode != 'L':
                    print("Converting image to grayscale...")
                    image = image.convert('L')

                # Perform OCR
                print("Performing OCR with Tesseract...")
                text = pytesseract.image_to_string(image, lang='lit')

            print("Extracted text from receipt:")
            print(text)

            if not text.strip():
                print("ERROR: No text extracted from the image")
                return JsonResponse({
                    "error": "Could not extract text from the image. Please make sure the receipt is clear and well-lit."
                }, status=400)

            # Extract data from the text
            print("Extracting data from OCR text...")
            items = []
            total_amount = 0
            store_name = None

            # Try to identify the store
            print("Trying to identify store...")
            store_pattern = r"(LIDL|MAXIMA|IKI|RIMI|NORFA)"
            store_match = re.search(store_pattern, text, re.IGNORECASE)
            if store_match:
                store_name = store_match.group(1).upper()
                print(f"Store identified: {store_name}")
            else:
                print("Store not identified from receipt")

            # Extract VAT information
            vat_amount = 0
            vat_pattern = r'PVM\s+(\d+[.,]\d{2})'
            for line in text.split('\n'):
                vat_match = re.search(vat_pattern, line, re.IGNORECASE)
                if vat_match:
                    try:
                        vat_str = vat_match.group(1).replace(',', '.')
                        vat_amount = float(vat_str)
                        print(f"Found VAT amount: {vat_amount}")
                    except ValueError as e:
                        print(f"Error parsing VAT amount: {e}")

            # Extract items and prices
            lines = text.split('\n')
            print(f"Receipt contains {len(lines)} lines of text")

            # Store-specific patterns
            if store_name:
                print(f"Using {store_name}-specific parsing patterns")
                
                # LIDL patterns
                if store_name == "LIDL":
                    total_pattern = r"(Tarpinė suma|Iš viso|Suma|Galutinė suma|PVM mokėtojo kodas)[:\s]*.*?(\d+[.,]\d{2})"
                    item_pattern = r'([A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž0-9\.\s\-\"\']+?)[\s]+?(\d+[.,]\d{2})[\s]*([A-Z])?'
                
                # MAXIMA patterns
                elif store_name == "MAXIMA":
                    total_pattern = r"(Viso|Suma|Mokėti)[:\s]*.*?(\d+[.,]\d{2})"
                    item_pattern = r'([A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž0-9\.\s\-\"\']+?)[\s]+(\d+[.,]\d{2})'
                
                # IKI patterns
                elif store_name == "IKI":
                    total_pattern = r"(Viso|Suma|Mokėti)[:\s]*.*?(\d+[.,]\d{2})"
                    item_pattern = r'([A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž0-9\.\s\-\"\']+?)[\s]+(\d+[.,]\d{2})'
                
                # RIMI patterns
                elif store_name == "RIMI":
                    total_pattern = r"(Viso|Suma|Mokėti)[:\s]*.*?(\d+[.,]\d{2})"
                    item_pattern = r'([A-Za-zĄČĘĖĮŠŲŪŽąčęėįšųūž0-9\.\s\-\"\']+?)[\s]+(\d+[.,]\d{2})'

                # Try to find the total amount
                for line in lines:
                    total_match = re.search(total_pattern, line, re.IGNORECASE)
                    if total_match:
                        try:
                            total_str = total_match.group(2).replace(',', '.')
                            total_amount = float(total_str)
                            print(f"Found total amount: {total_amount}")
                            break
                        except ValueError as e:
                            print(f"Error parsing total amount: {e}")

                # Process items
                for line in lines:
                    item_match = re.search(item_pattern, line, re.IGNORECASE)
                    if item_match:
                        try:
                            name = item_match.group(1).strip()
                            price = float(item_match.group(2).replace(',', '.'))

                            # Remove product codes (numbers) from the beginning of item names
                            name = re.sub(r'^\d+\s+', '', name)

                            # Skip items that are likely not actual products
                            skip_words = ['suma', 'viso', 'mokėtojo', 'kvitas', 'grąža', 'PVM', 'Mokėti']
                            if any(word.lower() in name.lower() for word in skip_words):
                                continue

                            # Skip items that are just numbers or very short codes
                            if re.match(r'^\d+$', name) or len(name.strip()) <= 3:
                                print(f"Skipping numeric code or short item: {name}")
                                continue

                            # Check if this item is already in our list
                            if not any(item['name'] == name for item in items):
                                items.append({
                                    'name': name,
                                    'price': price,
                                    'quantity': 1
                                })
                                print(f"Found item: {name} - {price}")
                        except ValueError as e:
                            print(f"Error parsing item: {e}")

            if not items and total_amount == 0:
                print("WARNING: Could not extract items or total. Returning error.")
                return JsonResponse({
                    "success": False,
                    "error": "Nepavyko nuskaityti duomenų"
                }, status=400)

            # If we couldn't extract items but have a total, create a single
            # item
            if not items and total_amount > 0:
                store_text = store_name if store_name else 'parduotuvėje'
                items.append({
                    'name': f"Pirkinys {store_text}",
                    'price': total_amount,
                    'quantity': 1
                })
                print(f"Created generic item with total amount: {total_amount}")

            # If we have no total but have items, sum up the items
            if total_amount == 0 and items:
                total_amount = sum(item['price'] for item in items)
                print(f"Calculated total from items: {total_amount}")

            # Add VAT as a separate item if it was found
            if vat_amount > 0:
                vat_item = {
                    'name': 'PVM',
                    'price': vat_amount,
                    'quantity': 1
                }
                print(f"Adding VAT as item: {vat_amount}")
                items.append(vat_item)

                # Make sure the total includes VAT if it was found
                # First check if the total already includes VAT
                items_total = sum(item['price'] for item in items)
                if abs(
                        total_amount -
                        items_total) > 0.01:  # If there's a discrepancy
                    print(
                        f"Updating total to include VAT. Old: {total_amount}, New: {items_total}")
                    total_amount = items_total

            category_id = None
            try:
                # Default to "Maistas" category if available
                food_category = models.Category.objects.filter(
                    name__icontains='Maist').first()
                if food_category:
                    category_id = food_category.pk
                    print(f"Using food category: {food_category.name}, id: {food_category.pk}")
            except Exception as e:
                print(f"Error finding category: {str(e)}")

            response_data = {
                "success": True,
                "store": store_name,
                "total_amount": total_amount,
                "items": items,
                "category_id": category_id,
                "vat_amount": vat_amount
            }

            print("Returning successful OCR response:")
            print(response_data)
            print("====== RECEIPT SCANNING COMPLETED SUCCESSFULLY ======\n")
            return JsonResponse(response_data)

        except Exception as e:
            print(f"ERROR in OCR processing: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")

            # Return error message instead of mock data
            print("Returning error message")
            return JsonResponse({
                "success": False,
                "error": "Nepavyko nuskaityti duomenų"
            }, status=400)

    except Exception as e:
        print("\n====== RECEIPT SCANNING FAILED ======")
        print(f"General error during receipt scanning: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        print("======================================\n")
        return JsonResponse({"error": str(e)}, status=500)


@parent_required
def finance(request):
    """Render the finance page."""
    return render(request, 'finance/finance.html')


def get_newest_operations(operation_list):
    operation_list = operation_list[:5]

    result = [{"category": op.category.name, "amount": op.amount}
              for op in operation_list]

    return result


def get_chart(operation_list):
    monthly_data = defaultdict(lambda: {"expenses": 0, "income": 0})

    # Aggregate expenses and income by month
    for operation in operation_list:
        month_label = operation.datetime.strftime("%Y-%m")  # Format as YYYY-MM

        if operation.amount < 0:
            # Assuming negative values are expenses
            monthly_data[month_label]["expenses"] += abs(operation.amount)
        else:
            monthly_data[month_label]["income"] += operation.amount

    # Sort by month (ascending order)
    sorted_months = sorted(monthly_data.keys())

    # Extract labels and data lists
    labels = sorted_months
    dataExp = [monthly_data[month]["expenses"] for month in sorted_months]
    dataInc = [monthly_data[month]["income"] for month in sorted_months]

    result = {
        "labels": labels,
        "dataExp": dataExp,
        "dataInc": dataInc
    }

    return result


def get_pie(operation_list):
    labels = []
    data = []
    backgroundColor = []

    categories = models.Category.objects.all()

    for category in categories:
        cat_operation_list = operation_list.filter(category=category)

        total = 0
        for item in cat_operation_list:
            total += item.amount

        if total < 0:
            labels.append(category.name)
            data.append(total)
            backgroundColor.append(category.color)

    result = {
        "labels": labels,
        "data": data,
        "backgroundColor": backgroundColor
    }

    return result

# Create your views here.


@parent_required
def categories(request):
    """API endpoint to fetch finance categories."""
    categories = models.Category.objects.all()
    category_data = []
    for category in categories:
        category_data.append({
            "id": category.pk,
            "name": category.name,
            "income": category.income,
            "color": category.color
        })

    return JsonResponse({"finance_categories": category_data}, safe=False)


def get_all_operations(operation_list):
    """Returns all operations in the given operation list with formatting."""
    result = []

    for op in operation_list:
        # Check if the operation has any items
        has_items = op.listitem_set.exists()

        result.append({
            "id": op.id,
            "category": op.category.name,
            "amount": op.amount,
            "date": op.datetime.strftime("%Y-%m-%d"),
            "has_items": has_items
        })

    return result


@parent_required
def delete_operation(request, operation_id):
    """API endpoint to delete finance operation."""
    if request.method == 'POST':
        try:
            operation = lModels.List.objects.get(
                id=operation_id, list_type='FINANCE')
            operation.delete()
            return JsonResponse({"success": True})
        except lModels.List.DoesNotExist:
            return JsonResponse({"error": "Operation not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@parent_required
def edit_operation(request, operation_id):
    """API endpoint to edit finance operation."""
    if request.method == 'POST':
        try:
            operation = lModels.List.objects.get(
                id=operation_id, list_type='FINANCE')
            data = json.loads(request.body)

            if 'date' in data:
                try:
                    operation.datetime = datetime.fromisoformat(
                        data['date'].replace('Z', '+00:00'))
                except ValueError:
                    try:
                        operation.datetime = datetime.strptime(
                            data['date'], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        operation.datetime = datetime.strptime(
                            data['date'], '%Y-%m-%dT%H:%M')

            # Update amount if provided
            if 'amount' in data:
                operation.amount = Decimal(data['amount'])

            operation.save()
            return JsonResponse({"success": True})
        except lModels.List.DoesNotExist:
            return JsonResponse({"error": "Operation not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@parent_required
def edit_operation_item(request, item_id):
    """API endpoint to edit operation item."""
    if request.method == 'POST':
        try:
            item = lModels.ListItem.objects.get(id=item_id)
            data = json.loads(request.body)

            if 'name' in data:
                item.name = data['name']

            if 'amount' in data:
                item.amount = Decimal(data['amount'])
            if 'quantity' in data:
                item.qty = int(data['quantity'])

            item.save()
            return JsonResponse({"success": True})
        except lModels.ListItem.DoesNotExist:
            return JsonResponse({"error": "Item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)
