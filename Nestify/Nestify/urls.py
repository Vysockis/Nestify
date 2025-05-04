from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django_prometheus import exports

urlpatterns = [
    path("metrics/", exports.ExportToDjangoView, name="prometheus-metrics"),
    path('family/', include('Family.urls')),
    path('finance/', include('Finance.urls')),
    path('inventory/', include('Inventory.urls')),
    path('list/', include('List.urls')),
    path('plan/', include('Plan.urls')),
    path('', include('Profile.urls')),
    path('dashboard/', include('Dashboard.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
