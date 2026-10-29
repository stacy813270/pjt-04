from urllib.parse import urlencode
from django.db.models import Count
from .models import Category


def category_sidebar(request):
    categories = list(Category.objects.annotate(book_count=Count('books')))
    params = {}
    match = request.resolver_match
    if match and match.namespace == 'books' and match.url_name in ('index', 'category'):
        if request.GET.get('liked') == '1':
            params['liked'] = '1'
        if request.GET.get('q', '').strip():
            params['q'] = request.GET['q'].strip()
    return {
        'sidebar_categories': categories,
        'category_book_total': sum(category.book_count for category in categories),
        'category_filter_query': f'?{urlencode(params)}' if params else '',
    }
