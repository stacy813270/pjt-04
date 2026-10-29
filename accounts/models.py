from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class User(AbstractUser):
    class Gender(models.TextChoices):
        FEMALE = 'F', '여성'
        MALE = 'M', '남성'
        OTHER = 'O', '기타'
        PRIVATE = 'N', '공개 안 함'

    GENRE_CHOICES = [
        ('NOVEL', '소설'), ('POETRY', '시'), ('ESSAY', '에세이'),
        ('HUMANITIES', '인문'), ('SCIENCE', '과학'), ('HISTORY', '역사'),
        ('ECONOMY', '경제·경영'), ('SELF_HELP', '자기계발'), ('ART', '예술'),
    ]

    gender = models.CharField('성별', max_length=1, choices=Gender.choices, blank=True)
    age = models.PositiveIntegerField('나이', blank=True, null=True, validators=[MinValueValidator(1)])
    weekly_reading_hours = models.PositiveIntegerField(
        '주간 평균 독서 시간', blank=True, null=True, validators=[MinValueValidator(1)],
    )
    annual_reading_count = models.PositiveIntegerField(
        '연간 독서량', blank=True, null=True, validators=[MinValueValidator(1)],
    )
    interested_genres = models.CharField('관심 장르', max_length=600, blank=True)
    interested_categories = models.ManyToManyField(
        'books.Category', related_name='interested_users', blank=True,
        verbose_name='관심 카테고리',
    )

    def get_genre_list(self):
        return self.interested_genres.split(',') if self.interested_genres else []

    def get_interested_genres_display(self):
        labels = dict(self.GENRE_CHOICES)
        return ', '.join(labels.get(genre, genre) for genre in self.get_genre_list())
