import re
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

# ИМПОРТИРОВАНО: Служебный b2b-модуль отправки почты и объект настроек settings
from django.core.mail import send_mail
from django.conf import settings

from users.models import User
from users.serializers import UserSerializer
from catalog.models import Category
@method_decorator(csrf_protect, name='dispatch')
class UserCreateAPIView(View):
    """
    Регистрация нового b2b-аккаунта с автоматическим email-уведомлением в отдел продаж
    """

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')

        categories = Category.objects.all()
        return render(request, 'register.html', {'categories': categories})

    def post(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = UserSerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'register.html', {
                'errors': serializer.errors,
                'categories': categories
            })

        data = serializer.validated_data.copy()
        raw_password = data.pop('password', None)  # Безопасно извлекаем пароль

        if 'username' in data:
            del data['username']

        email = data.get('email')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким Email уже зарегистрирован.')
            return render(request, 'register.html', {'categories': categories})

        # Безопасное создание через менеджер с хэшированием пароля сразу
        user = User.objects.create_user(password=raw_password, **data)
        user.is_active = True
        user.save()

        # =========================================================================
        # НАСТРОЕНО: СБОР БАЗОВЫХ ДАННЫХ ИЗ МОДЕЛИ И SMTP-ОТПРАВКА НА АДМИН-ПОЧТУ
        # =========================================================================
        # Вытаскиваем параметры, которые строго соответствуют полям твоей модели User
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        phone = data.get('phone', '')
        city = data.get('city', 'Не указан')
        company = data.get('company', 'Не указана')

        # Формируем тему и строгое b2b-тело письма для отдела продаж
        mail_subject = f"🚀 Новая регистрация клиента: {company if company else 'Частное лицо'}"

        mail_message = (
            f"На CRV-Bakery Иркутск зарегистрирован новый пользователь.\n\n"
            f"=== ДАННЫЕ ИЗ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ ===\n"
            f"• Имя: {first_name}\n"
            f"• Фамилия: {last_name}\n"
            f"• Телефон связи: {phone}\n"
            f"• Электронная почта: {email}\n"
            f"• Город присутствия: {city}\n"
            f"• Название компании: {company}\n\n"
            f"--------------------------------------------------\n"
            f"Сообщение сгенерировано автоматически почтовым шлюзом Django."
        )

        # Отправляем базовую карточку клиента на твой рабочий Email
        try:
            send_mail(
                subject=mail_subject,
                message=mail_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[getattr(settings, 'B2B_ADMIN_EMAIL', 'irkutsk1@crv-bakery.ru')],
                fail_silently=False,
            )
        except Exception as e:
            # Предотвращаем падение страницы, если возник сбой почтового шлюза Яндекса/Mail.ru
            print(f"⚠️ Ошибка отправки SMTP-уведомления: {e}")

        messages.success(request, 'Регистрация успешна! Войдите в аккаунт.')
        return redirect('users:login')
@method_decorator(csrf_protect, name='dispatch')
class CustomTokenObtainPairView(View):
    """Авторизация по сессиям и JWT-кукам с поддержкой структуры футера"""

    def get(self, request, *args, **kwargs):
        # Открываем форму входа в любых условиях без ложных блокировок
        categories = Category.objects.all()
        return render(request, 'login.html', {'categories': categories})

    def post(self, request, *args, **kwargs):
        categories = Category.objects.all()
        email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = None
        error_message = None

        if email and password:
            user_obj = User.objects.filter(email=email).first()
            if user_obj:
                if user_obj.check_password(password):
                    user = user_obj
                else:
                    error_message = 'Неверный пароль. Повторите попытку.'
            else:
                error_message = 'Пользователь с таким Email не найден.'
        else:
            error_message = 'Заполните все поля формы.'

        if error_message or user is None:
            return render(request, 'login.html', {
                'error': error_message,
                'categories': categories
            })

        # Принудительный вход в сессию Django, чтобы шапка видела статус входа
        login(request, user)

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # НАСТРОЕНО: При удачном входе переносим закупщика строго на главную страницу каталога
        response = redirect('/')
        response.set_cookie(key='access_token', value=access_token, httponly=True, samesite='Lax', path='/')
        response.set_cookie(key='refresh_token', value=str(refresh), httponly=True, samesite='Lax', path='/')

        return response


class CustomLogoutView(View):
    """Безопасный логаут со стиранием кук авторизации"""

    def get(self, request, *args, **kwargs):
        logout(request)
        response = redirect('/')
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response


class UserListView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Панель управления контрагентами ИРК-филиала"""

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('catalog:index')

    def get(self, request, *args, **kwargs):
        all_users = User.objects.all().order_by('-date_joined')
        return render(request, 'users/user_list.html', {'all_users': all_users})


class UserProfileView(LoginRequiredMixin, View):
    """Редактирование профиля закупщика с PhoneNumberField и валидацией email"""

    def get(self, request, *args, **kwargs):
        return render(request, 'users/profile.html', {'user': request.user})

    def post(self, request, *args, **kwargs):
        user = request.user
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        city = request.POST.get('city', '').strip()
        company = request.POST.get('company', '').strip()

        if not email:
            messages.error(request, 'Поле Email не может быть пустым.')
            return redirect('users:profile')

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Этот Email адрес уже используется.')
            return redirect('users:profile')

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(ru|com|net|org|info|biz)$'
        if not re.match(email_regex, email):
            messages.error(request, 'Некорректный формат email. В конце домена не должно быть цифр.')
            return redirect('users:profile')

        phone_regex = r'^\+7[0-9]{10}$'
        if not re.match(phone_regex, phone):
            messages.error(request, 'Некорректный формат телефона. Ожидается +7 и 10 цифр без лишних символов.')
            return redirect('users:profile')

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.city = city if city else None
        user.company = company if company else None

        try:
            user.full_clean()
            user.save()
            messages.success(request, 'Данные Вашего профиля успешно обновлены.')
        except Exception as e:
            messages.error(request, f'Ошибка валидации полей модели: {e}')

        return redirect('users:profile')


@method_decorator(csrf_protect, name='dispatch')
class CustomPasswordResetConfirmView(View):
    """Сброс и установка нового пароля по токену"""

    def get_user(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def get(self, request, uidb64, token, *args, **kwargs):
        user = self.get_user(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            return render(request, 'users/password_reset_confirm.html', {'validlink': True})
        return render(request, 'users/password_reset_confirm.html', {'validlink': False})

    def post(self, request, uidb64, token, *args, **kwargs):
        user = self.get_user(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.POST.get('new_password', '').strip()
            if len(new_password) < 8:
                messages.error(request, 'Пароль должен быть не менее 8 символов.')
                return render(request, 'users/password_reset_confirm.html', {'validlink': True})

            user.set_password(new_password)
            user.save()
            messages.success(request, 'Ваш пароль успешно изменен. Используйте его для входа.')
            return redirect('users:login')

        return render(request, 'users/password_reset_confirm.html', {'validlink': False})
