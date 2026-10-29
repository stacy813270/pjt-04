from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from todos.models import Todo

from .forms import (
    CustomAuthenticationForm,
    CustomPasswordChangeForm,
    CustomUserChangeForm,
    CustomUserCreationForm,
)

# [STEP 4-2] next 주소가 우리 사이트 주소인지 확인하는 함수
# from django.utils.http import url_has_allowed_host_and_scheme


def login(request):
    if request.user.is_authenticated:
        return redirect('todos:index')

    if request.method == 'POST':
        # AuthenticationForm 은 첫 번째 인자로 request 를 받음 (다른 폼과 순서가 다름)
        form = CustomAuthenticationForm(request, request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            # [STEP 4-2] 로그인 후 원래 가려던 페이지로 돌아가기
            # ※ @login_required 가 로그인 화면으로 보낼 때 /accounts/login/?next=/todos/3/ 처럼 원래 주소를 붙여 줌
            # ※ 외부 사이트로 보내는 공격을 막기 위해 우리 사이트 주소일 때만 이동
            # next_url = request.GET.get('next')
            # if next_url and url_has_allowed_host_and_scheme(
            #     next_url, allowed_hosts={request.get_host()}
            # ):
            #     return redirect(next_url)
            return redirect('todos:index')
    else:
        form = CustomAuthenticationForm()
    context = {'form': form}
    return render(request, 'accounts/login.html', context)


@require_POST
def logout(request):
    # 링크(GET)로 로그아웃되지 않도록 POST 요청만 허용
    auth_logout(request)
    return redirect('todos:index')


def signup(request):
    if request.user.is_authenticated:
        return redirect('todos:index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # 가입하자마자 로그인 상태로
            return redirect('todos:index')
    else:
        form = CustomUserCreationForm()
    context = {'form': form}
    return render(request, 'accounts/signup.html', context)


@login_required
def update(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '회원정보를 수정했습니다.')
            return redirect('accounts:profile', request.user.username)
    else:
        form = CustomUserChangeForm(instance=request.user)
    context = {'form': form}
    return render(request, 'accounts/update.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        # PasswordChangeForm 은 첫 번째 인자로 "누구의" 비밀번호인지(user) 를 받음
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # [STEP 4-3 직접 작성] 비밀번호를 바꿔도 로그인 상태 유지하기
            # [실습 포인트] 먼저 이 상태로 비밀번호를 바꿔 보고, 변경 직후 로그아웃되는 것을 확인
            #   - 로그인 세션에는 비밀번호로 만든 값이 들어 있어, 비밀번호가 바뀌면 기존 세션이 무효가 됨
            #   - update_session_auth_hash(request, user) 로 세션을 새 비밀번호 기준으로 갱신
            # TODO: 세션을 갱신하는 한 줄 작성
            messages.success(request, '비밀번호를 변경했습니다.')
            return redirect('accounts:profile', request.user.username)
    else:
        form = CustomPasswordChangeForm(request.user)
    context = {'form': form}
    return render(request, 'accounts/change_password.html', context)


@login_required
@require_POST
def delete(request):
    # 순서 주의 : 회원을 먼저 지운 뒤 세션을 정리(로그아웃)
    request.user.delete()
    auth_logout(request)
    return redirect('todos:index')


@login_required
def profile(request, username):
    # get_user_model() : settings.AUTH_USER_MODEL 에 지정된 User 를 돌려줌 (User 를 직접 import 하지 않음)
    User = get_user_model()
    user = User.objects.get(username=username)
    # 할 일과 작성자는 아직 연결되어 있지 않으므로(모델 관계 학습 전) 모든 할 일을 표시
    todos = Todo.objects.all()
    # 템플릿의 {{ user }} 는 이미 로그인한 사람이므로 'user_profile' 로 넘김
    context = {'user_profile': user, 'todos': todos}
    return render(request, 'accounts/profile.html', context)
