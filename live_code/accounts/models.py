from django.contrib.auth.models import AbstractUser


# [STEP 1-1] 기본 User 를 우리 User 로 교체하기
# ※ AbstractUser 를 상속하면 username · password · email 등 기본 필드를 그대로 물려받음
# ※ 지금은 필드를 추가하지 않고 "교체만" 해 둠 => 필요해지면 이 클래스에 필드를 추가
class User(AbstractUser):
    pass
