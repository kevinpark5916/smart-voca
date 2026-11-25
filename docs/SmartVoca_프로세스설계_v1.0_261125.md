# 프로세스 설계서 (Process Logic)

**파일 위치**: `docs/SmartVoca_프로세스설계_v1.0_261125.md` (정본, 2026-11-25 승인)
**작성일**: 2026-11-25
**버전**: v1.0
**설명**: 암기 일차, 가중치 출제, 문항 구성, 채점, 연속 학습일, 보고서 집계 등 핵심 로직의 단계와 규칙을 현재 코드 기준으로 정의한다.

---

## 0. 표기 규칙

- 각 항목은 **PL-XX**로 번호를 붙인다. 관련 요구사항(FR), 결정 기록(DR), 테스트 함수를 함께 적는다.
- 아래 내용은 `src/` 코드를 읽어 정리한 것이다. 코드와 다르면 코드가 기준이며, 이 문서를 고친다.
- 설정 기본값은 `데이터 설계서 §7`을 따른다.

---

## PL-01. 단어 CSV 검증과 적재 (FR-01, FR-02)

**입력**: CSV 파일 경로. 인코딩은 `utf-8-sig`(BOM 자동 제거).

**단계**
1. 헤더에 `id, word, pos, meaning, example, level`이 모두 있는지 본다. 하나라도 없으면 오류 한 건만 돌려주고 종료한다.
2. 각 행을 읽는다 (행 번호는 헤더 다음부터 2).
3. 행 검증
   - `word, pos, meaning, example`은 공백 제거 후 비어 있으면 오류.
   - `id`, `level`은 정수여야 한다.
   - `word`는 소문자로 바꾼 값이 이미 나왔으면 "중복 단어" 오류 (대소문자 무시. DB 기준과 다름, 데이터 설계서 DQ-01 참조).
4. 오류 행은 건너뛰고 `"행번호: 사유"` 문자열을 목록에 넣는다.
5. 검증을 통과한 단어만 `WordRepository.upsert_many()`로 저장한다 (id 기준 갱신 또는 추가). 저장은 한 트랜잭션이다 (DI-08).

**출력**: (저장 개수, 오류 목록)

**예외**
- DB 저장 중 `IntegrityError`(예: 다른 id가 같은 word를 가짐)가 나면 **이번 불러오기 전체가 취소**되고 오류 한 건이 추가된다.
- 저장소 쪽 CSV 내보내기(`save_words_to_csv`)는 UTF-8 BOM으로 쓴다 (엑셀 호환).

**관련**: DR-02, DR-11 (원본 파일 보호). 테스트: `test_word_csv.py` 6개.

---

## PL-02. 최초 실행 시 기본 단어 적재 (FR-01)

**조건**: 단어 테이블이 비어 있고 기본 CSV가 있을 때만 실행.

**단계**: PL-01을 기본 CSV에 대해 실행한다. 결과 메시지를 상태 표시줄 또는 콘솔에 보여 준다.

**관련**: `AppContext.load_default_words_if_empty()`. 테스트: `test_word_csv.py::test_project_word_list_is_valid`.

---

## PL-03. 일차별 암기 목록 생성 (FR-04, DR-06)

**입력**: 단어 전체, 일차 번호(day_no ≥ 1), 설정, 직전 세션의 '다시' 단어 id 목록.

**단계**
1. 단어를 `id` 오름차순으로 정렬한다.
2. 신규 단어: 인덱스 `(day_no - 1) × N` 부터 N개를 뽑는다. N은 `daily_new_count`.
3. 복습 단어: 직전 '다시' 목록을 앞에서부터 보며 다음 조건을 모두 만족하는 단어만 담는다.
   - 신규 목록에 이미 있으면 뺀다 (중복 방지).
   - 단어 테이블에 없는 id는 무시한다.
   - 담은 개수가 `daily_review_count`(M)에 이르면 멈춘다.
4. 결과 = 복습 카드(`kind=review`) 목록 + 신규 카드(`kind=new`) 목록. 복습이 앞이다.

**예외**: day_no < 1이면 `ValueError`.

**관련**: 테스트 `test_study_plan.py` 7개 (`test_review_words_come_first_and_are_capped` 등).

---

## PL-04. 암기 세션 시작·이어 하기 (FR-04, DR-08, DR-14)

**입력**: 현재 시각, 설정, DB 상태.

