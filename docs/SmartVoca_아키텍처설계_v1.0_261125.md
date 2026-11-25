# 아키텍처 설계서 (Architecture Design)

**파일 위치**: `docs/SmartVoca_아키텍처설계_v1.0_261125.md` (정본, 2026-11-25 승인)
**작성일**: 2026-11-25
**버전**: v1.0
**설명**: 스마트 보카의 구성 요소, 계층, 모듈 책임, 실행 경로, 웹 API 개요, 보안 전략을 현재 코드 기준으로 정의한다. Charter §6의 "간략 버전" 계획을 따른다.

---

## 1. 개요

- **형태**: 개인 PC에서만 쓰는 로컬 학습 도구. 외부 통신이 없다 (C-2, NFR-02).
- **프론트엔드 두 개**: PyQt6 데스크톱 화면과 Flask 웹 화면. 두 화면은 **같은 서비스 계층**을 쓴다 (DR-17).
- **저장소**: SQLite 1개, CSV 입출력, JSON 설정 1개.

## 2. 구성 요소 (Topology)

```
┌──────────────────────┐        ┌──────────────────────────────┐
│ PyQt6 데스크톱        │        │ 브라우저 (127.0.0.1:5000)     │
│ src/main.py          │        │  templates/index.html         │
│ src/ui/*             │        │  static/js/*.js               │
└──────────┬───────────┘        └──────────────┬───────────────┘
           │ 직접 호출                          │ HTTP/JSON (/api/*)
           │                                   │
┌──────────▼───────────────────────────────────▼───────────────┐
│ 조립 계층  src/app_context.py (AppContext)                    │
│            src/web/app.py (Flask 앱, 블루프린트)               │
└──────────┬───────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────┐
│ 서비스 계층  src/services/                                     │
│   study_service.py (암기 흐름)   quiz_service.py (시험 흐름)    │
└──────┬─────────────────┬──────────────────┬──────────────────┘
       │                 │                  │
┌──────▼──────┐   ┌──────▼──────┐   ┌───────▼────────┐
│ 도메인 로직  │   │ 보고서       │   │ 설정           │
│ study/      │   │ report/     │   │ config/        │
│ quiz/       │   │             │   │                │
│ models/     │   │             │   │                │
└──────┬──────┘   └──────┬──────┘   └───────┬────────┘
       │                 │                  │
┌──────▼─────────────────▼──────────┐   ┌───▼──────────────────┐
│ 저장 계층  src/storage/            │   │ 파일                  │
│ word/study/quiz 저장소, CSV        │──▶│ smartvoca.db, *.csv,  │
│ database.py (연결·스키마)           │   │ config.json, reports/ │
└───────────────────────────────────┘   └──────────────────────┘
```

## 3. 계층과 의존 규칙

| 계층 | 위치 | 할 일 | 하면 안 되는 일 |
|------|------|-------|-----------------|
| 화면 (데스크톱) | `src/ui/` | 위젯 배치, 입력 처리, 서비스 호출 | SQL 직접 실행 |
| 화면 (웹) | `src/web/templates`, `src/web/static` | 화면 그리기, `/api` 호출 | 서버 로직 판단 (채점, 가중치) |
| 웹 API | `src/web/api_*.py` | 요청 값 검증, 서비스 호출, JSON 응답 | 도메인 규칙 직접 구현 |
| 조립 | `src/app_context.py` | 저장소·서비스·설정 생성 | 규칙 판단 |
| 서비스 | `src/services/` | 여러 단계를 묶은 흐름 (암기·시험) | 화면 객체 사용 |
| 도메인 | `src/study/`, `src/quiz/`, `src/models/` | 규칙 계산 (순수 로직) | PyQt, Flask, SQL import |
| 보고서 | `src/report/` | 기간 집계, HTML 생성 | 화면 객체 사용 |
| 저장 | `src/storage/` | SQL, CSV 읽기·쓰기 | 규칙 판단 |
| 설정·경로 | `src/config/`, `src/paths.py` | 설정 검증, 경로 상수 | — |

**의존 방향**: 화면 → 조립·서비스 → 도메인·저장 → 파일. 반대 방향 import는 두지 않는다.

