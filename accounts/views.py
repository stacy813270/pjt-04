from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import (
    CustomAuthenticationForm, CustomPasswordChangeForm,
    CustomUserChangeForm, CustomUserCreationForm,
    InterestCategoryForm,
)


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.user.is_authenticated:
        return redirect('books:index')
    next_url = request.POST.get('next') or request.GET.get('next', '')
    form = CustomAuthenticationForm(request, data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        messages.success(request, '로그인되었습니다. 반가워요!')
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect('books:index')
    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


@require_POST
@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, '로그아웃되었습니다.')
    return redirect('books:index')


@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.user.is_authenticated:
        return redirect('books:index')
    form = CustomUserCreationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, '가입을 환영합니다. 함께 읽는 즐거움을 시작해 보세요.')
        return redirect('books:index')
    return render(request, 'accounts/signup.html', {'form': form})


@require_http_methods(['GET', 'POST'])
@login_required
def update(request):
    form = CustomUserChangeForm(
        request.POST if request.method == 'POST' else None, instance=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '회원정보를 수정했습니다.')
        return redirect('books:index')
    return render(request, 'accounts/update.html', {'form': form})


@require_POST
@login_required
def delete(request):
    request.user.delete()
    auth_logout(request)
    messages.success(request, '회원탈퇴가 완료되었습니다.')
    return redirect('books:index')


@require_http_methods(['GET', 'POST'])
@login_required
def change_password(request):
    form = CustomPasswordChangeForm(
        request.user, data=request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, '비밀번호를 변경했습니다.')
        return redirect('books:index')
    return render(request, 'accounts/change_password.html', {'form': form})


@require_GET
@login_required
def profile(request, username):
    user_profile = get_object_or_404(
        get_user_model().objects.prefetch_related('interested_categories'), username=username,
    )
    context = {'user_profile': user_profile}
    if user_profile.pk == request.user.pk:
        context['interest_form'] = InterestCategoryForm(instance=request.user)
    return render(request, 'accounts/profile.html', context)


@require_POST
@login_required
def update_interested_categories(request):
    form = InterestCategoryForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, '관심 카테고리를 저장했습니다.')
        return redirect('accounts:profile', username=request.user.username)
    return render(request, 'accounts/profile.html', {
        'user_profile': request.user, 'interest_form': form,
    })
