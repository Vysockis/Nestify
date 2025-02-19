from django.http import JsonResponse
from Nestify.decorators import family_member_required
from List import models as lModels
from collections import defaultdict
from . import models
from datetime import datetime
from django.utils import timezone
from calendar import monthrange

# Create your views here.
@family_member_required
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

    start_date = datetime(startYear, startMonth, 1, 0, 0, 0, tzinfo=timezone.get_current_timezone())

    last_day = monthrange(endYear, endMonth)[1]
    end_date = datetime(endYear, endMonth, last_day, 23, 59, 59, tzinfo=timezone.get_current_timezone())


    operation_list = lModels.List.get_family_list_finance(family).order_by("-datetime")

    newest = get_newest_operations(operation_list)
    operation_list = operation_list.filter(datetime__gte=start_date, datetime__lte=end_date)
    chart = get_chart(operation_list)
    pie = get_pie(operation_list)

    payload = {
        "chart": chart,
        "pie": pie,
        "newest": newest
    }

    return JsonResponse({"data": payload}, safe=False)


def get_newest_operations(operation_list):
    operation_list = operation_list[:5]

    result = [
        {"category": op.category.name, "amount": op.amount} for op in operation_list
    ]

    return result

def get_chart(operation_list):
    monthly_data = defaultdict(lambda: {"expenses": 0, "income": 0})

    # Aggregate expenses and income by month
    for operation in operation_list:
        month_label = operation.datetime.strftime("%Y-%m")  # Format as YYYY-MM

        if operation.amount < 0:
            monthly_data[month_label]["expenses"] += abs(operation.amount)  # Assuming negative values are expenses
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
