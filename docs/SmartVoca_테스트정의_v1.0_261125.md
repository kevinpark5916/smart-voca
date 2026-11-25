# 테스트 정의서 (Test Specification)

**파일 위치**: `docs/SmartVoca_테스트정의_v1.0_261125.md` (정본, 2026-11-25 승인)
**작성일**: 2026-11-25
**버전**: v1.0
**설명**: 요구사항별 BDD 시나리오, 자동 테스트와 현재 테스트 함수의 대응, 수동 테스트 체크리스트, 미구현 기능의 테스트 계획을 정의한다 (방법론 §2.4, NFR-06).

---

## 1. 목적과 범위

- 요구사항 ID(FR, NFR)별로 **Given / When / Then** 시나리오를 정하고, 각 시나리오가 자동 테스트인지 수동 테스트인지 표시한다.
- 대상: MVP(FR-01 ~ FR-08, FR-13), 웹 버전(DR-17), 일부 2차 선구현(FR-17 연속 학습일).
- 이 문서는 **현재 구현된 기능**을 기준으로 한다. 미구현 기능(FR-09 ~ FR-11, FR-14 ~ FR-20 등)은 §6에 계획만 적는다.

## 2. 실행 방법

| 항목 | 내용 |
|------|------|
| 전체 실행 | `python -m pytest` (프로젝트 루트) |
| 화면 테스트 | 테스트 안에서 `QT_QPA_PLATFORM=offscreen`으로 실행 (화면이 뜨지 않음) |
| 웹 테스트 | Flask 테스트 클라이언트, 임시 DB 사용 |
| 임시 데이터 | DB를 쓰는 테스트는 pytest `tmp_path`(임시 폴더)를 쓴다. 실제 DB 경로는 참조하지 않는다. `tests/conftest.py`는 샘플 단어 픽스처(`sample_words`, id 1~30)와 `make_word()`를 제공한다 |
| 실제 단어 검사 | `test_word_csv.py::test_project_word_list_is_valid`가 `data/words.csv`를 읽어 2000행과 형식을 확인 |

**최근 실행 결과**: 2026-11-25에 `python -m pytest` 실행, **81 passed** (9.74초).

## 3. 테스트 레벨

| 레벨 | 대상 | 도구 |
|------|------|------|
| 단위 | 가중치, 채점, 문항 구성, 일차 계획, CSV, 설정, 연속 학습일 | pytest |
| 통합 | 서비스 + 저장소 + 임시 DB | pytest |
| 웹 API | 블루프린트 + Flask 테스트 클라이언트 | pytest |
| 화면 스모크 | PyQt 위젯 생성과 키 입력 (offscreen) | pytest-qt 없이 `QApplication` 직접 사용 |
| 수동 | 실제 창과 브라우저에서 사람이 조작 | 체크리스트 (§5) |

## 4. BDD 시나리오와 자동 테스트 대응

### 4.1 단어 데이터 (FR-01, FR-02)

| 시나리오 ID | Given / When / Then | 자동 테스트 | 상태 |
|-------------|---------------------|-------------|------|
| TS-01-1 | Given 정상 CSV, When 불러오면, Then 모든 행이 Word로 읽힌다 | `test_word_csv.py::test_load_valid_rows` | 자동 |
| TS-01-2 | Given 원본 `data/words.csv`, When 검사하면, Then 2000행, id 중복 없음 | `test_word_csv.py::test_project_word_list_is_valid` | 자동 |
| TS-02-1 | Given 잘못된 행이 섞인 CSV, When 불러오면, Then 잘못된 행은 건너뛰고 행 번호와 사유를 돌려준다 | `test_word_csv.py::test_bad_rows_are_skipped_with_line_numbers` | 자동 |
| TS-02-2 | Given 필수 컬럼이 없는 CSV, When 불러오면, Then 오류 한 건만 돌려준다 | `test_word_csv.py::test_missing_column_returns_single_error` | 자동 |
| TS-02-3 | Given 단어를 저장한 뒤, When 다시 읽으면, Then 내용이 같다 | `test_word_csv.py::test_save_then_load_round_trip` | 자동 |
| TS-02-4 | Given 내보낸 파일, When 엑셀이 열면, Then UTF-8 BOM이 붙어 있다 | `test_word_csv.py::test_saved_file_has_bom_for_excel` | 자동 |
| TS-02-5 | Given 웹에서 CSV 업로드, When 가져오면, Then 유효한 행만 저장되고 오류 목록이 온다 | `test_web_api.py::test_words_import_reports_errors_and_saves_valid_rows` | 자동 |
| TS-02-6 | Given 웹 내보내기, When 요청하면, Then 헤더가 있는 CSV가 내려온다 | `test_web_api.py::test_words_export_returns_csv_with_header` | 자동 |
| TS-02-7 | Given 단어가 많을 때, When 목록을 새로 고치면, Then 1초 안에 표시된다 (NFR-03) | `test_ui_smoke.py::test_word_list_refresh_is_fast_with_all_words` | 자동 |
| TS-02-8 | Given 단어 목록 탭, When 검색어를 넣으면, Then 행이 걸러진다 | `test_ui_upgrade.py::test_word_search_filters_rows`, `test_web_api.py::test_word_search_matches_word_and_meaning` | 자동 |
| TS-02-9 | Given 단어 목록 탭, When id로 정렬하면, Then 숫자 순서다 (문자열 순서가 아님) | `test_ui_upgrade.py::test_word_sort_key_sorts_ids_numerically` | 자동 |

