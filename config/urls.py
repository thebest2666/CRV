from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Панель администратора
    path('admin/', admin.site.urls),

    # Приложение пользователей (b2b-аккаунты)
    path('users/', include('users.urls', namespace='users')),

    # Приложение каталога (полностью управляет корнем сайта, включая /contacts/ и /info/)
    path('', include('catalog.urls', namespace='catalog')),
]

# Раздача медиа и статики в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
