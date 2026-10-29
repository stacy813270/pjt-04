from django.db import models


class Todo(models.Model):
    title = models.CharField(max_length=100, verbose_name='제목')
    # blank=True : 폼에서 비워 두어도 됨 (문자열 필드는 null=True 대신 빈 문자열로 저장)
    content = models.TextField(blank=True, verbose_name='내용')
    completed = models.BooleanField(default=False, verbose_name='완료 여부')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # [STEP 2-1] 상태 : CharField + choices
    # ※ (DB 에 저장될 값, 화면에 보여 줄 이름) 형태의 튜플 리스트로 선택지를 정의
    # ※ 상수이므로 변수 이름은 대문자로 작성 (PEP 8 관례)
    STATUS_CHOICES = [
        ('TODO', '할 일'),
        ('DOING', '진행 중'),
        ('DONE', '완료'),
    ]
    status = models.CharField(
        max_length=5,
        choices=STATUS_CHOICES,
        default='TODO',
        help_text='현재 작업 상태를 선택해주세요.',
        verbose_name='상태',
    )

    # [STEP 2-2 직접 작성] 우선순위 : PositiveIntegerField + choices
    # [실습 포인트] 바로 위 status 와 같은 모양으로 작성합니다
    #   - DB 에는 숫자 1 · 2 · 3, 화면에는 '낮음' · '보통' · '높음'
    #   - 음수가 될 수 없는 숫자이므로 PositiveIntegerField 사용
    #   - 기본값은 2(보통), help_text 와 verbose_name('우선순위') 도 지정
    # TODO: PRIORITY_CHOICES 리스트 작성
    PRIORITY_CHOICES = [
        (1, '낮음'),
        (2, '보통'),
        (3, '높음'),
    ]
    # TODO: priority 필드 작성
    priority = models.PositiveIntegerField(
        choices=PRIORITY_CHOICES,
        default=2,
        help_text='우선순위를 선택해주세요.',
        verbose_name='우선순위',
    )

    # [STEP 3-3] 태그 : 여러 개를 콤마로 이어 붙인 문자열 하나로 저장
    # ※ 'WORK,STUDY' 처럼 저장 => 모델 관계를 배우기 전에 쓸 수 있는 방법 (한계는 수업 마지막에 확인)
    # ※ choices 를 모델 필드에 걸지 않는 이유 : choices 는 값 하나만 고르는 칸이라 'WORK,STUDY' 를 허용하지 않음
    TAG_CHOICES = [
        ('WORK', '업무'),
        ('STUDY', '공부'),
        ('LIFE', '생활'),
    ]
    tags = models.CharField(
        max_length=100,
        blank=True,
        help_text='콤마로 구분된 태그 코드',
        verbose_name='태그',
    )
    
    def get_tag_list(self):
        """'WORK,STUDY' -> ['WORK', 'STUDY']"""
        return self.tags.split(',') if self.tags else []
    
    def get_tags_display(self):
        """'WORK,STUDY' -> '업무, 공부' (choices 필드의 get_FOO_display() 를 흉내 냄)"""
        labels = dict(self.TAG_CHOICES)
        return ', '.join(labels.get(tag, tag) for tag in self.get_tag_list())

    def __str__(self):
        return self.title
