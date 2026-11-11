from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Q
from django.contrib import messages
from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny

from .models import Ad, Category, Subcategory
from .serializers import AdSerializer, CategorySerializer, SubcategorySerializer


# =======================================================
# 1. HTML ПРЕДСТАВЛЕНИЕ КАТАЛОГА (С ДВУХРЕЖИМНЫМ ПОИСКОМ)
# =======================================================
class CatalogView(View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()
        products = Ad.objects.all()

        selected_category = request.GET.get('category')
        selected_subcategory = request.GET.get('subcategory')
        search_query = request.GET.get('search') or request.GET.get('q')

        if search_query:
            search_query = search_query.strip()
            products = products.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            if selected_subcategory:
                products = products.filter(subcategory_id=selected_subcategory)
            elif selected_category:
                products = products.filter(subcategory__category_id=selected_category)

        products = products.order_by('-created_at')

        return render(request, 'catalog.html', {
            'products': products,
            'categories': categories,
            'subcategories': subcategories,
            'is_admin': request.user.is_superuser,
            'current_cat': selected_category,
            'current_subcat': selected_subcategory,
            'search_query': search_query
        })

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('catalog:catalog')

        action = request.POST.get('action')

        if action == 'create_category':
            title = request.POST.get('category_title', '').strip()
            if title:
                Category.objects.get_or_create(title=title)
            else:
                messages.error(request, 'Название категории не может быть пустым.')
            return redirect('catalog:catalog')

        elif action == 'create_subcategory':
            title = request.POST.get('subcategory_title', '').strip()
            chosen_category_id = request.POST.get('modal_chosen_category')

            if title:
                cat_obj = None
                if chosen_category_id:
                    try:
                        cat_obj = Category.objects.get(id=chosen_category_id)
                    except Category.DoesNotExist:
                        pass

                Subcategory.objects.get_or_create(title=title, category=cat_obj)
            else:
                messages.error(request, 'Название подкатегории не может быть пустым.')
            return redirect('catalog:catalog')

        else:
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            price_raw = request.POST.get('price', '').strip()
            subcategory_id = request.POST.get('subcategory')
            photo = request.FILES.get('photo')

            # ДОБАВЛЕНО: Обработка флага "В наличии" (если чекбокс не отмечен, в POST ничего не придет)
            in_stock = request.POST.get('in_stock') == 'on'

            subcat_obj = None
            if subcategory_id:
                try:
                    subcat_obj = Subcategory.objects.get(id=subcategory_id)
                except Subcategory.DoesNotExist:
                    pass

            if title and price_raw and description:
                try:
                    price = float(price_raw.replace(',', '.'))
                    Ad.objects.create(
                        title=title,
                        description=description,
                        price=price,
                        subcategory=subcat_obj,
                        photo=photo,
                        in_stock=in_stock  # ДОБАВЛЕНО сохранение статуса наличия
                    )
                    messages.success(request, 'Товар успешно добавлен в каталог.')
                except ValueError:
                    messages.error(request, 'Некорректный формат цены. Используйте только цифры.')
            else:
                messages.error(request, 'Заполните все обязательные поля: Название, Цена, Описание.')

        return redirect('catalog:catalog')


# =======================================================
# 2. HTML ПРОСМОТР, ИЗМЕНЕНИЕ И УДАЛЕНИЕ ОБОРУДОВАНИЯ
# =======================================================
class ProductDetailView(View):
    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Ad, id=pk)

        viewed_products = request.session.get('viewed_products', [])
        pk_str = str(pk)

        if pk_str not in viewed_products:
            product.views_counter += 1
            product.save(update_fields=['views_counter'])

            viewed_products.append(pk_str)
            request.session['viewed_products'] = viewed_products
            request.session.modified = True

        subcategories = Subcategory.objects.all()
        categories = Category.objects.all()

        return render(request, 'product_detail.html', {
            'product': product,
            'subcategories': subcategories,
            'categories': categories
        })

    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('catalog:catalog')

        product = get_object_or_404(Ad, id=pk)
        action = request.POST.get('action')

        if action == 'delete_product':
            product.delete()
            messages.success(request, 'Товар успешно удален.')
            return redirect('catalog:catalog')

        elif action in ['update_product', 'edit_product']:
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            price_raw = request.POST.get('price', '').strip()
            photo = request.FILES.get('photo')
            views_counter = request.POST.get('views_counter')

            # ДОБАВЛЕНО: Чтение обновленного флага "В наличии" из формы
            in_stock = request.POST.get('in_stock') == 'on'

            if title and price_raw and description:
                try:
                    product.price = float(price_raw.replace(',', '.'))
                    product.title = title
                    product.description = description
                    product.in_stock = in_stock  # ДОБАВЛЕНО обновление статуса наличия

                    if views_counter is not None:
                        try:
                            product.views_counter = int(views_counter)
                        except ValueError:
                            pass

                    if photo:
                        product.photo = photo

                    product.save()
                    messages.success(request, 'Данные товара успешно обновлены.')
                except ValueError:
                    messages.error(request, 'Ошибка изменения цены: некорректный формат.')
            else:
                messages.error(request, 'Обязательные поля не могут быть пустыми.')

            return redirect('catalog:product_detail', pk=product.id)

        return redirect('catalog:product_detail', pk=product.id)


