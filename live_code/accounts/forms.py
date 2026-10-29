from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)


class CustomAuthenticationForm(AuthenticationForm):
    """로그인 폼"""

    # [STEP 4-1] 위젯 꾸미기 : 필드를 다시 선언하는 방식
    # ※ 로그인 폼은 ModelForm 이 아니라서 Meta.widgets 를 쓸 수 없음 => 같은 이름의 필드를 다시 선언
    # username = forms.CharField(
    #     label='사용자 이름',
    #     widget=forms.TextInput(
    #         attrs={'class': 'form-control', 'placeholder': '사용자 이름'}
    #     ),
    # )
    # password = forms.CharField(
    #     label='비밀번호',
    #     widget=forms.PasswordInput(
    #         attrs={'class': 'form-control', 'placeholder': '비밀번호'}
    #     ),
    # )


class CustomUserCreationForm(UserCreationForm):
    """회원가입 폼"""

    # [STEP 4-1] Meta.model 을 우리 User 로 교체
    # ※ 부모(UserCreationForm)의 Meta.model 은 기본 User 로 고정되어 있음
    # ※ 이 Meta 를 해제하기 전에 회원가입을 해 보면 "Manager isn't available" 에러 발생
    # ※ username 은 모델 필드이므로 052 에서 배운 Meta.widgets 로 위젯만 바꿈
    # ※ password1 · password2 는 모델 필드가 아니므로(폼에서 만든 칸) 필드를 다시 선언
    # class Meta(UserCreationForm.Meta):
    #     model = get_user_model()
    #     fields = ['username']
    #     widgets = {
    #         'username': forms.TextInput(
    #             attrs={'class': 'form-control', 'placeholder': '사용자 이름'}
    #         ),
    #     }
    #
    # password1 = forms.CharField(
    #     label='비밀번호',
    #     widget=forms.PasswordInput(
    #         attrs={'class': 'form-control', 'placeholder': '비밀번호'}
    #     ),
    # )
    # password2 = forms.CharField(
    #     label='비밀번호 확인',
    #     widget=forms.PasswordInput(
    #         attrs={'class': 'form-control', 'placeholder': '비밀번호 확인'}
    #     ),
    # )


class CustomUserChangeForm(UserChangeForm):
    """회원정보 수정 폼"""

    # 비밀번호는 비밀번호 변경 화면에서만 바꾸도록 수정 폼에서 칸을 없앰
    password = None

    # 회원가입 폼과 같은 방식 : 부모 Meta 는 물려받고 model · fields 만 바꿈
    class Meta(UserChangeForm.Meta):
        model = get_user_model()
        # fields 를 지정하지 않으면 is_superuser · is_staff 같은 권한 칸까지 사용자에게 열림
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': '이메일'}
            ),
            'first_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '이름'}
            ),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '성'}
            ),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """비밀번호 변경 폼"""

    # [STEP 4-1] 위젯 꾸미기
    # old_password = forms.CharField(
    #     label='현재 비밀번호',
    #     widget=forms.PasswordInput(
    #         attrs={'class': 'form-control', 'placeholder': '현재 비밀번호'}
    #     ),
    # )
    # new_password1 = forms.CharField(
    #     label='새 비밀번호',
    #     widget=forms.PasswordInput(
    #         attrs={'class': 'form-control', 'placeholder': '새 비밀번호'}
    #     ),
    # )
    # new_password2 = forms.CharField(
    #     label='새 비밀번호 확인',
    #     widget=forms.PasswordInput(
    #         attrs={'class': 'form-control', 'placeholder': '새 비밀번호 확인'}
    #     ),
    # )
