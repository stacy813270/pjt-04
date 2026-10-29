from django.core.management.base import BaseCommand
from books.models import Book, Category


class Command(BaseCommand):
    help = '공동 책장에 예시 도서 6권을 추가합니다. 기존 도서는 변경하지 않습니다.'

    def handle(self, *args, **options):
        books = [
            ('어린 왕자', '앙투안 드 생텍쥐페리', '9.5', '작은 별에서 온 어린 왕자가 여러 행성을 여행하며 사랑과 우정, 책임의 의미를 배워가는 이야기입니다.\n익숙한 세상을 조금 다른 시선으로 바라보게 하는 한 권입니다.'),
            ('데미안', '헤르만 헤세', '9.1', '소년 싱클레어가 자신의 내면을 탐색하며 성장하는 이야기입니다. 밝음과 어둠 사이에서 스스로의 길을 찾아가는 여정을 담았습니다.'),
            ('오만과 편견', '제인 오스틴', '9.2', '엘리자베스와 다아시가 서로에 대한 오해를 풀어가는 과정을 그립니다. 날카로운 관찰과 유머로 인간관계와 사회의 모습을 보여주는 소설입니다.'),
            ('모모', '미하엘 엔데', '9.6', '남의 말을 진심으로 들어주는 소녀 모모와 시간을 훔치는 회색 신사들의 이야기입니다. 우리에게 주어진 시간과 일상의 소중함을 돌아보게 합니다.'),
            ('월든', '헨리 데이비드 소로', '8.9', '숲속 작은 집에서 보낸 생활을 통해 자연과 자립, 단순한 삶을 사유한 기록입니다. 분주한 일상에서 잠시 멈추어 삶의 방향을 생각하게 합니다.'),
            ('동물 농장', '조지 오웰', '9.0', '농장의 동물들이 새로운 공동체를 세우면서 벌어지는 일을 다룬 우화입니다. 권력과 평등, 이상이 변해가는 모습을 간결한 이야기 속에 담았습니다.'),
        ]
        created_count = 0
        category_names = {
            '어린 왕자': '어린이·청소년', '모모': '어린이·청소년', '월든': '에세이',
            '데미안': '소설', '오만과 편견': '소설', '동물 농장': '소설',
        }
        for title, author, rating, description in books:
            category, _ = Category.objects.get_or_create(name=category_names[title])
            _, created = Book.objects.get_or_create(title=title, author=author, defaults={
                'customer_review_rank': rating, 'description': description, 'category': category,
            })
            created_count += created
        self.stdout.write(self.style.SUCCESS(f'예시 도서 {created_count}권을 추가했습니다.'))
