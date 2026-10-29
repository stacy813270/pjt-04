from django import forms

from .models import Todo


# [STEP 3-1] 검색 폼 : DB 와 연결되지 않은 일반 Form
# ※ 저장할 데이터가 아니라 "검색 조건" 을 받으므로 ModelForm 이 아닌 forms.Form 사용
# ※ required=False : 아무것도 입력하지 않으면 전체 목록
# ※ [('', '전체')] + Todo.STATUS_CHOICES : 모델의 선택지 앞에 '전체' 를 하나 붙임
class TodoSearchForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', '전체')] + Todo.STATUS_CHOICES,
        required=False,
        label='상태',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    keyword = forms.CharField(
        required=False,
        label='검색어',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': '제목에 포함된 단어'}
        ),
    )


class TodoForm(forms.ModelForm):
    """할 일 생성 폼"""

    # [STEP 3-3] 태그 : 여러 개 고르는 칸으로 바꿔 끼우기
    # ※ 모델의 tags 는 문자열 칸이지만, 폼에서는 같은 이름으로 MultipleChoiceField 를 선언해 바꿔 끼움
    # ※ 체크한 값들은 cleaned_data 에 리스트(['WORK', 'STUDY'])로 들어옴
    # ※ 해제 후 아래 Meta 의 STEP 3-3 도 해제하고 makemigrations · migrate
    tags = forms.MultipleChoiceField(
        choices=Todo.TAG_CHOICES,
        required=False,
        label='태그',
        # CheckboxSelectMultiple : 체크박스로 그리기 (지우면 여러 줄 선택 상자로 그려짐)
        widget=forms.CheckboxSelectMultiple,
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 수정 화면 : DB 의 'WORK,STUDY' 를 리스트로 바꿔 체크된 상태로 보여 줌
        if self.instance.pk:
            self.initial['tags'] = self.instance.get_tag_list()

    class Meta:
        model = Todo
        fields = ['title', 'content']
        # fields += [...] 는 STEP 마다 칸을 하나씩 늘리기 위한 실습용 표기
        # 실제 코드에서는 fields = ['title', 'content', 'status', 'priority', 'tags'] 처럼 한 줄로 씀
        # [STEP 2-1] 상태 칸 추가
        fields += ['status']
        # [STEP 2-2] 우선순위 칸 추가 (models.py 에 priority 를 작성한 뒤 해제)
        fields += ['priority']
        # [STEP 3-3] 태그 칸 추가
        # fields += ['tags']

        # Meta.widgets : 모델 필드 설정(max_length, choices 등)은 그대로 두고 "그리는 모양" 만 바꿈
        # 아직 폼에 없는 필드의 위젯은 무시되므로 미리 적어 두어도 됨
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '할 일을 입력하세요'}
            ),
            'content': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': '상세 내용을 입력하세요',
                    'rows': 4,
                }
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# [STEP 3-2 직접 작성] Form 상속 : 수정 폼 = 생성 폼 + 완료 여부 칸
# [실습 포인트] TodoForm 을 상속하면 위젯 · 태그 칸 · __init__ 을 모두 물려받음
#   - class Meta(TodoForm.Meta) : Meta 도 상속하면 model · widgets 를 다시 쓰지 않아도 됨
#   - 수정 화면에만 필요한 'completed' 칸을 fields 에 더하기만 하면 끝
class UpdateTodoForm(TodoForm):
    """할 일 수정 폼"""

    class Meta(TodoForm.Meta):
        # TODO: TodoForm.Meta.fields 에 'completed' 를 더한 리스트로 바꾸기
        fields = TodoForm.Meta.fields + ['completed']
