# 요구사항 명세서 (Requirement Spec)

**파일 위치**: `ai-agent/claude/SmartVoca_Requirement_Spec_v1.0_261021.md` (초안, 승인 후 `docs/` 승격)
**작성일**: 2026-10-21
**버전**: v1.0
**설명**: 스마트 보카의 기능·비기능 요구사항, 수용 기준, 구현 모듈 매핑을 정의한다.

---

## 1. 우선순위 정의

| 표기 | 의미 |
|------|------|
| MVP | 최소 기능 제품. 필수 구현 |
| 1차 | MVP 이후 첫 번째 개선 |
| 2차 | 1차 이후 개선 |
| 선택 | 여유가 있을 때 구현 |

## 2. 기능 요구사항 (FR)

### 2.1 MVP

| ID | 요구사항 | 수용 기준 | 우선순위 |
|----|----------|-----------|----------|
| FR-01 | 단어 데이터 제공 | CSV 2000행. 컬럼은 `id, word, pos, meaning, example, level`. 인코딩 UTF-8 with BOM. `word` 값 중복 없음 | MVP |
| FR-02 | 단어 목록 불러오기·저장 | 파일 대화상자로 CSV를 읽어 DB에 반영. 잘못된 행은 건너뛰고 행 번호와 사유 목록 표시. 현재 단어 목록을 CSV로 내보내기 가능 | MVP |
| FR-03 | 암기 모드 (플래시카드) | 앞면에 `word` 표시, 뒤집기 버튼으로 `meaning`과 `example` 표시. 카드별 "알았음" / "다시" 표기를 이력에 저장 | MVP |
| FR-04 | 하루 단위 진도 생성 | 설정의 "하루 신규 단어 수 N"(기본 20)에 따라 1일차는 `id` 오름차순 1~N번, 2일차는 N+1~2N번. 세션 시작 시 "N일차" 표시. 직전 학습일의 "다시" 단어 중 최대 M개(기본 10)를 당일 목록 앞에 복습 단어로 포함 | MVP |
| FR-05 | 가중치 기반 랜덤 시험 | 사용자가 문제 수(5~100, 기본 20)를 지정하면 가중치에 따라 랜덤 출제. 같은 시험에서 같은 단어는 한 번만 출제. 가중치 규칙은 DR-03 참조 | MVP |
| FR-06 | 출제 방향·유형 선택 | 방향: 한→영, 영→한, 혼합. 유형: 단답형, 4지선다형, OX형, 혼합. 혼합 방향이나 혼합 유형일 때 문제마다 무작위로 결정 | MVP |
| FR-07 | 채점과 이력 저장 | 단답형은 앞뒤 공백과 대소문자를 무시하고 비교. 뜻이 여러 개(쉼표 구분)면 그중 하나만 맞아도 정답. 4지선다형은 보기 4개 중 1개 선택. OX형은 제시된 뜻과 단어의 짝이 맞으면 O, 아니면 X. 시험 세션과 문항별 결과를 SQLite에 저장 | MVP |
| FR-08 | 기간별 HTML 보고서 | 시작일과 종료일을 지정하면 다음 항목을 포함한 HTML 파일 생성: 학습 일수, 암기 단어 수, 시험 횟수, 평균 정답률, 자주 틀린 단어 TOP 10 | MVP |
| FR-13 | 설정 저장 | `config.json`에 하루 신규 단어 수, 복습 단어 수, 시험 문제 수 기본값, 가중치 값을 저장하고 시작 시 읽음 | MVP |

### 2.2 1차

| ID | 요구사항 | 수용 기준 |
|----|----------|-----------|
| FR-09 | 단어 편집 GUI | 단어 추가·수정·삭제, `word` 또는 `meaning`으로 검색. 저장 전 중복 검사 |
| FR-10 | 편집 거리 채점 | 단어 길이 5자 이상일 때 편집 거리 1까지 정답 처리 (DR-04) |
| FR-11 | 오답 단어장 | 오답률이 기준(기본 50%) 이상인 단어를 별도 목록으로 보기, 이 목록만으로 시험 가능 |
| FR-12 | 시험 결과 요약 | 시험 종료 후 정답 수, 정답률, 틀린 문항 목록 표시 |
| FR-14 | TTS 발음 | `pyttsx3`로 `word` 발음 재생. 영어 음성이 없으면 버튼 비활성화 |

### 2.3 2차

| ID | 요구사항 | 수용 기준 |
|----|----------|-----------|
| FR-15 | 간격 반복 알고리즘 (SRS) | SM-2 방식으로 다음 복습 시점 계산. 가중치 방식(FR-05)과 병행 가능 (DR-03) |
| FR-16 | 듣기 시험 | TTS로 발음을 들려주고 단어를 입력 |
| FR-17 | 학습 통계·달력 | 날짜별 학습량 달력, 연속 학습일(streak) 표시 |
| FR-18 | Excel 보고서 | FR-08 보고서를 `.xlsx`로도 출력 (`openpyxl`) |
| FR-19 | DB 백업·복원 | SQLite 파일을 날짜가 붙은 이름으로 복사, 백업 파일로 복원 |
| FR-20 | 시험 시간 제한 | 전체 시험 시간을 설정하고, 시간이 끝나면 자동 종료 |

### 2.4 선택