### 4.2 암기 (FR-03, FR-04)

| 시나리오 ID | Given / When / Then | 자동 테스트 | 상태 |
|-------------|---------------------|-------------|------|
| TS-03-1 | Given 1일차 목록, When 카드를 순서대로 답하면, Then 세션이 끝나고 `finished_at`이 기록된다 | `test_web_api.py::test_study_start_creates_new_day_and_answers_in_order`, `test_services_storage.py::test_day_one_then_day_two_with_review` | 자동 |
| TS-03-2 | Given 뒤집기 전, When 알았음을 누르면, Then 응답이 무시된다 | `test_ui_smoke.py::test_study_view_blocks_answer_before_flip_and_supports_undo` | 자동 |
| TS-03-3 | Given 카드 화면, When Space, 1, 2, Backspace, Enter를 누르면, Then 단축키대로 동작한다 | `test_ui_smoke.py::test_shortcuts_work_from_main_window_key_events`, `test_backspace_and_enter_answer_cards` | 자동 |
| TS-03-4 | Given 응답한 카드, When 되돌리기를 하면, Then 마지막 응답만 지워진다 | `test_web_api.py::test_study_undo_reopens_last_answer`, `test_services_storage.py::test_undo_reopens_finished_session_and_clears_last_answer` | 자동 |
| TS-03-5 | Given 응답이 없는 새 세션, When 되돌리기를 하면, Then 아무 일도 없다 | `test_services_storage.py::test_undo_on_fresh_session_does_nothing` | 자동 |
| TS-03-6 | Given 답하지 않은 "다시" 카드가 있는 상태에서 앱을 껐다 켜면, When 시작하면, Then 같은 세션을 이어 한다 | `test_services_storage.py::test_unfinished_session_resumes_instead_of_starting_new_day` | 자동 |
| TS-03-7 | Given 세션이 끝났을 때, When 화면을 보면, Then "다음 일차 시작" 버튼이 보인다 (자동 전환 없음) | `test_ui_smoke.py::test_next_day_button_appears_after_day_is_finished`, `test_services_storage.py::test_next_day_starts_only_after_finish_is_confirmed` | 자동 |
| TS-04-1 | Given 1일차, When 목록을 만들면, Then id 1~N번 단어 | `test_study_plan.py::test_day_one_takes_first_n_words_by_id` | 자동 |
| TS-04-2 | Given 2일차, When 목록을 만들면, Then N+1~2N번 단어 | `test_study_plan.py::test_day_two_continues_from_next_block` | 자동 |
| TS-04-3 | Given "다시" 단어가 많음, When 목록을 만들면, Then 복습 단어는 앞에, 최대 M개 | `test_study_plan.py::test_review_words_come_first_and_are_capped` | 자동 |
| TS-04-4 | Given 복습 단어가 오늘 신규에도 있음, When 목록을 만들면, Then 중복되지 않음 | `test_study_plan.py::test_review_word_already_in_today_new_block_is_not_duplicated` | 자동 |
| TS-04-5 | Given 모든 단어를 외움, When 다음 일차를 요청하면, Then 세션이 없다 | `test_services_storage.py::test_no_session_after_all_words_are_studied` | 자동 |
| TS-04-6 | Given 일차 0 또는 음수, When 목록을 만들면, Then 오류 | `test_study_plan.py::test_day_must_be_positive` | 자동 |
| TS-04-7 | Given 홈 화면, When 열면, Then 오늘 일차, 전체 진도, 연속 학습일이 보인다 | `test_web_api.py::test_home_reports_total_and_first_day`, `test_ui_upgrade.py::test_home_view_shows_plan_and_navigates` | 자동 |
| TS-17-1 | Given 학습 기록이 있는 날짜들, When 연속 학습일을 계산하면, Then 오늘 또는 어제부터 거꾸로 센 값 | `test_ui_upgrade.py::test_streak_counts_back_from_today_or_yesterday` | 자동 |