**알려진 예외**
- `src/report/report_data.py`가 `src/storage/`를 직접 import한다 (도메인이 저장 계층을 읽음). 집계 쿼리가 저장 계층에 있어서 생긴 예외다. 허용하되, 쿼리를 더 늘리지 않는다 (현황분석 F-08).
- `src/study/streak.py`는 PyQt 없이 쓰도록 분리했다 (2026-11-04). 같은 원칙을 도메인 계층 전체에 적용한다.

## 4. 모듈 책임

| 모듈 | 책임 | 요구사항 | 결정 기록 |
|------|------|----------|-----------|
| `src/main.py` | 데스크톱 진입점, 예외 처리 | 전체 | — |
| `src/run_web.py` | 웹 진입점, 127.0.0.1:5000, 단일 스레드 실행 | FR-03 이후 웹 | DR-17 |
| `src/app_context.py` | 구성 요소 조립, CSV 가져오기·내보내기, 설정 갱신 | FR-01, FR-02, FR-13 | DR-02 |
| `src/paths.py` | 개발·배포 경로 분기 | FR-23 | DR-07 |
| `src/config/settings.py` | `Settings` 값, 범위 검증, JSON 읽기·쓰기 | FR-13 | — |
| `src/models/word.py` | `Word`, 뜻 후보 목록 | FR-01, FR-07 | — |
| `src/models/word_stat.py` | 단어별 시험 통계 | FR-05 | — |
| `src/storage/database.py` | 연결, 스키마 생성 | FR-07 | DR-02 |
| `src/storage/word_csv.py` | CSV 검증·읽기·쓰기 | FR-01, FR-02 | DR-11 |
| `src/storage/word_repository.py` | 단어 테이블 | FR-02 | DR-06 |
| `src/storage/study_repository.py` | 암기 세션·카드 | FR-03, FR-04 | DR-08, DR-13 |
| `src/storage/quiz_repository.py` | 시험 세션·응답, 통계 | FR-05, FR-07, FR-08 | — |
| `src/study/study_plan.py` | 일차 목록 계산 | FR-04 | DR-06 |
| `src/study/streak.py` | 연속 학습일 | FR-17 | — |
| `src/quiz/weighting.py` | 가중치, 가중 무작위 선택 | FR-05 | DR-03, DR-09 |
| `src/quiz/question.py` | 문항 모델, 방향·유형 상수 | FR-06 | — |
| `src/quiz/question_builder.py` | 문항 구성 | FR-06 | DR-10 |
| `src/quiz/grader.py` | 정규화, 채점 | FR-07 | DR-04 |
| `src/services/study_service.py` | 암기 세션 시작·이어 하기·응답·되돌리기 | FR-03, FR-04 | DR-08, DR-13, DR-14 |
| `src/services/quiz_service.py` | 시험 생성·채점·저장·재시험 | FR-05 ~ FR-07, FR-12 | — |
| `src/report/report_data.py` | 기간 집계 | FR-08 | — |
| `src/report/report_builder.py` | HTML 보고서 | FR-08 | — |
| `src/ui/*` | PyQt 화면 (홈, 암기, 시험, 이력, 단어 목록, 설정, 보고서) | FR-02 ~ FR-08, FR-12, FR-13, FR-22 | DR-01, DR-15, DR-16 |
| `src/web/app.py` | Flask 앱 조립, 블루프린트 등록, JSON 오류 응답 | DR-17 | DR-17 |
| `src/web/common.py` | 요청 값 검증, 날짜 범위 | — | — |
| `src/web/serializers.py` | 도메인 객체 → JSON | — | — |
| `src/web/api_*.py` | API 블루프린트 (홈, 암기, 시험, 이력, 단어·설정) | 아래 §6 | DR-17 |
| `src/web/static`, `src/web/templates` | 웹 화면 (단일 HTML + JS 6개 + CSS) | 아래 §6 | DR-17 |

## 5. 실행 경로

### 5.1 데스크톱

```
python src/main.py
 → AppContext.open()            (DB 연결, 설정 읽기, 서비스 생성)
 → apply_theme()                (밝게/어둡게, 글자 크기)
 → load_default_words_if_empty()
 → MainWindow                   (탭: 홈, 암기, 시험, 이력, 단어 목록)
```

