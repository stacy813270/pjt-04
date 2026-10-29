from django import forms
from django.db import transaction
from .models import Book, Category, normalize_category_name


class BookForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, label='카테고리',
        empty_label='카테고리를 선택해 주세요',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    new_category = forms.CharField(
        label='새 카테고리 추가', required=False, max_length=50,
        help_text='목록에 없으면 새 이름을 입력하세요. 입력한 새 이름이 위의 선택보다 우선합니다.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '예: 여행, 컴퓨터·IT'}),
    )

    class Meta:
        model = Book
        fields = ['title', 'description', 'customer_review_rank', 'author', 'category', 'new_category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '어떤 책을 소개하고 싶으신가요?'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6, 'placeholder': '책의 줄거리와 소개를 들려주세요.',
            }),
            'customer_review_rank': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'max': 10, 'step': '0.1', 'placeholder': '예: 9.5',
            }),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '저자 이름'}),
        }

    def clean_new_category(self):
        return normalize_category_name(self.cleaned_data['new_category'])

    def clean(self):
        data = super().clean()
        if not data.get('category') and not data.get('new_category'):
            self.add_error('category', '카테고리를 선택하거나 새 카테고리 이름을 입력해 주세요.')
        return data

    @transaction.atomic
    def save(self, commit=True):
        book = super().save(commit=False)
        new_name = self.cleaned_data.get('new_category')
        if new_name:
            book.category, _ = Category.objects.get_or_create(
                name__iexact=new_name, defaults={'name': new_name},
            )
        if commit:
            book.save()
            self.save_m2m()
        return book