### 4.3 시험 (FR-05, FR-06, FR-07, FR-12)

| 시나리오 ID | Given / When / Then | 자동 테스트 | 상태 |
|-------------|---------------------|-------------|------|
| TS-05-1 | Given 이력 없는 단어, When 가중치를 계산하면, Then 1 + W_NEW | `test_weighting.py::test_unseen_word_gets_new_bonus_only` | 자동 |
| TS-05-2 | Given 방금 본 단어, 전부 정답, When 가중치를 계산하면, Then 1 | `test_weighting.py::test_recent_word_with_no_wrong_answers_has_base_weight` | 자동 |
| TS-05-3 | Given 7일 이상 지난 단어, When 가중치를 계산하면, Then W_OLD가 더해진다 | `test_weighting.py::test_old_word_gets_old_bonus` | 자동 |
| TS-05-4 | Given 오답률 50%, When 가중치를 계산하면, Then W_WRONG × 0.5가 더해진다 | `test_weighting.py::test_wrong_rate_adds_weight_proportionally` | 자동 |
| TS-05-5 | Given 설정 값을 바꿈, When 가중치를 계산하면, Then 바뀐 값이 반영된다 | `test_weighting.py::test_weights_follow_settings` | 자동 |
| TS-05-6 | Given 후보 단어, When 뽑으면, Then 중복 없이 요청 수만큼 | `test_weighting.py::test_pick_returns_distinct_words_up_to_count`, `test_pick_never_exceeds_pool_size` | 자동 |
| TS-05-7 | Given 가중치가 큰 단어, When 여러 번 뽑으면, Then 더 자주 뽑힌다 | `test_weighting.py::test_heavy_weight_is_picked_much_more_often` | 자동 |
| TS-05-8 | Given 틀린 단어가 많음, When 다음 시험을 만들면, Then 그 단어들이 더 자주 나온다 | `test_services_storage.py::test_weights_push_wrong_words_into_next_quiz` | 자동 |
| TS-05-9 | Given 시험 생성, When 채점하면, Then 시험 세션과 응답이 DB에 저장된다 | `test_services_storage.py::test_quiz_run_is_weighted_graded_and_stored` | 자동 |
| TS-05-10 | Given 문제 수 범위 밖(4 또는 101), When 웹에서 시험을 만들면, Then 400 | `test_web_api.py::test_quiz_rejects_out_of_range_count_and_bad_options` | 자동 |
| TS-06-1 | Given 혼합 방향, When 문항을 만들면, Then 실제 방향은 한쪽으로 정해진다 | `test_quiz_grading.py::test_mixed_direction_and_type_resolve_to_concrete_values` | 자동 |
| TS-06-2 | Given 영→한 단답, When 문항을 만들면, Then 문제는 영단어, 정답은 뜻 | `test_quiz_grading.py::test_ko_en_prompt_is_meaning_and_answer_is_word` | 자동 |
| TS-06-3 | Given 4지선다, When 문항을 만들면, Then 보기 4개(정답 포함, 중복 없음) | `test_quiz_grading.py::test_choice_has_four_distinct_options_including_answer` | 자동 |
| TS-06-4 | Given 뜻이 같은 다른 단어, When 보기를 만들면, Then 그 단어는 오답 보기에서 빠짐 | `test_quiz_grading.py::test_choice_skips_distractors_with_same_meaning` | 자동 |
| TS-06-5 | Given OX 문항, When 만들면, Then 짝과 정답 O/X가 일치 | `test_quiz_grading.py::test_ox_expected_matches_candidate` | 자동 |
| TS-06-6 | Given 4지선다 단어가 4개 미만, When 시험을 만들면, Then 오류 | `test_services_storage.py::test_choice_quiz_needs_at_least_four_words` | 자동 |
| TS-06-7 | Given 4지선다·OX 설정, When 화면을 열면, Then 보기와 OX가 그려진다 | `test_ui_smoke.py::test_quiz_view_choice_and_ox_modes_render` | 자동 |
| TS-06-8 | Given 키보드 조작, When 4지선다에서 숫자키를 누르면, Then 보기가 선택된다 | `test_ui_upgrade.py::test_keyboard_answers_choice_question` | 자동 |
| TS-07-1 | Given 단답 정답, When 공백·대소문자를 바꿔 입력하면, Then 정답 | `test_quiz_grading.py::test_normalize_trims_case_and_spaces`, `test_short_answer_english_is_case_insensitive` | 자동 |
| TS-07-2 | Given 뜻이 쉼표로 여러 개, When 그중 하나를 쓰면, Then 정답 | `test_quiz_grading.py::test_short_answer_accepts_any_comma_separated_meaning` | 자동 |
| TS-07-3 | Given 괄호 안 표기, When 괄호 없이 쓰면, Then 정답 | `test_quiz_grading.py::test_parenthesis_is_optional_in_short_answer` | 자동 |
| TS-07-4 | Given 빈 답, When 채점하면, Then 오답 | `test_quiz_grading.py::test_empty_short_answer_is_wrong` | 자동 |
| TS-07-5 | Given 웹 시험 진행 중, When 답하기 전 문항을 조회하면, Then 정답은 응답에 없다 | `test_web_api.py::test_quiz_questions_hide_expected_answers_until_submitted` | 자동 |
| TS-07-6 | Given 시험 완료, When 이력을 보면, Then 세션과 문항별 응답이 나온다 | `test_services_storage.py::test_history_queries_return_sessions_and_answers`, `test_web_api.py::test_quiz_history_lists_finished_sessions` | 자동 |
| TS-07-7 | Given 기간 필터, When 이력을 보면, Then 기간 밖 시험은 빠진다 | `test_ui_upgrade.py::test_history_date_range_excludes_sessions_outside` | 자동 |
| TS-07-8 | Given 시험 종료, When 결과 화면을 보면, Then 정답 수, 정답률, 틀린 문항이 있다 | `test_ui_smoke.py::test_history_tab_shows_quiz_after_it_finishes`, `test_web_api.py::test_quiz_full_run_summarises_wrong_answers_and_retries_them` | 자동 |
| TS-12-1 | Given 틀린 문항이 있음, When 틀린 단어만 재시험하면, Then 틀린 단어만 출제 | `test_ui_upgrade.py::test_retry_run_contains_only_wrong_words` | 자동 |
| TS-12-2 | Given 전부 정답, When 재시험을 보면, Then 재시험 버튼이 비활성 | `test_ui_upgrade.py::test_retry_disabled_when_everything_correct` | 자동 |
| TS-06-9 | Given 테마 설정, When 바꾸면, Then 시험 화면 색이 바뀐다 | `test_ui_upgrade.py::test_quiz_theme_palette_switches` | 자동 |

