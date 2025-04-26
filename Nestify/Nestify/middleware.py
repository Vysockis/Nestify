from django.shortcuts import redirect

class PaymentRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.path.startswith('/family/payment/') or request.path.startswith('/family/webhook/'):
            return self.get_response(request)

        try:
            family = request.user.getFamily()
            if not family.is_paid:
                return redirect('payment_required')
        except AttributeError:
            pass

        return self.get_response(request) 