| ID | 요구사항 | 수용 기준 |
|----|----------|-----------|
| FR-21 | Windows 알림 | 설정한 시간에 학습 알림 표시 |
| FR-22 | 다크 모드 | 설정에서 밝은 테마와 어두운 테마 전환 |
| FR-23 | exe 배포 | PyInstaller로 단일 실행 파일 생성, 데이터 경로를 `%APPDATA%\SmartVoca`로 전환 (DR-07) |

## 3. 비기능 요구사항 (NFR)

| ID | 분류 | 요구사항 |
|----|------|----------|
| NFR-01 | 호환성 | Windows 10/11, Python 3.11 이상에서 실행 |
| NFR-02 | 오프라인 | MVP 기능은 인터넷 없이 동작 |
| NFR-03 | 성능 | 단어 2000개 로딩과 목록 표시는 1초 이내 (목표) |
| NFR-04 | 데이터 보호 | 원본 CSV를 덮어쓰지 않음. 불러오기 전 기존 DB 백업 옵션 제공 (1차) |
| NFR-05 | 유지보수 | 파일 1개는 500줄 이하 유지. 함수·클래스에 한두 줄 설명 주석 추가 (학습 목적) |
| NFR-06 | 테스트 | 가중치 계산, 채점, 출제, CSV 로딩, 진도 생성은 pytest 단위 테스트 필수 |
| NFR-07 | 보안 | 개인정보와 비밀정보를 저장하지 않음. 설정 파일에 API 키 없음 |
| NFR-08 | 추적성 | 모든 구현 커밋 메시지와 테스트에 FR/NFR ID 명시 (방법론 §3) |

## 4. 가중치 규칙 (FR-05 초안)

출제 가중치 `w`는 다음 식으로 계산한다. 값은 모두 `config.json`에서 조정한다 (기본값은 DR-03 참조).

```
w = 1
  + W_NEW     (시험 이력이 없으면 가산)
  + W_OLD     (마지막 시험 후 OLD_DAYS일 이상 지났으면 가산)
  + W_WRONG × 오답률   (오답률 = 오답 수 / 전체 응답 수, 응답이 없으면 0)
```

기본값: `W_NEW = 3`, `W_OLD = 2`, `OLD_DAYS = 7`, `W_WRONG = 4`

## 5. 구현 매핑 (계획)

| 모듈 (파일) | 주요 클래스·함수 | 담당 요구사항 |
|-------------|------------------|---------------|
| `src/main.py` | `main()` | 진입점 |
| `src/models/word.py` | `Word` (dataclass) | FR-01 |
| `src/storage/word_csv.py` | `load_words_from_csv()`, `save_words_to_csv()` | FR-01, FR-02 |
| `src/storage/database.py` | `Database` (연결, 스키마 생성) | FR-07 |
| `src/storage/word_repository.py` | `WordRepository` | FR-02, FR-09 |
| `src/storage/history_repository.py` | `HistoryRepository` | FR-03, FR-07, FR-08 |
| `src/config/settings.py` | `Settings` (config.json 읽기·쓰기) | FR-13 |
| `src/study/study_plan.py` | `StudyPlanner.build_day_plan()` | FR-04 |
| `src/quiz/weighting.py` | `compute_word_weight()`, `pick_weighted_words()` | FR-05 |
| `src/quiz/question_builder.py` | `QuestionBuilder` (방향·유형별 문제 생성) | FR-06 |
| `src/quiz/grader.py` | `normalize()`, `is_short_answer_correct()` | FR-07, FR-10 |
| `src/report/report_builder.py` | `build_html_report()` | FR-08 |
| `src/ui/main_window.py` | `MainWindow` | 전체 화면 전환 |
| `src/ui/study_view.py` | `StudyView` | FR-03, FR-04 |
| `src/ui/quiz_view.py` | `QuizView` | FR-05 ~ FR-07 |
| `src/ui/word_list_view.py` | `WordListView` | FR-02, FR-09 |

## 6. 화면 정의 (MVP)

| 화면 | 구성 요소 | 연결 요구사항 |
|------|-----------|---------------|
| 메인 | 탭 3개: 암기, 시험, 단어 목록 / 메뉴: 파일(불러오기·저장), 보고서, 설정 | FR-02, FR-08, FR-13 |
| 암기 | 현재 N일차 표시, 카드(앞·뒤), 뒤집기, 알았음·다시 버튼, 진행률 | FR-03, FR-04 |
| 시험 | 설정 패널(문제 수, 방향, 유형), 시작 버튼, 문제 영역, 답 입력 또는 보기 선택, 다음 버튼 | FR-05 ~ FR-07 |
| 단어 목록 | 표 (id, word, meaning), 불러오기·저장 버튼 | FR-02 |
| 설정 | 하루 신규 단어 수, 복습 단어 수, 시험 문제 수 기본값, 가중치 값 | FR-13 |

## 7. 추적 매트릭스

| 요구사항 | 기획 문서 | 결정 기록 | 테스트 (계획) |
|----------|-----------|-----------|----------------|
| FR-01, FR-02 | Charter §3.1 | DR-05, DR-02 | `test_word_csv.py` |
| FR-03, FR-04 | Charter §2 G-1 | DR-06 | `test_study_plan.py` |
| FR-05 | Charter §2 G-2 | DR-03 | `test_weighting.py` |
| FR-06, FR-07 | Charter §3.1 | DR-04 | `test_question_builder.py`, `test_grader.py` |
| FR-08 | Charter §2 G-3 | DR-02 | `test_report_builder.py` |
| FR-13 | Charter §3.1 | DR-07 | `test_settings.py` |

테스트 파일 이름은 계획이며, Test Specification 작성 시 확정한다.
