from .models import Category

def categories_processor(request):
    """
    Глобально подмешивает b2b-категории во все контексты сайта.
    Имя функции строго синхронизировано со значением в settings.py.
    """
    return {
        # Передаем переменную, которую мы настроили для цикла подвала
        'global_b2b_categories': Category.objects.all()
    }