**단계**
1. 끝나지 않은 세션(`finished_at IS NULL`)이 있으면 그 세션을 **이어 한다**. 새 일차를 만들지 않는다.
2. 없으면 다음 일차를 계산한다: `day_no = 마지막 일차 + 1` (세션이 없으면 1).
3. 이미 전체 단어를 다 본 경우(`(day_no - 1) × N ≥ 전체 단어 수`)는 `None`을 돌려준다. 화면은 "모두 외움"을 표시한다.
4. 직전 **완료된** 세션을 찾고, 그 세션의 '다시' 단어를 복습 목록으로 쓴다 (PL-03).
5. 계획을 세션과 카드로 한 번에 저장하고, 세션을 불러와 돌려준다.

**자동 전환 없음**: 세션이 끝나도 다음 일차를 자동으로 만들지 않는다. 사용자가 "다음 일차 시작" 버튼을 누를 때만 4~5단계가 실행된다 (DR-14).

**관련**: 테스트 `test_services_storage.py`의 `test_day_one_then_day_two_with_review`, `test_unfinished_session_resumes_instead_of_starting_new_day`, `test_no_session_after_all_words_are_studied`.

---

## PL-05. 카드 응답과 세션 완료 (FR-03)

**입력**: 세션, 답할 카드(첫 미응답 카드), 결과(`know` 또는 `again`).

**단계**
1. 결과 값이 `know` 또는 `again`인지 검사한다. 아니면 400 오류 (웹 API).
2. 세션에서 첫 미응답 카드의 `result`, `recorded_at`을 저장한다.
3. 모든 카드가 응답되었으면 세션의 `finished_at`을 기록한다.
4. 갱신된 세션을 돌려준다.

**규칙**: 카드는 순서대로만 답한다. 화면에서 뒤집기 전에는 답을 받지 않는다 (데스크톱·웹 모두 적용).

**결과 의미**
- `know`: 알았음
- `again`: 다시 보기 · 내일 복습. 같은 날 다시 나오지 않는다 (DR-15). 다음 일차 계획의 복습 목록이 된다 (PL-03).

**관련**: 테스트 `test_study_view_flips_and_records_cards`, `test_web_api.py::test_study_start_creates_new_day_and_answers_in_order`.

---

## PL-06. 되돌리기 (DR-13)

**단계**
1. 세션에서 응답된 카드 중 **마지막** 카드를 찾는다. 없으면 아무 일도 하지 않는다.
2. 그 카드의 `result`, `recorded_at`을 NULL로 바꾼다.
3. 세션이 끝난 상태였으면 `finished_at`을 NULL로 바꿔 다시 연다.

**범위**: 현재 세션의 마지막 응답 한 건만. 이전 일차 기록은 건드리지 않는다.

**관련**: 테스트 `test_undo_reopens_finished_session_and_clears_last_answer`, `test_undo_on_fresh_session_does_nothing`.

---

## PL-07. 연속 학습일 (FR-17 일부, 2차 항목 선구현)

**입력**: 학습 기록이 있는 날짜 목록(`YYYY-MM-DD`), 오늘 날짜.

**단계**
1. 오늘 학습 기록이 있으면 오늘부터, 없으면 어제부터 거꾸로 센다.
2. 날짜가 목록에 있는 동안 1씩 더한다. 처음으로 없는 날에서 멈춘다.
3. 결과가 연속 학습일 수다 (0일 이상).

**관련**: `src/study/streak.py`. 테스트 `test_ui_upgrade.py::test_streak_counts_back_from_today_or_yesterday`.

---

## PL-08. 출제 가중치 (FR-05, DR-03, DR-09)

**식**

```
이력 없음:  w = 1 + W_NEW
이력 있음:  w = 1
             + W_OLD            (마지막 응답 후 OLD_DAYS일 이상 지남, 또는 마지막 응답 시각 없음)
             + W_WRONG × 오답률  (오답률 = 오답 수 / 응답 수)
```

**기본값**: W_NEW = 3, W_OLD = 2, OLD_DAYS = 7, W_WRONG = 4.

**계산 예시**

| 상황 | 계산 | 가중치 |
|------|------|--------|
| 한 번도 안 본 단어 | 1 + 3 | 4.0 |
| 오늘 본 단어, 전부 정답 | 1 | 1.0 |
| 오늘 본 단어, 1번 중 1번 오답 | 1 + 4 × 1.0 | 5.0 |
| 10일 전에 4번 중 2번 오답 | 1 + 2 + 4 × 0.5 | 5.0 |

**규칙**
- 이력 없는 단어에는 W_OLD를 더하지 않는다 (DR-09).
- 오답률은 해당 단어의 전체 응답 기준이다. 시험 종류와 무관하다.

