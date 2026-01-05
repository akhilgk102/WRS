from adminapp.models import Category

def categories_processor(request):
    """Make categories available in all templates"""
    return {
        'all_categories': Category.objects.all()
    }