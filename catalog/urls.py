from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from .views import (
    IndexView,
    CatalogView,
    ProductDetailView,
    AdListAPIView,
    AdViewSet,
    CategoryViewSet,
    SubcategoryViewSet,
    contacts,
    info, SendKPRequestView
)

app_name = 'catalog'

# Настройка роутера для REST API
router = DefaultRouter()
router.register(r'api/products', AdViewSet, basename='api-product')
router.register(r'api/categories', CategoryViewSet, basename='api-category')
router.register(r'api/subcategories', SubcategoryViewSet, basename='api-subcategory')

urlpatterns = [
    # Главная страница (витрина)
    path('', IndexView.as_view(), name='index'),

    # Каталог оборудования
    path('catalog/', CatalogView.as_view(), name='catalog'),

    # СТРАХОВКА ДЛЯ КЭША: Перенаправляет старый URL /search/?q=... на новый /catalog/?search=...
    path('search/', RedirectView.as_view(url='/catalog/', query_string=True), name='old_search_redirect'),

    # Детальная карточка товара
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),

    # Информационные страницы (добавь пути, если планируешь выводить их через этот urls.py)
    path('contacts/', contacts, name='contacts'),
    path('info/', info, name='info'),

    # REST API эндпоинты
    path('api/list/', AdListAPIView.as_view(), name='product-list-api'),
    path('', include(router.urls)),
    path('products/send-kp/', SendKPRequestView.as_view(), name='send_kp_request'),
]
