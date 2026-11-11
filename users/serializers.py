from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from users.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор авторизации, который проверяет пароль
    по полю email и генерирует стандартные JWT-токены.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Явно указываем SimpleJWT, что на входе будет email вместо username
        self.fields['email'] = serializers.EmailField()
        if 'username' in self.fields:
            del self.fields['username']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Так как USERNAME_FIELD = 'email', передаем в authenticate параметр email
            user = authenticate(email=email, password=password)

            if not user:
                raise AuthenticationFailed('Неверный логин или пароль')

            if not user.is_active:
                raise AuthenticationFailed('Пользователь деактивирован')

            # Генерируем стандартную пару JWT-токенов
            refresh = RefreshToken.for_user(user)

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

        raise serializers.ValidationError('Необходимо указать email и пароль')


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.
    Поле username полностью исключено.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'phone', 'city', 'company']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def validate_email(self, value):
        """Проверка уникальности email на уровне сериализатора"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('Пользователь с таким Email уже зарегистрирован.')
        return value.lower()
