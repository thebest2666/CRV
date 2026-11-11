from rest_framework import serializers
from .models import Category, Subcategory, Ad


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title']


class SubcategorySerializer(serializers.ModelSerializer):
    # Показывает текстовое название категории в ответе, а не просто ID
    category_title = serializers.CharField(source='category.title', read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'title', 'category', 'category_title']


class AdSerializer(serializers.ModelSerializer):
    # Показывает детальную информацию о подкатегории при выводе
    subcategory_detail = SubcategorySerializer(source='subcategory', read_only=True)
    formatted_price = serializers.ReadOnlyField()

    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'description', 'photo',
            'in_stock', 'views_counter', 'price', 'formatted_price',
            'subcategory', 'subcategory_detail', 'created_at'
        ]
        # Счетчик просмотров и даты защищены от изменения извне
        read_only_fields = ['views_counter', 'created_at', 'formatted_price']