### 4.4 보고서 (FR-08)

| 시나리오 ID | Given / When / Then | 자동 테스트 | 상태 |
|-------------|---------------------|-------------|------|
| TS-08-1 | Given 기간 내 암기와 시험 기록, When 요약을 만들면, Then 학습 일수, 암기 단어 수, 시험 횟수, 정답률이 맞다 | `test_services_storage.py::test_report_summary_counts_study_and_quiz` | 자동 |
| TS-08-2 | Given 오답 단어, When HTML을 만들면, Then TOP 목록과 생성 시각이 있다 | `test_services_storage.py::test_report_html_is_written_and_escapes_text` | 자동 |
| TS-08-3 | Given 단어에 `<script>` 같은 문자, When HTML을 만들면, Then 이스케이프된다 | `test_services_storage.py::test_report_html_is_written_and_escapes_text` | 자동 |
| TS-08-4 | Given 웹에서 기간 없이 요청, When 보고서를 받으면, Then 400 | `test_web_api.py::test_report_requires_dates_and_ordered_range` | 자동 |
| TS-08-5 | Given 웹에서 기간을 지정, When 받으면, Then HTML 파일이 생성되고 내려간다 | `test_web_api.py::test_report_download_writes_html_file` | 자동 |

### 4.5 설정 (FR-13)

