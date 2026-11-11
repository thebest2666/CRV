from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):  # Наследуемся от BaseUserAdmin для поддержки паролей и прав
    # Переопределяем отображение списка
    list_display = ('row_number', 'email', 'first_name', 'last_name', 'phone', 'city', 'company', 'is_active')
    list_filter = ('city', 'company', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

    # Так как у нас нет username, убираем дефолтную сортировку BaseUserAdmin
    ordering = ('email',)

    # Настройки полей при редактировании конкретного пользователя в админке
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'phone', 'city', 'company')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    # Настройки полей при создании нового пользователя через админку
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password'),
        }),
    )

    def get_queryset(self, request):
        """
        Переопределяем queryset, чтобы динамически пронумеровать объекты
        на этапе выборки, не ломая потокобезопасность.
        """
        queryset = super().get_queryset(request)
        # Превращаем в список, чтобы сохранить порядок сортировки админки
        return queryset

    def changelist_view(self, request, extra_context=None):
        """
        Используем стандартный механизм Django для сохранения данных
        в рамках ОДНОГО текущего запроса (request), а не в классе.
        """
        response = super().changelist_view(request, extra_context=extra_context)

        # Проверяем, что вернулся именно TemplateResponse (страница со списком)
        if hasattr(response, 'context_data') and 'cl' in response.context_data:
            cl = response.context_data['cl']
            page_num = cl.page_num
            list_per_page = cl.list_per_page

            # Проставляем каждому объекту его глобальный порядковый номер
            for index, obj in enumerate(cl.result_list):
                global_index = index + 1
                if page_num > 1:
                    global_index += (page_num - 1) * list_per_page
                obj._row_number = global_index  # Сохраняем номер внутри самого объекта в памяти

        return response

    def row_number(self, obj):
        """
        Безопасно читаем номер из атрибута объекта.
        """
        return getattr(obj, '_row_number', '')

    row_number.short_description = '№ п/п'
