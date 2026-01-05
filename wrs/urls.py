from django.contrib import admin
from django.urls import path, include
from adminapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    path('', include('adminapp.urls')),
    path('user/', include('userapp.urls')),   # ✅ Added userapp URLs
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