| 시나리오 ID | Given / When / Then | 자동 테스트 | 상태 |
|-------------|---------------------|-------------|------|
| TS-13-1 | Given 설정 저장, When 다시 읽으면, Then 같은 값. 범위 밖 값은 거부 | `test_services_storage.py::test_settings_round_trip_and_validation` | 자동 |
| TS-13-2 | Given 웹 설정 화면, When 저장하면, Then 파일에 반영되고 잘못된 값은 400 | `test_web_api.py::test_settings_save_and_validation` | 자동 |

### 4.6 웹 화면과 앱 기동

| 시나리오 ID | Given / When / Then | 자동 테스트 | 상태 |
|-------------|---------------------|-------------|------|
| TS-WEB-1 | Given 서버 실행, When `/`를 열면, Then 화면이 나온다 | `test_web_api.py::test_index_page_is_served` | 자동 |
| TS-UI-1 | Given 앱 실행, When 메인 창이 뜨면, Then 탭 5개가 있다 | `test_ui_smoke.py::test_main_window_builds_with_all_tabs` | 자동 |
| TS-UI-2 | Given 설정 화면, When 글자 크기를 바꾸면, Then 픽셀 크기가 배율대로 바뀐다 | `test_ui_upgrade.py::test_scale_factor_applies_to_pixel_sizes` | 자동 |

### 4.7 자동 테스트 수 요약

| 영역 | 파일 | 테스트 수 |
|------|------|-----------|
| 채점·문항 | `test_quiz_grading.py` | 11 |
| 저장·서비스 | `test_services_storage.py` | 13 |
| 일차 계획 | `test_study_plan.py` | 7 |
| 가중치 | `test_weighting.py` | 8 |
| CSV | `test_word_csv.py` | 6 |
| 화면 스모크 | `test_ui_smoke.py` | 10 |
| 화면 2차 | `test_ui_upgrade.py` | 10 |
| 웹 API | `test_web_api.py` | 16 |
| **합계** | | **81** (실행 결과와 일치) |

> 위 표의 수는 파일별 `def test_` 개수를 센 값이다. 합계 81은 `python -m pytest` 결과와 일치한다.

## 5. 수동 테스트 체크리스트 (미확인 항목)

작업 일지(2026-10-21, 2026-11-04)에 "미확인"으로 남은 항목이다. 사람이 직접 확인하고 결과를 적는다.

| ID | 항목 | 확인 방법 | 결과 | 날짜 |
|----|------|-----------|------|------|
| MT-01 | 데스크톱 한 바퀴 | `python src/main.py` → 암기 1일차 끝까지 → 시험 1회 → 보고서 생성 | 미확인 | |
| MT-02 | 암기 단축키 | Space 뒤집기, 1 다시 보기, 2 알았음, Ctrl+Z 되돌리기 | 미확인 | |
| MT-03 | 암기 버튼 | "다음 일차 시작" 버튼, 되돌리기 버튼 | 미확인 | |
| MT-04 | 이력 탭 | 시험 후 이력 탭 표시, 세션 선택 시 문항 상세 | 미확인 | |
| MT-05 | 단어 목록 새로 고침 | 2000행 상태에서 새로 고침 반응 체감 | 미확인 | |
| MT-06 | 웹 암기 | `python src/run_web.py` → 뒤집기, 알았음·다시, 되돌리기, 완료 후 다음 일차 | 미확인 | |
| MT-07 | 웹 시험 | 출제 → 4지선다·OX 답하기 → 결과 요약 → 틀린 단어 재시험 | 미확인 | |
| MT-08 | 웹 단축키 | 시험과 암기 화면의 키보드 조작 | 미확인 | |
| MT-09 | exe 실행 | 임시 `APPDATA`에서 `dist/SmartVoca.exe` 실행 (배포 정의서 §4) | 일부 확인 (기동만) | 2026-10-21 |
| MT-10 | 다른 PC에서 exe 실행 | Python 미설치 PC에서 실행 | 미확인 | |
| MT-11 | 설정 화면 | 테마 전환, 글자 크기 전환, 저장 후 재시작 유지 | 미확인 | |
| MT-12 | 보고서 열기 | 보고서 대화상자 → HTML 열기 → 표 값 확인 | 미확인 | |

