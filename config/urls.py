# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Birinchi bo'lib o'zingizning veb-ilovangiz URL'larini tekshiring
    path('', include('web.urls')),

    # So'ngra Django'ning standart admin paneliga murojaat qiling
    path('admin/', admin.site.urls),

    # Agar API-ga murojaat qilishni xohlasangiz, uning URL'larini qo'shing
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)