**관련**: `src/quiz/weighting.py::compute_word_weight`. 테스트 `test_weighting.py` 8개 (가중치 관련 4개 + 선택 관련 4개).

---

## PL-09. 가중 무작위 선택 (FR-05)

**입력**: (단어, 가중치) 목록, 뽑을 개수 count, 난수 생성기.

**단계** (비복원 추출, 룰렛 방식)
1. 남은 풀의 가중치 합 T를 구한다.
2. [0, T) 사이 난수 r을 뽑는다.
3. 누적 합이 r을 넘는 첫 단어를 고른다. 고른 단어는 풀에서 뺀다.
4. count개를 뽑거나 풀이 빌 때까지 반복한다.

**규칙**: 같은 시험에서 같은 단어는 두 번 나오지 않는다. 풀 크기보다 많이 요청하면 풀 크기만큼만 뽑는다.

**관련**: `pick_weighted_words`. 테스트 `test_pick_returns_distinct_words_up_to_count`, `test_heavy_weight_is_picked_much_more_often`.

---

## PL-10. 시험 생성 (FR-05, FR-06)

**입력**: 문제 수, 방향, 유형, 현재 시각.

**단계**
1. 전체 단어와 단어별 시험 통계(응답 수, 오답 수, 마지막 응답 시각)를 읽는다.
2. 단어마다 PL-08로 가중치를 계산한다.
3. PL-09로 문제 수만큼 단어를 뽑는다.
4. 뽑힌 단어마다 PL-11로 문항을 만든다.
5. 시험 세션(`quiz_session`)을 저장하고, 진행 중 시험 객체를 돌려준다.

**검사**: 4지선다가 필요한 유형(`choice`, `mixed`)은 단어가 4개 이상이어야 한다. 부족하면 `ValueError`.

**관련**: 테스트 `test_quiz_run_is_weighted_graded_and_stored`, `test_choice_quiz_needs_at_least_four_words`, `test_weights_push_wrong_words_into_next_quiz`.

---

## PL-11. 문항 구성 (FR-06, DR-10)

**혼합 해소**
- 방향이 `mixed`면 `ko_en` 또는 `en_ko`를 무작위로 고른다.
- 유형이 `mixed`면 `short`, `choice`, `ox` 중 무작위로 고른다.

**방향별 질문과 정답**

| 방향 | 문제(prompt) | 정답(expected) |
|------|--------------|----------------|
| ko_en (한→영) | 뜻 | 영단어 |
| en_ko (영→한) | 영단어 | 뜻 |

**유형별 구성**

| 유형 | 구성 규칙 |
|------|-----------|
| short (단답형) | 정답 목록(accepted)을 만든다. 영→한이면 뜻을 쉼표로 나눈 각 항목과 괄호를 뗀 형태까지 정답이다. 한→영이면 영단어 하나다. |
| choice (4지선다) | 정답 1개 + 다른 단어의 답 3개. 정답 문자열과 같은 답을 가진 단어는 제외한다. 보기 순서는 섞는다. 후보가 부족하면 있는 만큼만 쓴다. |
| ox (OX) | 50%는 정답 짝을 보여 주고 정답 `O`. 50%는 다른 단어의 짝을 보여 주고 정답 `X`. 다른 단어가 없으면 정답 짝을 보여 준다. |

**관련**: `src/quiz/question_builder.py`. 테스트 `test_quiz_grading.py` 중 문항 구성 관련 테스트 (`test_choice_*`, `test_ox_*`, `test_mixed_*`, `test_ko_en_*`).

---

## PL-12. 채점 (FR-07, DR-04)

**정규화**: 앞뒤 공백 제거, 소문자 변환, 연속 공백을 한 칸으로 줄인다.

| 유형 | 판정 |
|------|------|
| short | 정규화한 답이 정답 목록 중 하나와 같으면 정답. 빈 답은 오답. |
| choice | 고른 보기가 정답 보기와 **문자열로 같으면** 정답. |
| ox | 입력을 대문자로 바꾼 값이 `O` 또는 `X`와 같으면 정답. |

**저장**: 문항마다 바로 `quiz_answer`에 저장한다 (정답 여부, 입력 답, 스냅샷 prompt·expected).

**관련**: `src/quiz/grader.py`. 테스트 `test_quiz_grading.py` 전체.

**1차 변경 예정**: FR-10 편집 거리 허용 (단어 길이 5자 이상, 거리 1). 자세한 내용은 구현 계획서를 본다.

