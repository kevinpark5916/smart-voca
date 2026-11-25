# 데이터 설계서 (Data Design)

**파일 위치**: `docs/SmartVoca_데이터설계_v1.0_261125.md` (정본, 2026-11-25 승인)
**작성일**: 2026-11-25
**버전**: v1.0
**설명**: 스마트 보카의 SQLite 테이블, 컬럼, 관계, 제약, 쓰기·읽기 흐름, 설정 파일 규격을 현재 코드 기준으로 정의한다.

---

## 1. 저장소 개요

| 저장소 | 개발 실행 경로 | exe 배포 경로 | 형식 | 역할 |
|--------|----------------|---------------|------|------|
| 학습 DB | `data/smartvoca.db` | `%APPDATA%\SmartVoca\smartvoca.db` | SQLite 3 | 단어, 암기 기록, 시험 기록 |
| 기본 단어 원본 | `data/words.csv` | exe 내부 `data/words.csv` (읽기 전용) | UTF-8 BOM CSV | 최초 실행 때 DB로 적재 |
| 설정 | `data/config.json` | `%APPDATA%\SmartVoca\config.json` | JSON (UTF-8) | 학습량, 시험 기본값, 가중치, 화면 설정 |
| 보고서 | `data/reports/` | `%APPDATA%\SmartVoca\reports\` | HTML | 기간 보고서 출력물 |

- 경로는 `src/paths.py`에서 한 번만 정한다 (DR-07, FR-23).
- `data/smartvoca.db`와 `data/*.db`, `data/backups/`는 `.gitignore`로 커밋에서 제외한다 (CLAUDE.md 규칙 6).
- `data/words.csv`는 2000행 단어 원본이라 커밋 대상이다.

## 2. 공통 규칙

| 항목 | 규칙 | 근거 |
|------|------|------|
| 시각 저장 | 로컬 시간을 `YYYY-MM-DDTHH:MM:SS` 문자열(TEXT)로 저장 (`isoformat(timespec="seconds")`) | `src/storage/*_repository.py` |
| 날짜 비교 | 시각 문자열의 앞 10자리(`substr(col, 1, 10)`)를 `YYYY-MM-DD`로 비교 | `report_data.py`, 이력 조회 |
| 암기 결과 코드 | `know`(알았음), `again`(다시) | `RESULT_KNOW`, `RESULT_AGAIN` |
| 미응답 표시 | `study_record.result`가 NULL이면 아직 답하지 않은 카드 | DR-13 되돌리기 |
| 진행 중 표시 | `*_session.finished_at`이 NULL이면 진행 중 | DR-08 |
| 시험 방향·유형 | `quiz_session`에는 요청 값(`mixed` 가능), `quiz_answer`에는 문항별 실제 값(`mixed` 해소 후) 저장 | FR-06 |
| 외래 키 | 연결마다 `PRAGMA foreign_keys = ON` | `database.py` |
| SQL 작성 | 한 쿼리 안에 빈 줄을 넣지 않는다 (CLAUDE.md 규칙 4) | `database.py` |

## 3. 테이블 명세

### 3.1 word (단어)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK | CSV의 `id`를 그대로 사용 (DR-02). 일차 진도 순서 기준 (DR-06) |
| word | TEXT | NOT NULL, UNIQUE | 영단어. 대소문자 구분 UNIQUE (주의: 10절 DQ-01 참조) |
| pos | TEXT | NOT NULL | 품사 (예: `n.`, `v.`) |
| meaning | TEXT | NOT NULL | 뜻. 쉼표로 여러 뜻 구분 가능 (FR-07) |
| example | TEXT | NOT NULL | 예문 |
| level | INTEGER | NOT NULL | 표시용 난이도. 정렬에 쓰지 않는다 (DR-06) |

- 생성: 불러오기 시 `INSERT ... ON CONFLICT(id) DO UPDATE` (id가 같으면 값 갱신).
- 2000행이 기준이다 (FR-01).

### 3.2 study_session (암기 일차 세션)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 세션 번호 |
| day_no | INTEGER | NOT NULL | N일차 (1부터) |
| started_at | TEXT | NOT NULL | 세션 생성 시각 |
| finished_at | TEXT | NULL 허용 | 모든 카드에 답하면 기록. NULL이면 진행 중 |

- 한 일차가 한 세션이다. 같은 `day_no`가 여러 세션으로 생기지 않도록 `start_or_resume`이 관리한다 (PL-04).
- 진행 중 세션은 최대 1개여야 한다는 규칙은 **애플리케이션 규칙**이며 DB 제약으로 강제하지 않는다 (5절 DI-05 참조).

### 3.3 study_record (암기 카드 기록)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 카드 번호 |
| session_id | INTEGER | NOT NULL, FK → study_session.id | 소속 세션 |
| word_id | INTEGER | NOT NULL, FK → word.id | 단어 |
| position | INTEGER | NOT NULL | 세션 안 카드 순서 (0부터). 복습 카드가 앞 |
| kind | TEXT | NOT NULL | `review`(복습) 또는 `new`(신규) |
| result | TEXT | NULL 허용 | `know`, `again`, 또는 NULL(미응답) |
| recorded_at | TEXT | NULL 허용 | 응답 시각. 되돌리면 NULL |

- 인덱스 `idx_study_record_session` (session_id).
- 같은 단어가 여러 일차에 나올 수 있다 (복습 카드). 일차 안에서는 중복되지 않는다 (PL-03).

### 3.4 quiz_session (시험 세션)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 시험 번호 |
| started_at | TEXT | NOT NULL | 시험 생성 시각 |
| finished_at | TEXT | NULL 허용 | 마지막 문항 채점 후 기록 |
| direction | TEXT | NOT NULL | 요청한 방향 (`ko_en`, `en_ko`, `mixed`) |
| question_type | TEXT | NOT NULL | 요청한 유형 (`short`, `choice`, `ox`, `mixed`) |
| total | INTEGER | NOT NULL | 문항 수 |

### 3.5 quiz_answer (시험 문항 응답)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 응답 번호 |
| quiz_session_id | INTEGER | NOT NULL, FK → quiz_session.id | 소속 시험 |
| word_id | INTEGER | NOT NULL, FK → word.id | 단어 |
| direction | TEXT | NOT NULL | 문항의 실제 방향 (`ko_en` 또는 `en_ko`) |
| question_type | TEXT | NOT NULL | 문항의 실제 유형 (`short`, `choice`, `ox`) |
| prompt | TEXT | NOT NULL | 화면에 보여 준 문제 (스냅샷) |
| expected | TEXT | NOT NULL | 정답 표시 (스냅샷). OX는 `O` 또는 `X` |
| user_answer | TEXT | NOT NULL | 사용자가 입력하거나 고른 답 |
| is_correct | INTEGER | NOT NULL | 1이면 정답, 0이면 오답 |
| answered_at | TEXT | NOT NULL | 응답 시각 |

- `prompt`와 `expected`는 단어 정보를 복사해 둔 **스냅샷**이다. 나중에 단어를 고쳐도 과거 시험 기록은 바뀌지 않는다. 이 때문에 FR-09(단어 편집) 구현 시 이 점이 중요하다.
- 인덱스 `idx_quiz_answer_word` (word_id). 가중치 계산과 오답 집계가 이 인덱스를 쓴다.

## 4. 관계

```
word 1 ──────< study_record >────── 1 study_session
 │
 └──────────< quiz_answer >─────── 1 quiz_session
```

- `word`는 기준 테이블이다. 학습 기록과 시험 기록이 모두 `word.id`를 가리킨다.
- `study_record`와 `quiz_answer`는 서로 독립이다. 시험 결과가 암기 카드에 영향을 주지 않는다.
- 세션 삭제 기능은 없다. 기록은 누적만 된다 (보관 정책은 8절).

## 5. 제약과 무결성

| ID | 규칙 | 강제 방법 | 상태 |
|----|------|-----------|------|
| DI-01 | 단어 id 중복 없음 | PK | 강제됨 |
| DI-02 | 단어 원문(word) 중복 없음 | UNIQUE (대소문자 구분) | 강제됨, 단 CSV 검사와 기준이 다름 (10절 DQ-01) |
| DI-03 | 기록은 존재하는 단어·세션만 참조 | FOREIGN KEY | 강제됨 |
| DI-04 | 카드 결과는 `know`, `again`, NULL 중 하나 | 없음 (서비스·API에서 검사) | 애플리케이션 검사 (`VALID_RESULTS`) |
| DI-05 | 진행 중 암기 세션은 최대 1개 | 없음 (`start_or_resume`에서 검사) | 애플리케이션 규칙 |
| DI-06 | 시험 문항 정답 여부는 0 또는 1 | 없음 | 애플리케이션 규칙 |
| DI-07 | 설정 값 범위 | `Settings.validate()` | 저장 전·읽기 후 검사 |
| DI-08 | 불러오기는 전부 성공하거나 전부 실패 | 트랜잭션 (`with connection`) | 강제됨 |

## 6. 쓰기·읽기 흐름

| 흐름 | 쓰기 대상 | 트랜잭션 | 참조 로직 |
|------|-----------|----------|-----------|
| 단어 CSV 불러오기 | word (upsert) | 전체 한 번에 | PL-01 |
| 암기 일차 시작 | study_session, study_record (N개) | 한 번에 | PL-03, PL-04 |
| 카드 응답 | study_record.result, recorded_at | 한 건씩 | PL-05 |
| 카드 되돌리기 | study_record.result·recorded_at을 NULL로, study_session.finished_at을 NULL로 | 한 건씩 | PL-06 |
| 세션 완료 | study_session.finished_at | 한 건 | PL-05 |
| 시험 생성 | quiz_session | 한 건 | PL-10 |
| 문항 채점 | quiz_answer | 한 건씩 | PL-12 |
| 시험 완료 | quiz_session.finished_at | 한 건 | PL-13 |
| 가중치 계산 (읽기) | quiz_answer 집계 (단어별 응답 수, 오답 수, 마지막 응답 시각) | — | PL-08 |
| 연속 학습일 (읽기) | study_record.recorded_at 날짜 목록 | — | PL-07 |
| 기간 보고서 (읽기) | 세 테이블 집계 | — | PL-15 |

## 7. 설정 파일 (config.json) 규격

| 키 | 타입 | 기본값 | 허용 범위 | 사용처 |
|----|------|--------|-----------|--------|
| daily_new_count | int | 20 | 1~200 | 하루 신규 단어 수 (FR-04) |
| daily_review_count | int | 10 | 0~100 | 하루 복습 단어 최대 수 (FR-04) |
| quiz_question_count | int | 20 | 5~100 | 시험 문제 수 기본값 (FR-05) |
| weight_new | float | 3.0 | 0 이상 | 이력 없는 단어 가산 (FR-05) |
| weight_old | float | 2.0 | 0 이상 | 오래된 단어 가산 (FR-05) |
| old_days | int | 7 | 1~365 | "오래됨" 기준 일수 (FR-05) |
| weight_wrong | float | 4.0 | 0 이상 | 오답률 가산 계수 (FR-05) |
| theme | str | "light" | light, dark | 화면 테마 (FR-22) |
| font_scale | str | "normal" | small, normal, large | 글자 크기 |

- 파일이 없으면 기본값을 쓴다. 모르는 키는 무시한다 (`load_settings`).
- 값이 범위를 벗어나면 `ValueError`로 거부하고 파일을 쓰지 않는다 (`save_settings`).
- 알려진 문제: 타입이 틀린 값(예: 문자열 숫자)은 `TypeError`가 날 수 있고, 데스크톱 시작 시 처리되지 않는다 (현황분석 F-01).

## 8. 보관·백업 (현재 상태)

- 현재 백업 기능이 없다 (FR-19 2차, NFR-04의 "불러오기 전 백업 옵션"은 1차).
- 데이터 삭제 기능이 없다. 기록은 계속 쌓인다. 개인 학습 기록 규모에서는 문제가 없지만, 보관 기간 정책은 결정이 필요하다 (현황분석 D-07).
- 스키마 변경 절차가 없다. `CREATE TABLE IF NOT EXISTS`만 있어서 기존 테이블 구조를 바꿀 수 없다. 컬럼을 추가하려면 버전 번호와 마이그레이션 단계가 필요하다 (현황분석 F-03).

## 9. 인덱스와 성능

| 인덱스 | 대상 | 목적 |
|--------|------|------|
| idx_quiz_answer_word | quiz_answer(word_id) | 단어별 가중치 집계 |
| idx_study_record_session | study_record(session_id) | 세션 카드 조회 |

- 날짜 기간 조회(`substr(...) BETWEEN`)는 인덱스를 타지 않는다. 기록이 수만 행 이하라 현재는 문제가 없다. 기록이 크게 늘면 `answered_at`, `recorded_at`에 인덱스를 검토한다.

## 10. 확인 필요 사항

| ID | 내용 | 현재 동작 | 제안 |
|----|------|-----------|------|
| DQ-01 | 단어 중복 기준 불일치 | CSV 검사는 대소문자 무시, DB UNIQUE는 대소문자 구분 | 대소문자 무시로 통일 (현황분석 D-05) |
| DQ-02 | 스키마 버전 관리 없음 | 테이블 생성만 있음 | `PRAGMA user_version` 기반 마이그레이션 도입 (1차 컬럼 추가 전) |
| DQ-03 | 중단된 시험 기록 | 마지막 문항 전에 종료하면 `finished_at`이 NULL로 남음 | 이력에 "미완료"로 표시할지 결정 (D-06) |