- 설정 파일 오류 시 메시지 상자를 띄우고 종료한다 (`main.py`).

### 5.2 웹

```
python src/run_web.py
 → AppContext.open()
 → load_default_words_if_empty()
 → create_app(context)          (블루프린트 5개, QUIZ_RUNS 저장소)
 → app.run(127.0.0.1:5000, threaded=False)
```

- `threaded=False`: 한 번에 한 요청만 처리한다. 같은 SQLite 연결을 여러 스레드가 나눠 쓰지 않도록 하기 위해서다 (DR-17).

## 6. 웹 API 개요

> Charter §6에서 Integration Spec을 생략했다. 웹 API가 생겼으므로 그 요약을 여기에 둔다. 별도 인터페이스 정의서로 분리할지는 결정이 필요하다 (현황분석 D-03).

| 메서드 | 경로 | 설명 | 요구사항 |
|--------|------|------|----------|
| GET | `/` | 웹 화면 | — |
| GET | `/api/home` | 오늘 일차, 진도, 연속 학습일, 최근 정답률 | FR-17 일부 |
| GET | `/api/study/session` | 진행 중 암기 세션 또는 상태(`no_words`, `all_done`, `ready`) | FR-03, FR-04 |
| POST | `/api/study/start` | 이어 하기 또는 다음 일차 시작 | FR-04 |
| POST | `/api/study/answer` | 다음 카드에 `know`/`again` 기록 | FR-03 |
| POST | `/api/study/undo` | 마지막 응답 되돌리기 | DR-13 |
| POST | `/api/quiz/runs` | 시험 생성 (`count`, `direction`, `questionType`) | FR-05, FR-06 |
| POST | `/api/quiz/runs/<id>/answers` | 문항 채점 (`index`, `answer`), 마지막 문항이면 요약 포함 | FR-07, FR-12 |
| POST | `/api/quiz/runs/<id>/retry` | 틀린 단어만 재시험 | FR-12 |
| GET | `/api/history/quiz` | 시험 이력 목록 (`start`, `end`, `limit`) | FR-07 |
| GET | `/api/history/quiz/<id>/answers` | 시험 문항별 응답 | FR-07 |
| GET | `/api/history/study` | 암기 이력 목록 | FR-03 |
| GET | `/api/report` | 기간 보고서 HTML 다운로드 (`start`, `end` 필수) | FR-08 |
| GET | `/api/words` | 단어 목록, `q`로 검색 | FR-02 |
| POST | `/api/words/import` | CSV 업로드 불러오기 | FR-02 |
| GET | `/api/words/export` | CSV 내려받기 | FR-02 |
| GET | `/api/settings` | 설정 조회 | FR-13 |
| PUT | `/api/settings` | 설정 저장 (받은 키만 덮어씀) | FR-13 |

**공통 규칙**
- 오류는 `{"error": "메시지"}` JSON으로 준다. `ValueError`·`TypeError`는 400, 나머지 HTTP 오류는 원래 코드.
- 응답 키는 camelCase를 쓴다. 단, `/api/settings`는 설정 파일과 같은 snake_case를 쓴다 (DR-17 제약).
- 시험 문항 응답에는 정답을 넣지 않는다 (PL-17).

## 7. 상태 관리

| 상태 | 위치 | 수명 | 비고 |
|------|------|------|------|
| 학습 기록 | SQLite | 영구 | 데이터 설계서 |
| 설정 | `config.json` | 영구 | 저장 시 즉시 파일 기록 |
| 진행 중 암기 세션 | DB (`finished_at` NULL) | 영구 | 프로그램을 껐다 켜도 이어 한다 |
| 진행 중 시험 | 메모리 (데스크톱 화면 객체, 웹 `QUIZ_RUNS`) | 프로그램 실행 중 | 끄면 사라짐. 채점한 문항은 DB에 있음 |
| 화면 상태 | 데스크톱 위젯, 웹 `quizState`·JS 변수 | 화면 실행 중 | 서버와 어긋나면 서버 값을 우선 |

- 웹 `QUIZ_RUNS`는 완료된 시험을 지우지 않는다. 1인용이라 문제가 되지 않지만 장기 실행 시 쌓인다 (현황분석 F-04).

