# 요구사항별 실행 결과 캡처

촬영: **2026-10-29 (Asia/Seoul)** · Google Chrome · PNG **32장**

PDF의 필수 요구사항 **F401~F416, NF401~NF402**와 구현된 심화 항목 **F418~F419**를 확인했습니다. 각 기능을 실제로 실행한 전체 페이지 캡처입니다. 입력·확인 화면에 더해 저장·삭제 후 결과 화면도 포함했습니다.

**[전체 이미지 갤러리](screenshots/index.html)** · **[전체 압축 파일](screenshots.zip)**

- 캡처 전용 SQLite DB 복사본과 테스트 계정을 사용했으며 원본 `db.sqlite3`는 변경하지 않았습니다.
- 회원가입·로그인·회원 수정·비밀번호 변경·도서 CRUD·로그아웃·회원탈퇴를 실제로 처리했습니다. 비밀번호 변경 후 세션 유지와 변경된 비밀번호 로그인도 확인했습니다.
- `23`~`25` 이미지는 서비스 화면이 아닌 **실제 Django 실행 결과를 정리한 검증 보고서**입니다. 모델·폼의 상속/필드, URL 역참조, HTTP 405·CSRF 403·로그인 이동 302 응답을 확인했습니다.
- **F417은 현재 미구현된 선택 과제이므로 실행 화면이 없습니다.** 추가 기능인 좋아요 기반 GPT 추천은 작가 정보 생성·저장과 다른 기능입니다.
- 추가 기능으로 개인 좋아요·카테고리·관심 카테고리·모바일 메뉴·실제 GMS 추천 성공 및 요청 중 버튼 비활성화 화면도 포함했습니다.
- 데스크톱 뷰포트는 1440 × 1000, 모바일은 390 × 844입니다. 전체 페이지 캡처여서 PNG 높이는 화면별로 다릅니다.
- `14-invalid-input.png`는 브라우저 기본 입력 제한을 생략해 **서버에서 평점 11을 거부한 오류**를 확인한 화면입니다.

## PDF 요구사항 대응

| 요구사항 | 확인 항목 | 실행 결과 이미지 |
| --- | --- | --- |
| F401 | 프로젝트·앱·공통 Navbar | [01-index-guest.png](screenshots/01-index-guest.png)<br>[15-mobile.png](screenshots/15-mobile.png)<br>[23-model-form-verification.png](screenshots/23-model-form-verification.png) |
| F402 | AbstractUser 사용자 모델 | [03-signup.png](screenshots/03-signup.png)<br>[23-model-form-verification.png](screenshots/23-model-form-verification.png) |
| F403 | 회원 Form과 유효성 검증 | [02-login.png](screenshots/02-login.png)<br>[03-signup.png](screenshots/03-signup.png)<br>[23-model-form-verification.png](screenshots/23-model-form-verification.png) |
| F404 | Book 모델의 네 필드 | [05-book-create.png](screenshots/05-book-create.png)<br>[23-model-form-verification.png](screenshots/23-model-form-verification.png) |
| F405 | BookForm과 입력 오류 | [05-book-create.png](screenshots/05-book-create.png)<br>[14-invalid-input.png](screenshots/14-invalid-input.png)<br>[23-model-form-verification.png](screenshots/23-model-form-verification.png) |
| F406 | 로그인과 인증별 메뉴 | [01-index-guest.png](screenshots/01-index-guest.png)<br>[02-login.png](screenshots/02-login.png)<br>[02b-login-success.png](screenshots/02b-login-success.png)<br>[04-index-member.png](screenshots/04-index-member.png) |
| F407 | 로그아웃 | [12-logout.png](screenshots/12-logout.png) |
| F408 | 회원가입과 자동 로그인 | [03-signup.png](screenshots/03-signup.png)<br>[04-index-member.png](screenshots/04-index-member.png) |
| F409 | 회원정보 수정 | [10-account-update.png](screenshots/10-account-update.png)<br>[10b-account-updated.png](screenshots/10b-account-updated.png)<br>[10c-profile-updated.png](screenshots/10c-profile-updated.png) |
| F410 | 회원탈퇴 | [13-account-delete.png](screenshots/13-account-delete.png)<br>[13b-account-deleted.png](screenshots/13b-account-deleted.png) |
| F411 | 비밀번호 변경과 세션 유지 | [02b-login-success.png](screenshots/02b-login-success.png)<br>[11-password.png](screenshots/11-password.png)<br>[11b-password-changed.png](screenshots/11b-password-changed.png) |
| F412 | 전체 도서 조회 | [01-index-guest.png](screenshots/01-index-guest.png) |
| F413 | 도서 등록 | [05-book-create.png](screenshots/05-book-create.png)<br>[06-book-detail.png](screenshots/06-book-detail.png)<br>[14-invalid-input.png](screenshots/14-invalid-input.png) |
| F414 | 도서 상세 조회 | [06-book-detail.png](screenshots/06-book-detail.png) |
| F415 | 도서 수정 | [07-book-update.png](screenshots/07-book-update.png)<br>[07b-book-updated.png](screenshots/07b-book-updated.png) |
| F416 | 도서 삭제 | [08-book-delete.png](screenshots/08-book-delete.png)<br>[08b-book-deleted.png](screenshots/08b-book-deleted.png) |
| F417 | AI 작가 정보 생성·저장 (선택) | **미구현 (선택 과제)** |
| F418 | 독서 정보·복수 관심 장르 (선택) | [03-signup.png](screenshots/03-signup.png)<br>[10-account-update.png](screenshots/10-account-update.png)<br>[23-model-form-verification.png](screenshots/23-model-form-verification.png) |
| F419 | 개인 프로필 (선택) | [09-profile.png](screenshots/09-profile.png)<br>[10c-profile-updated.png](screenshots/10c-profile-updated.png) |
| NF401 | URL 이름 공간과 역참조 | [24-url-verification.png](screenshots/24-url-verification.png) |
| NF402 | HTTP 메서드 제한 | [25-http-method-verification.png](screenshots/25-http-method-verification.png) |

