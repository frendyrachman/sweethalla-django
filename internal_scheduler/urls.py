# internal_scheduler/urls.py (project-level)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('scheduler.urls')), # Pastikan ini ada
]

# Sajikan file media
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Sajikan file statis saat DEBUG=False
urlpatterns += staticfiles_urlpatterns()
