from django.contrib import admin
from .models import Book, Category


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'customer_review_rank']
    list_filter = ['category']
    list_select_related = ['category']
    search_fields = ['title', 'author']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