## 8. 보안 (NFR-07)

| 항목 | 설계 |
|------|------|
| 네트워크 노출 | 웹 서버는 `127.0.0.1`에만 바인딩한다. 외부 기기에서 접속할 수 없다. |
| 인증 | 없음. 1인용 로컬 전제다. 외부 공개 전에 재설계가 필요하다 (DR-17). |
| 비밀정보 | 저장하지 않는다. API 키 없음. |
| 개인정보 | 실명, 학번, 연락처를 저장하지 않는다 (C-3). |
| 입력 검증 | 웹 요청 값은 API 계층에서 검사하고, 설정은 `Settings.validate()`로 검사한다. |
| 출력 이스케이프 | 보고서 HTML의 단어와 뜻은 이스케이프한다 (`html.escape`). |
| SQL | 값은 항상 `?` 자리표시자로 넘긴다. 테이블·컬럼 이름만 코드에서 고정 문자열로 만든다 (`word_repository.get_by_ids`의 `IN` 목록도 자리표시자). |

## 9. 오류 처리 정책

| 위치 | 처리 |
|------|------|
| 데스크톱 시작 시 설정 오류 | `ValueError`, `JSONDecodeError`만 잡아 메시지 상자 표시 (타입 오류는 미처리, F-01) |
| 데스크톱 화면 동작 | 메시지 상자로 사용자에게 알린다 |
| 웹 API | `ValueError`·`TypeError` → 400 JSON. 그 밖의 오류는 Flask 기본 처리 |
| CSV 불러오기 | 행 단위 오류는 건너뛰고 목록으로 돌려준다. DB 오류는 전체 취소 |

## 10. 확장 지점

| 예정 기능 | 붙일 위치 | 영향 |
|-----------|-----------|------|
| FR-09 단어 편집 | `WordRepository`에 추가·수정·삭제, 웹 API와 데스크톱 상세 대화상자 | 시험 스냅샷은 바뀌지 않음 (데이터 설계서 3.5) |
| FR-10 편집 거리 채점 | `grader.py`에 함수 추가, `grade_answer` 분기 | 테스트 필수 |
| FR-11 오답 단어장 | `quiz_repository`에 오답률 조회, `quiz_service`에 출제 원천 추가 | 기존 가중치와 별도 경로 |
| FR-14 TTS | `src/speech/` 새 패키지 (pyttsx3 래퍼). 화면 두 곳에서 호출 | 설치 패키지와 PyInstaller 설정 변경 |
| FR-19 백업 | 새 `backup.py`, DB 파일 복사 | `paths.py`의 경로 사용 |
| FR-18 Excel | `report/`에 xlsx 출력 추가 | openpyxl 추가 |

## 11. 관련 결정 기록

| DR | 내용 | 이 문서에서의 반영 |
|----|------|-------------------|
| DR-01 | PyQt6 | 데스크톱 화면 계층 |
| DR-02 | SQLite + CSV | 저장 계층 |
| DR-03 | 가중치 방식 | 도메인 `quiz/weighting.py` |
| DR-07 | 데이터 경로 분기 | `paths.py` |
| DR-13 ~ DR-16 | 되돌리기, 다음 일차 버튼, 다시 보기 의미, 표 모델 | 서비스·화면 계층 |
| DR-17 | Flask 웹 버전, 로컬 전용 | 웹 계층, §6 API |

## 12. 알려진 구조 이슈

| ID | 내용 | 영향 | 조치 |
|----|------|------|------|
| AQ-01 | `report_data.py`가 저장 계층을 직접 import | 낮음 | 허용 예외로 기록 (§3) |
| AQ-02 | `AppContext`의 서비스 필드가 `None`으로 만들어진 뒤 채워진다 (`type: ignore`) | 낮음 | 생성자 순서로 정리 가능 |
| AQ-03 | 웹 진행 중 시험이 메모리에만 있다 | 낮음 (1인용) | §7 참조 |
| AQ-04 | 데스크톱과 웹이 같은 서비스를 쓰지만 화면 상태 관리는 따로다 | 중간 (동작이 다를 수 있음) | 수동 테스트로 비교 (테스트 정의서) |
