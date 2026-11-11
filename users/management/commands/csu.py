from django.core.management import BaseCommand
from users.models import User


class Command(BaseCommand):
    """
    Кастомная команда для автоматического создания трех пользователей сразу.
    Безопасна при повторном запуске.
    """

    def handle(self, *args, **options):
        # Список из 3 пользователей с их персональными данными и правами
        users_to_create = [
            {
                'email': 'kond@crv-bakery.ru',
                'password': 'Cfytr12546pro',
                'first_name': 'Александр',
                'last_name': 'Анциферов',
                'company': 'CRV-bakery',
                'phone': '+79952551696',
                'city': 'Иркутск',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'aleksa@crv-bakery.ru',
                'password': 'ManagerPassword2026',
                'first_name': 'Александра',
                'last_name': 'Ткаченко',
                'company': 'CRV-bakery',
                'phone': '+79950474995',
                'city': 'Иркутск',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'hleb@crv-bakery.ru',
                'password': 'BuyerPassword2026',
                'first_name': 'Елена',
                'last_name': 'Полянская',
                'company': 'CRV-bakery',
                'phone': '+79950486192',
                'city': 'Иркутск',
                'is_staff': True,
                'is_superuser': True,
            }
        ]

        for user_data in users_to_create:
            email = user_data['email']
            password = user_data.pop('password')  # Извлекаем пароль для безопасного хэширования

            # НАСТРОЕНО: Вместо пропуска обновляем существующего снабженца или создаем нового
            user, created = User.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'company': user_data['company'],
                    'phone': user_data['phone'],
                    'city': user_data['city'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                    'is_active': True
                }
            )

            # Безопасно обновляем пароль (хэшируем его в СУБД)
            user.set_password(password)
            user.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f'🚀 Контрагент {email} успешно создан с нуля!'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'🔄 Параметры пользователя {email} в БД успешно обновлены из файла csu.py!'))