# =======================================================
# 3. HTML ПРЕДСТАВЛЕНИЕ ГЛАВНОЙ СТРАНИЦЫ (ВИТРИНА)
# =======================================================
class IndexView(View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()
        latest_products = Ad.objects.all().order_by('-views_counter', '-id')[:16]

        return render(request, 'index.html', {
            'categories': categories,
            'subcategories': subcategories,
            'latest_products': latest_products
        })


def contacts(request):
    categories = Category.objects.all()
    return render(request, 'contacts.html', {'categories': categories})


def info(request):
    categories = Category.objects.all()
    return render(request, 'info.html', {'categories': categories})


# =======================================================
# 4. REST API ПРЕДСТАВЛЕНИЯ (DRF)
# =======================================================
class AdListAPIView(generics.ListAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [AllowAny]


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [AllowAny]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    permission_classes = [AllowAny]


class SendKPRequestView(View):
    """
    Расширенный обработчик формы заказа КП для оборудования 'Под заказ'.
    Мгновенно собирает полные b2b-реквизиты и отправляет лид на рабочую почту.
    """

    def post(self, request, *args, **kwargs):
        client_name = request.POST.get('client_name', '').strip()
        client_phone = request.POST.get('client_phone', '').strip()
        client_email = request.POST.get('client_email', '').strip()
        client_company = request.POST.get('client_company', '').strip()
        client_city = request.POST.get('client_city', '').strip()
        client_comment = request.POST.get('client_comment', '').strip()
        product_title = request.POST.get('product_title', '').strip()

        # Проверка обязательных полей
        if not client_name or not client_phone or not client_email or not product_title:
            return JsonResponse({'status': 'error', 'message': 'Заполните обязательные поля: Имя, Телефон и Email.'},
                                status=400)

        # Формируем расширенное b2b-письмо для менеджера филиала
        subject = f"🔥 ЗАЯВКА: {product_title}"
        email_message = (
            f"Уважаемый менеджер!\n\n"
            f"На сайте Иркутского филиала оставлен расширенный запрос коммерческого предложения.\n\n"
            f"📦 Целевое оборудование: {product_title}\n"
            f"👤 Имя представителя: {client_name}\n"
            f"📞 Контактный телефон: {client_phone}\n"
            f"📧 Электронная почта: {client_email}\n"
            f"🏢 Название компании / ИП: {client_company if client_company else 'Не указана'}\n"
            f"📍 Город доставки: {client_city if client_city else 'Не указан (самовывоз)'}\n\n"
            f"💬 Комментарий к заказу:\n"
            f"{client_comment if client_comment else 'Комментарий отсутствует.'}\n\n"
            f"---------------------------------------------------\n"
            f"Письмо сгенерировано автоматически. Рекомендуемое время b2b-ответа — до 20 минут."
        )

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

        try:
            send_mail(subject, email_message, from_email, ['kond@crv-bakery.ru'], fail_silently=False)
            return JsonResponse({'status': 'success', 'message': 'Запрос успешно отправлен! Менеджер готовит смету.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ошибка отправки почтового сервера SMTP: {e}'},
                                status=500)