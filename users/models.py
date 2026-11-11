from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер для управления пользователями без поля username.
    Устраняет ошибки дублирования keyword argument 'email'.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Электронная почта обязательна для заполнения')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель b2b-пользователя (контрагента).
    Поле username полностью удалено. Авторизация происходит по email.
    """
    username = None  # Исключаем стандартное поле username

    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта',
        help_text='Укажите электронную почту'
    )
    first_name = models.CharField(
        max_length=50,
        verbose_name='Имя',
        help_text='Введите имя'
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='Фамилия',
        help_text='Введите фамилию'
    )
    phone = PhoneNumberField(
        verbose_name='Телефон',
        help_text='Укажите телефон'
    )
    city = models.CharField(
        max_length=50,
        verbose_name='Город',
        help_text='Укажите город',
        blank=True,
        null=True
    )
    company = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Название компании',
        help_text='Укажите название Вашей компании'
    )

    # Подключаем кастомный менеджер (Критически важно!)
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Поля, запрашиваемые приcreatesuperuser в консоли

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
