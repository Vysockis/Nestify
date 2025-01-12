from django.contrib import admin
from django.urls import path, include
from cprofile import views as cviews

urlpatterns = [
    path('family/', include('Family.urls')),
    path('finance/', include('Finance.urls')),
    path('inventory/', include('Inventory.urls')),
    path('list/', include('List.urls')),
    path('plan/', include('Plan.urls')),
    path('profile/', include('Profile.urls')),
    path('admin/', admin.site.urls),
]
