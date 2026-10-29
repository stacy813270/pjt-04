from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import TodoForm, UpdateTodoForm
from .models import Todo

# [STEP 3-1] 검색 폼 가져오기
from .forms import TodoSearchForm


# 로그인한 사용자만 접근 (정규 수업 내용) : 로그인하지 않았다면 로그인 화면으로 이동
@login_required
def index(request):
    todos = Todo.objects.all()

    # [STEP 3-1] 검색 조건으로 목록 거르기
    # ※ GET 으로 받은 검색 조건을 폼에 넣고, 검증을 통과한 값(cleaned_data)으로만 거름
    # ※ 주소 예 : /todos/?status=DOING&keyword=회의
    form = TodoSearchForm(request.GET)
    if form.is_valid():
        status = form.cleaned_data['status']
        keyword = form.cleaned_data['keyword']
        if status:
            todos = todos.filter(status=status)
        if keyword:
            todos = todos.filter(title__contains=keyword)

    # [STEP 3-1] 검색 폼도 템플릿으로 보내기
    # ※ 아래 한 줄을 해제한 뒤, 바로 아래의 기존 context 한 줄은 지웁니다
    context = {'todos': todos, 'form': form}
    # context = {'todos': todos}

    return render(request, 'todos/index.html', context)


@login_required
def create(request):
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            # [STEP 3-4 직접 작성] 태그 리스트를 콤마 문자열로 바꿔 저장
            # [실습 포인트] STEP 3-3 을 해제한 뒤 태그를 골라 저장해 보고, 상세 화면 · 관리자 페이지에서 저장된 값을 확인
            #   - 서버 로그의 cleaned_data 에서 tags 가 리스트로 들어오는 것을 확인
            #   - form.save(commit=False) : DB 저장을 미루고 객체(todo)만 받기
            #   - ','.join(리스트) : ['WORK', 'STUDY'] -> 'WORK,STUDY'
            #   - 값을 바꾼 뒤 todo.save() 로 직접 저장
            # TODO: 아래 form.save() 한 줄을 위 순서대로 바꾸기
            print('cleaned_data :', form.cleaned_data)
            todo = form.save(commit=False)
            tags = ','.join(form.cleaned_data['tags'])
            todo.tags = tags
            todo.save()
            # [STEP 3-5] 저장 성공 알림
            # ※ 다음 화면에서 딱 한 번 보여 주고 사라지는 메시지 (base.html 에서 출력)
            messages.success(request, f"'{todo.title}' 할 일을 추가했습니다.")
            return redirect('todos:index')
    else:
        form = TodoForm()
    context = {'form': form}
    return render(request, 'todos/create.html', context)


@login_required
def detail(request, pk):
    todo = Todo.objects.get(pk=pk)
    context = {'todo': todo}
    return render(request, 'todos/detail.html', context)


@login_required
def update(request, pk):
    todo = Todo.objects.get(pk=pk)
    if request.method == 'POST':
        form = UpdateTodoForm(request.POST, instance=todo)
        if form.is_valid():
            # [STEP 3-4] 수정할 때도 같은 방식으로 저장 (생성 뷰를 작성한 뒤 해제)
            # ※ 아래 세 줄을 해제한 뒤, 바로 아래의 form.save() 한 줄은 지웁니다
            todo = form.save(commit=False)
            todo.tags = ','.join(form.cleaned_data['tags'])
            todo.save()
            # [STEP 3-5] 수정 성공 알림
            messages.success(request, '할 일을 수정했습니다.')
            return redirect('todos:detail', pk=pk)
    else:
        form = UpdateTodoForm(instance=todo)
    context = {'form': form, 'todo': todo}
    return render(request, 'todos/update.html', context)


@login_required
@require_POST
def delete(request, pk):
    # require_POST : 주소창 입력(GET)으로는 삭제되지 않도록 POST 요청만 허용
    todo = Todo.objects.get(pk=pk)
    todo.delete()
    return redirect('todos:index')
