from django.urls import path, reverse_lazy, reverse
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_protect

# Импортируем представления из views.py
from .views import (
    CustomTokenObtainPairView,
    UserCreateAPIView,
    CustomLogoutView,
    UserListView,
    UserProfileView,
    CustomPasswordResetConfirmView
)

app_name = 'users'


# Форма отправки ссылок восстановления через SMTP
class CustomPasswordResetForm(PasswordResetForm):
    def save(self, domain_override=None, subject_template_name=None,
             email_template_name=None, use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None, extra_email_context=None):
        email = self.cleaned_data["email"]
        active_users = self.get_users(email)

        # Определяем адрес отправителя по умолчанию
        from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

        for user in active_users:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            protocol = 'https' if use_https else 'http'

            # ИСПРАВЛЕНО: Избавление от хардкода ссылки через динамический reverse
            path_confirm = reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            reset_url = f"{protocol}://{domain}{path_confirm}"

            subject = f"Восстановление пароля на сайте {site_name}"
            email_message = (
                f"Вы получили это письмо, потому что запросили сброс пароля для учетной записи на сайте {site_name}.\n\n"
                f"Пожалуйста, перейдите по ссылке ниже, чтобы придумать новый пароль:\n"
                f"{reset_url}\n\n"
                f"Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо."
            )

            send_mail(subject, email_message, from_email, [user.email], fail_silently=False)


urlpatterns = [
    # Вход защищен от вмешательства глобального JSON-рендерера DRF
    path('login/', csrf_protect(CustomTokenObtainPairView.as_view()), name='login'),

    path('register/', UserCreateAPIView.as_view(), name='register'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Восстановление пароля
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset_form.html',
             form_class=CustomPasswordResetForm,
             success_url=reverse_lazy('users:password_reset_done')
         ),
         name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),

    path('profile/', UserProfileView.as_view(), name='profile'),
    path('user-list/', UserListView.as_view(), name='user_list'),
]
