from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse


def normalize_category_name(name):
    return ' '.join(name.split())


class Category(models.Model):
    name = models.CharField('카테고리 이름', max_length=50, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리'
        constraints = [
            models.UniqueConstraint(Lower('name'), name='category_name_case_insensitive'),
            models.CheckConstraint(condition=~models.Q(name=''), name='category_name_not_empty'),
        ]

    def save(self, *args, **kwargs):
        self.name = normalize_category_name(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('books:category', kwargs={'category_pk': self.pk})


def get_default_category_id():
    return Category.objects.get_or_create(name='기타')[0].pk


class Book(models.Model):
    title = models.CharField('도서 제목', max_length=200)
    description = models.TextField('설명')
    customer_review_rank = models.DecimalField(
        '회원 리뷰 평점', max_digits=3, decimal_places=1,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('10'))],
        help_text='0점부터 10점까지, 소수 첫째 자리까지 입력할 수 있어요.',
    )
    author = models.CharField('저자', max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='books',
        verbose_name='카테고리', default=get_default_category_id,
    )
    liked_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='liked_books', blank=True,
        verbose_name='좋아요한 사용자',
    )

    class Meta:
        ordering = ['-pk']
        verbose_name = '도서'
        verbose_name_plural = '도서'
        constraints = [models.CheckConstraint(
            condition=models.Q(customer_review_rank__gte=0, customer_review_rank__lte=10),
            name='book_review_rank_between_0_and_10',
        )]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('books:detail', kwargs={'pk': self.pk})
