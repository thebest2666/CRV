from django.contrib import admin
from django.utils.safestring import mark_safe
from catalog.models import Ad, Category, Subcategory


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    # Поля, которые будут видны в таблице со списком всех товаров
    list_display = ('id', 'get_html_photo', 'title', 'price', 'formatted_price', 'in_stock', 'subcategory',
                    'views_counter', 'created_at')
    # Поля, кликнув на которые можно перейти к редактированию товара
    list_display_links = ('id', 'title')
    # Фильтры в правой панели админки
    list_filter = ('in_stock', 'subcategory__category', 'subcategory', 'created_at')
    # Поля, по которым работает строка поиска
    search_fields = ('title', 'description')
    # Возможность быстро переключать галочку "В наличии" прямо из общей таблицы
    list_editable = ('in_stock', 'price')
    # Защищаем счетчик просмотров и дату от ручного изменения
    readonly_fields = ('views_counter', 'created_at', 'get_html_photo')
    # Порядок сортировки по умолчанию
    ordering = ('-created_at',)

    def get_html_photo(self, obj):
        """Динамически выводит миниатюру изображения товара прямо в админку"""
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="50" style="border-radius:4px;" />')
        return "Нет фото"

    get_html_photo.short_description = 'Миниатюра'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category')
    list_filter = ('category',)
    search_fields = ('title',)
