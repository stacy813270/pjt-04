from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, UserChangeForm, UserCreationForm,
)

User = get_user_model()


class StyledFormMixin:
    """Keep Django's built-in validation and add Bootstrap widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
            if isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs['autocomplete'] = (
                    'current-password' if name in ('password', 'old_password') else 'new-password'
                )
        if 'username' in self.fields:
            self.fields['username'].widget.attrs['autocomplete'] = 'username'


class CustomAuthenticationForm(StyledFormMixin, AuthenticationForm):
    pass


class ReadingProfileFormMixin(StyledFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['interested_genres'] = self.instance.get_genre_list()
        self.fields['interested_genres'].help_text = '관심 있는 장르를 여러 개 선택할 수 있어요.'

    def clean_interested_genres(self):
        # MultipleChoiceField validates the codes before they are serialized.
        return ','.join(self.cleaned_data['interested_genres'])


PROFILE_FIELDS = [
    'email', 'last_name', 'first_name', 'gender', 'age',
    'weekly_reading_hours', 'annual_reading_count', 'interested_genres', 'interested_categories',
]
PROFILE_LABELS = {
    'username': '아이디', 'email': '이메일', 'last_name': '성', 'first_name': '이름',
    'gender': '성별', 'age': '나이', 'weekly_reading_hours': '주간 평균 독서 시간 (시간)',
    'annual_reading_count': '연간 독서량 (권)', 'interested_genres': '관심 장르',
    'interested_categories': '관심 카테고리',
}


class CustomUserCreationForm(ReadingProfileFormMixin, UserCreationForm):
    interested_genres = forms.MultipleChoiceField(
        choices=User.GENRE_CHOICES, required=False, label='관심 장르',
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', *PROFILE_FIELDS]
        labels = PROFILE_LABELS
        widgets = {'interested_categories': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = '비밀번호'
        self.fields['password2'].label = '비밀번호 확인'


class CustomUserChangeForm(ReadingProfileFormMixin, UserChangeForm):
    password = None
    interested_genres = forms.MultipleChoiceField(
        choices=User.GENRE_CHOICES, required=False, label='관심 장르',
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = PROFILE_FIELDS
        labels = PROFILE_LABELS
        widgets = {'interested_categories': forms.CheckboxSelectMultiple}


class InterestCategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['interested_categories']
        widgets = {'interested_categories': forms.CheckboxSelectMultiple}
        help_texts = {'interested_categories': '관심 있는 카테고리를 여러 개 선택할 수 있어요.'}


class CustomPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    pass