## 전체 캡처 목록

| 이미지 | 실행 내용 | 요구사항 |
| --- | --- | --- |
| [01-index-guest.png](screenshots/01-index-guest.png) | 비로그인 전체 도서 목록 | F401, F406, F412 |
| [02-login.png](screenshots/02-login.png) | 로그인 폼과 잘못된 인증 정보 오류 | F403, F406 |
| [02b-login-success.png](screenshots/02b-login-success.png) | 변경된 비밀번호로 로그인 성공 | F406, F411 |
| [03-signup.png](screenshots/03-signup.png) | 추가 독서 정보와 관심 장르를 입력한 회원가입 폼 | F402, F403, F408, F418 |
| [04-index-member.png](screenshots/04-index-member.png) | 회원가입 완료 후 자동 로그인 | F406, F408 |
| [05-book-create.png](screenshots/05-book-create.png) | 도서 네 필드와 카테고리 입력 | F404, F405, F413 |
| [06-book-detail.png](screenshots/06-book-detail.png) | 등록 성공 후 도서 상세 | F413, F414 |
| [07-book-update.png](screenshots/07-book-update.png) | 기존 값이 복원된 도서 수정 폼 | F415 |
| [07b-book-updated.png](screenshots/07b-book-updated.png) | 제목과 평점 수정 완료 | F415 |
| [08-book-delete.png](screenshots/08-book-delete.png) | 도서 삭제 확인 모달 | F416 |
| [08b-book-deleted.png](screenshots/08b-book-deleted.png) | 삭제 후 홈페이지와 완료 알림 | F416 |
| [09-profile.png](screenshots/09-profile.png) | 기본 정보와 독서 프로필 | F419 |
| [10-account-update.png](screenshots/10-account-update.png) | 수정 폼과 복원된 관심 장르 | F409, F418 |
| [10b-account-updated.png](screenshots/10b-account-updated.png) | 회원정보 저장 후 홈페이지 | F409 |
| [10c-profile-updated.png](screenshots/10c-profile-updated.png) | 저장된 이름과 연간 독서량 확인 | F409, F419 |
| [11-password.png](screenshots/11-password.png) | 기존 비밀번호와 새 비밀번호 입력 | F411 |
| [11b-password-changed.png](screenshots/11b-password-changed.png) | 비밀번호 변경 완료와 로그인 유지 | F411 |
| [12-logout.png](screenshots/12-logout.png) | 로그아웃 후 비로그인 Navbar | F407 |
| [13-account-delete.png](screenshots/13-account-delete.png) | 테스트 회원 탈퇴 확인 | F410 |
| [13b-account-deleted.png](screenshots/13b-account-deleted.png) | 회원탈퇴 후 홈페이지와 세션 종료 | F410 |
| [14-invalid-input.png](screenshots/14-invalid-input.png) | 서버 검증으로 범위 밖 평점 거부 | F405, F413 |
| [15-mobile.png](screenshots/15-mobile.png) | 모바일 목록과 펼친 메뉴 | F401 |
| [16-book-like.png](screenshots/16-book-like.png) | 도서 상세의 개인 좋아요 선택 | 추가: 개인 좋아요 |
| [17-my-liked-books.png](screenshots/17-my-liked-books.png) | 본인이 좋아요한 도서 목록 | 추가: 개인 좋아요 |
| [18-category-list.png](screenshots/18-category-list.png) | 선택한 카테고리의 도서 목록과 건수 | 추가: 카테고리 조회 |
| [19-category-create.png](screenshots/19-category-create.png) | 새 카테고리를 입력한 도서 등록 폼 | 추가: 카테고리 생성 |
| [20-interest-categories.png](screenshots/20-interest-categories.png) | 복수 관심 카테고리 저장과 목록 링크 | 추가: 관심 카테고리 |
| [21-gpt-recommendations.png](screenshots/21-gpt-recommendations.png) | 실제 GMS 추천 응답 | 추가: GPT 추천 |
| [22-recommendation-throttle.png](screenshots/22-recommendation-throttle.png) | 실제 추천 요청 중 중복 실행 차단 | 추가: 추천 쓰로틀 |
| [23-model-form-verification.png](screenshots/23-model-form-verification.png) | 모델과 폼 실행 검증 | F401, F402, F403, F404, F405, F418 |
| [24-url-verification.png](screenshots/24-url-verification.png) | URL 이름 공간 실행 검증 | NF401 |
| [25-http-method-verification.png](screenshots/25-http-method-verification.png) | HTTP 메서드와 CSRF 실행 검증 | NF402 |

실제 촬영 URL·촬영 환경·부가 설명은 [manifest.json](screenshots/manifest.json)에 기록했습니다. 검증 보고서 HTML 원본도 같은 폴더에 포함했습니다.