---

## PL-13. 시험 세션 생명주기 (FR-07, FR-12)

```
생성 (PL-10) → 문항 1..N 순서로 채점 (PL-12) → 마지막 문항 채점 시 finished_at 기록 → 결과 요약 (FR-12)
```

**규칙**
- 문항은 한 번만 답할 수 있다. 이미 답한 문항에 다시 답하면 `ValueError`.
- 진행 중 시험 객체는 메모리에 있다 (데스크톱: 화면 객체, 웹: `app.config["QUIZ_RUNS"]`). 프로그램을 끄면 사라진다. 이미 채점한 문항은 DB에 남는다.
- 중간에 종료한 시험은 `finished_at`이 NULL로 남는다 (DQ-03, 결정 필요).

**결과 요약 (FR-12)**: 정답 수, 문항 수, 정답률, 틀린 단어 목록. 틀린 단어만 다시 시험할 수 있다 (PL-14).

---

## PL-14. 틀린 단어만 재시험 (FR-12)

**단계**
1. 현재 시험 객체에서 채점 결과가 오답(`False`)인 문항의 단어를 모은다.
2. 한 개도 없으면 `ValueError("틀린 단어가 없습니다")`.
3. 모은 단어로 PL-10과 같은 방식으로 새 시험 세션을 만든다. 방향과 유형은 새 설정을 쓴다.

**관련**: 테스트 `test_retry_run_contains_only_wrong_words`, `test_retry_disabled_when_everything_correct`, `test_web_api.py::test_quiz_full_run_summarises_wrong_answers_and_retries_them`.

---

## PL-15. 기간 보고서 집계 (FR-08)

**입력**: 시작일, 종료일(양 끝 포함), 상위 개수(기본 10).

**집계 항목**

| 항목 | 계산 |
|------|------|
| 학습 일수 | 기간 안에 `recorded_at`이 있는 서로 다른 날짜 수 |
| 암기한 단어 수 | 기간 안에 응답한 서로 다른 단어 수 |
| 시험 횟수 | 기간 안에 시작한 시험 세션 수 |
| 응답 수, 정답 수 | 기간 안의 `quiz_answer` 행 수, 정답 합 |
| 평균 정답률 | 정답 수 ÷ 응답 수 (응답이 없으면 0) |
| 자주 틀린 단어 TOP N | 기간 안에서 오답이 1 이상인 단어를 오답 수 내림차순, 같으면 응답 수 오름차순으로 N개 |

**저장**: HTML 파일을 `reports/report_시작일_종료일_시분초.html`로 저장한다. 파일 이름에 시각을 넣어 덮어쓰지 않는다. HTML 안의 단어는 이스케이프한다.

**관련**: `src/report/report_data.py`, `report_builder.py`. 테스트 `test_report_summary_counts_study_and_quiz`, `test_report_html_is_written_and_escapes_text`, `test_report_download_writes_html_file`.

---

## PL-16. 설정 검증 (FR-13)

- 저장 전과 읽은 후 모두 `Settings.validate()`를 실행한다.
- 범위 위반은 `ValueError`로 거부하고 파일을 쓰지 않는다. 범위는 `데이터 설계서 §7`과 같다.
- 웹 설정 저장 API는 받은 키만 덮어쓰고, 나머지는 현재 값을 유지한다.

**관련**: 테스트 `test_settings_round_trip_and_validation`, `test_settings_save_and_validation`.

---

## PL-17. 웹 응답 노출 규칙

- 시험 문항 조회 응답에는 정답(`expected`)과 인정 답(`accepted`)을 넣지 않는다. 답한 뒤 채점 응답에서만 정답을 보여 준다.
- 암기 카드 응답에는 뜻과 예문을 넣되, 뒤집기 전 답 입력은 서버가 막는다.

**관련**: 테스트 `test_quiz_questions_hide_expected_answers_until_submitted`.

---

## 확인 필요 사항

| ID | 내용 | 현재 동작 | 관련 |
|----|------|-----------|------|
| PQ-01 | FR-04 "직전 학습일"의 해석 | 직전 **완료된** 세션의 '다시' 단어를 쓴다 | 현황분석 D-04 |
| PQ-02 | 중단된 시험의 처리 | 기록은 남고 `finished_at`은 NULL | 현황분석 D-06 |
| PQ-03 | 채점 정답 목록에 괄호 제거형 포함 | "만(灣)" 정답은 "만"도 인정 (FR-07 취지에 맞음) | 확인만 필요 |