## 6. 미구현 기능의 테스트 계획

1차 기능을 구현할 때 이 계획을 Test Specification에 추가한다.

| 요구사항 | 주요 시나리오 | 테스트 파일 (계획) | 비고 |
|----------|---------------|---------------------|------|
| FR-09 단어 편집 | 추가 시 중복 거부, 수정 후 기존 시험 기록의 스냅샷은 그대로, 삭제 시 기록 참조 처리 | `test_word_edit.py` | 삭제 정책 결정 필요 (구현 계획서 D-02) |
| FR-10 편집 거리 채점 | 길이 5 미만은 허용 안 함, 5 이상 거리 1 허용, 거리 2는 오답 | `test_quiz_grading.py` 추가 | DR-04 |
| FR-11 오답 단어장 | 오답률 50% 이상만 목록, 목록만으로 시험 생성 | `test_wrong_words.py` | 기준값은 설정으로 뺄지 결정 |
| FR-14 TTS | 영어 음성 없으면 버튼 비활성, 있으면 발음 호출 | `test_speech.py` (음성 엔진은 가짜 객체로 대체) | R-2 |
| NFR-04 백업 옵션 | 불러오기 전 백업 파일 생성, 백업에서 원복 | `test_backup.py` | 1차 |
| FR-15 SRS | 정답·오답에 따라 다음 복습 날짜 계산 | `test_srs.py` | 2차, DR-03 재검토 |
| FR-16 듣기 시험 | 발음 → 입력 → 채점 | `test_listening.py` | 2차 |
| FR-17 달력 | 날짜별 학습량 집계 | `test_calendar.py` | 2차 (연속 학습일은 완료) |
| FR-18 Excel | 같은 내용의 xlsx 생성 | `test_excel_report.py` | 2차 |
| FR-19 백업·복원 | 날짜 이름 복사, 복원 후 기록 일치 | `test_backup.py` | 2차 |
| FR-20 시간 제한 | 시간 종료 시 자동 채점, 미답 문항 처리 | `test_timer.py` | 2차 |
| FR-21 알림 | 설정 시각에 알림 | 수동 | 선택 |
| FR-23 exe | 빌드 후 기동, 데이터 경로 APPDATA | 수동 + 스크립트 | 배포 정의서 |

## 7. 완료 기준 (Exit Criteria)

| 단계 | 기준 |
|------|------|
| 기능 구현 완료 | 해당 FR의 시나리오가 모두 자동 또는 수동으로 확인됨. 전체 자동 테스트 통과. |
| 1차 완료 | §6의 1차 항목 테스트 추가, MT-01 ~ MT-08 수동 확인 완료 |
| 배포 전 | MT-09 ~ MT-12 완료, 배포 정의서의 체크리스트 통과 |
| 문서 | 시나리오 ID와 테스트 함수 이름이 맞다. 테스트 추가 시 이 문서를 같이 고친다 (방법론 §3-4). |

## 8. 알려진 테스트 공백

| ID | 공백 | 위험 | 조치 |
|----|------|------|------|
| TG-01 | 한글 CSV에서 엑셀 저장본을 다시 읽는 경로가 실제 엑셀로 검증되지 않음 | 낮음 | 수동 확인 (MT-05 범위 포함) |
| TG-02 | 데스크톱과 웹의 동작 차이를 비교하는 테스트 없음 | 중간 | AQ-04. 수동 비교 항목으로 관리 |
| TG-03 | 설정 파일이 잘못된 타입(문자열 등)일 때 데스크톱 기동 테스트 없음 | 중간 | F-01 수정 시 테스트 추가 |
| TG-04 | 여러 날짜에 걸친 실제 시간 흐름(예: 7일 경과)을 실제 시계 없이 검사하는 테스트가 적음 | 낮음 | `now` 인자를 직접 넣어 검사 중 (가중치 테스트) |
| TG-05 | Python 3.11~3.13 호환 테스트 없음 | 중간 | DR-12 해소 시 추가 (배포 정의서 §6) |
