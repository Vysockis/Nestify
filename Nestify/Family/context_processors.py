def user_family(request):
    if request.user.is_authenticated:
        family = request.user.getFamily()
        return {'user_family': family}  # This variable will be available in all templates
    return {'user_family': None}
