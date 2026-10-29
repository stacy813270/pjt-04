import math
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from .forms import BookForm
from .models import Book, Category
from .recommendations import DISCLAIMER, RecommendationError, book_key, recommend_books


def books_with_like_state(user):
    """Annotate personal like state in SQL without one query per card."""
    books = Book.objects.select_related('category')
    if user.is_authenticated:
        likes = Book.liked_users.through.objects.filter(
            book_id=OuterRef('pk'), user_id=user.pk,
        )
        return books.annotate(is_liked=Exists(likes))
    return books.annotate(is_liked=Value(False, output_field=BooleanField()))


@require_GET
def index(request, category_pk=None):
    liked_only = request.GET.get('liked') == '1'
    if liked_only and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    books = books_with_like_state(request.user)
    if liked_only:
        books = books.filter(liked_users=request.user)
    selected_category = None
    if category_pk is not None:
        selected_category = get_object_or_404(Category, pk=category_pk)
        books = books.filter(category=selected_category)
    keyword = request.GET.get('q', '').strip()
    total_count = books.count()
    if keyword:
        books = books.filter(Q(title__icontains=keyword) | Q(author__icontains=keyword))
    return render(request, 'books/index.html', {
        'books': books, 'keyword': keyword, 'total_count': total_count,
        'liked_only': liked_only,
        'selected_category': selected_category,
        'list_url': selected_category.get_absolute_url() if selected_category else reverse('books:index'),
        'has_liked_books': request.user.liked_books.exists() if liked_only else False,
        'recommendation_throttle_seconds': settings.BOOK_RECOMMENDATION_THROTTLE_SECONDS,
        'recommendation_disclaimer': DISCLAIMER,
    })


@require_http_methods(['GET', 'POST'])
@login_required
def create(request):
    form = BookForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        book = form.save()
        messages.success(request, '새로운 도서를 등록했습니다.')
        return redirect(book)
    return render(request, 'books/create.html', {'form': form})


@require_GET
def detail(request, pk):
    book = get_object_or_404(books_with_like_state(request.user), pk=pk)
    return render(request, 'books/detail.html', {'book': book})


@require_http_methods(['GET', 'POST'])
@login_required
def update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST if request.method == 'POST' else None, instance=book)
    if request.method == 'POST' and form.is_valid():
        book = form.save()
        messages.success(request, '도서 정보를 수정했습니다.')
        return redirect(book)
    return render(request, 'books/update.html', {'form': form, 'book': book})


@require_POST
@login_required
def delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    messages.success(request, '도서를 삭제했습니다.')
    return redirect('books:index')


@require_POST
def like(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 후 좋아요를 사용할 수 있습니다.'}, status=401)
    book = get_object_or_404(Book, pk=pk)
    liked = request.POST.get('liked')
    if liked not in ('true', 'false'):
        return JsonResponse({'error': '좋아요 상태는 true 또는 false여야 합니다.'}, status=400)
    # Set the requested state so retries never toggle a saved like accidentally.
    if liked == 'true':
        book.liked_users.add(request.user)
    else:
        book.liked_users.remove(request.user)
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'book_id': book.pk, 'liked': liked == 'true'})
    return redirect(book)


def _recommendation_rate_limit(seconds, message):
    response = JsonResponse({'error': message, 'retry_after': seconds}, status=429)
    response['Retry-After'] = str(seconds)
    return response


@require_POST
@never_cache
def recommendations(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 후 도서 추천을 받을 수 있습니다.'}, status=401)
    liked_books = [{
        'title': book.title, 'author': book.author, 'category': book.category.name,
        'description': book.description,
    } for book in request.user.liked_books.select_related('category')]
    if not liked_books:
        return JsonResponse({'error': '좋아요한 책을 먼저 추가해 주세요.'}, status=400)
    user_key = f'book-recommendations:{request.user.pk}'
    busy_key = f'{user_key}:busy'
    cooldown_key = f'{user_key}:cooldown'
    interval = settings.BOOK_RECOMMENDATION_THROTTLE_SECONDS
    now = time.time()
    deadline = cache.get(cooldown_key, 0)
    if deadline > now:
        return _recommendation_rate_limit(math.ceil(deadline - now), '잠시 후 다시 추천받아 주세요.')
    if not cache.add(busy_key, True, timeout=settings.BOOK_RECOMMENDATION_TIMEOUT_SECONDS + 30):
        return _recommendation_rate_limit(5, '이전 추천을 생성 중입니다. 잠시 기다려 주세요.')
    try:
        if not cache.add(cooldown_key, now + interval, timeout=interval):
            return _recommendation_rate_limit(interval, '잠시 후 다시 추천받아 주세요.')
        items = recommend_books(liked_books)
        existing = {book_key(book.title, book.author): book.get_absolute_url()
                    for book in Book.objects.only('pk', 'title', 'author')}
        for item in items:
            item['detail_url'] = existing.get(book_key(item['title'], item['author']))
        return JsonResponse({
            'recommendations': items, 'liked_count': len(liked_books),
            'disclaimer': DISCLAIMER, 'retry_after': interval,
        })
    except RecommendationError as exc:
        return JsonResponse({'error': str(exc)}, status=exc.status)
    finally:
        cache.delete(busy_key)
