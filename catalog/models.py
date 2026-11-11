from django.db import models


class Category(models.Model):
    """
    Информация о категории товара
    """
    title = models.CharField(max_length=100, unique=True, verbose_name='Категория товара', help_text='Введите категорию товара')

    class Meta:
        verbose_name = 'Категория товара'
        verbose_name_plural = 'Категории товара'

    def __str__(self):
        return self.title


class Subcategory(models.Model):
    """
    Информация о подкатегории товара
    """
    title = models.CharField(
        unique=True,
        max_length=100,
        verbose_name='Подкатегория товара',
        help_text='Введите подкатегорию товара'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='subcategories',
        verbose_name='Главная категория',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Подкатегория товара'
        verbose_name_plural = 'Подкатегории товара'

    def __str__(self):
        if self.category:
            return f"{self.category.title} -> {self.title}"
        return f"Без категории -> {self.title}"


class Ad(models.Model):  # Исправлено Add -> Ad (Объявление)
    """
    Информация об объявлении
    """
    title = models.CharField(
        max_length=100,
        verbose_name='Название товара',
        help_text='Напишите название товара'
    )
    in_stock = models.BooleanField(
        default=True,
        verbose_name='В наличии',
        help_text='Снимите галочку, если товар доступен только "Под заказ"'
    )
    description = models.TextField(
        verbose_name='Описание товара',
        help_text='Напишите описание товара'
    )
    photo = models.ImageField(
        upload_to='catalog/photo',
        blank=True,
        null=True,
        verbose_name='Изображение товара',
        help_text='Загрузите изображение товара'
    )
    views_counter = models.PositiveIntegerField(
        verbose_name='Количество просмотров',
        default=0
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена',
        help_text='Установите цену'
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        verbose_name='Подкатегория товара',
        help_text='Выберите подкатегорию товара',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']

    @property
    def formatted_price(self):
        # Если флаг "В наличии" снят (False), цену скрываем
        if not self.in_stock:
            return "Цена по запросу"

        if self.price is not None:
            return f"{self.price:,.0f}".replace(",", " ")
        return "0"

    def __str__(self):
        return self.title