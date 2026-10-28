# 작업 일지 (Work Log)

**파일 위치**: `ai-agent/claude/SmartVoca_Work_Log_v1.0_261021.md`
**작성일**: 2026-10-21
**버전**: v1.0
**설명**: 2026-10-21 세션에서 수행한 기획, 단어 데이터, MVP 구현 기록

---

## 1. 기획 (Charter, Requirement Spec, Decision Records)

- 요구사항 7개 + 추가 기능 제안 → 우선순위 정리 (MVP / 1차 / 2차 / 선택)
- 기획 문서 3종 초안 작성 (`ai-agent/claude/`, `docs/` 승격은 승인 대기)

## 2. 단어 데이터

- `data/words.csv` 2000행 생성 (`id,word,pos,meaning,example,level`, UTF-8 BOM)
- 작업 원본: `ai-agent/claude/261021_단어데이터/data/part01~08.csv` (part08은 마지막 8행 미사용)
- 검토 결과
  - 형식: 2000행, 중복 없음, 필드 누락 없음, id 1~2000 연속
  - 예문에 표제어 포함 여부: 불규칙 활용형 11건은 정상, `motion` 예문 1건 수정
  - 무작위 샘플 60행 직접 확인: 뜻과 예문 일치
  - 전체 2000행의 뜻·예문 의미 검토는 하지 않음 (사용자 확인 필요)

## 3. MVP 구현

- 환경: Python 3.15.0, PyQt6 6.11.0, pytest 9.1.1
- 구현 파일
  - 데이터: `src/models/`, `src/storage/` (word, study, quiz 저장소, CSV, DB 스키마)
  - 로직: `src/study/study_plan.py`, `src/quiz/` (가중치, 문항 생성, 채점)
  - 서비스: `src/services/` (암기 흐름, 시험 흐름)
  - 보고서: `src/report/` (요약 계산, HTML 저장)
  - 설정·조립: `src/config/settings.py`, `src/app_context.py`, `src/paths.py`
  - 화면: `src/ui/` (메인 창, 암기, 시험, 단어 목록, 설정, 보고서), `src/main.py`
- 테스트 (`tests/`)
  - 단위·통합 41개: CSV, 일차 목록, 가중치, 문항·채점, 저장소·서비스, 보고서, 설정
  - 화면 스모크 4개: 창 구성, 암기 카드, 단답 시험, 4지선다·OX 렌더링
  - 결과: 45개 모두 통과 (`python -m pytest`)
- 실행 확인: `python src/main.py`가 오류 없이 시작되고, 첫 실행 시 단어 2000개를 DB로 가져옴
- 파일 줄 수: 모든 파일 500줄 이하 (최대 `src/ui/quiz_view.py` 209줄)

## 4. 미완료 / 다음 작업

- 실제 화면을 사람이 직접 조작하는 수동 테스트 (암기 → 시험 → 보고서 한 바퀴)
- Test Specification 문서 작성 (방법론 §2.4)
- git 초기화와 첫 커밋 (승인 대기)
- README.md 작성
- 단어 뜻·예문 전체 검토 (사용자)
- DR-12: Python 버전 재검토 (3.12 또는 3.13 검토)

## 5. exe 빌드 (FR-23)

- 도구: PyInstaller 6.22.3 (`ai-agent/scripts/build_exe.py`, `--onefile --windowed`)
- 결과: `dist/SmartVoca.exe` (약 39MB)
- 경로 분리 (DR-07 구현): exe로 실행하면 DB, 설정, 보고서를 `%APPDATA%\SmartVoca\`에 저장하고, 기본 단어 CSV는 exe 안에 포함한다. 개발 실행은 기존처럼 `data/`를 쓴다.
- 확인: 임시 APPDATA로 실행 → 오류 없이 시작, DB에 단어 2000개 적재
- 미확인: 실제 화면 조작, 다른 PC(파이썬 미설치 환경)에서의 실행

## 6. 암기 화면 개선 (검토 후속 작업)

- 되돌리기: 마지막 응답 하나를 취소 (`StudyRepository.clear_result`, `reopen_session`, `StudyService.undo_last`). DR-13
- 다음 일차 시작 버튼: 세션이 끝나면 표시. 앱 재시작 없이 다음 일차 시작 가능. DR-14
- 단축키: Space 뒤집기, 1 다시 보기, 2 알았음, Ctrl+Z 되돌리기
- 라벨: "다시" → "다시 보기 · 내일 복습". DR-15
- 뒤집기 전에는 답 입력을 무시 (버튼뿐 아니라 단축키도)
- 테스트: 50개 통과. exe 재빌드 완료.
- 미확인: 실제 화면에서 단축키와 버튼 조작 (수동)

## 7. 이력 탭 추가, 단어 목록 응답 없음 수정

- 이력 탭: 시험 이력(세션 목록, 선택 시 문항별 응답)과 암기 이력(일차별 요약). 이력 탭을 열 때마다 새로 읽는다.
- 저장소: `QuizRepository.list_sessions`, `session_answers`, `StudyRepository.list_sessions` 추가
- 응답 없음 원인: QTableWidget에 칸마다 항목을 넣고 열 너비를 내용에 맞춤 → QTableView + 모델로 교체 (DR-16)
- 테스트: 54개 통과
- exe: `dist/SmartVoca.exe` 재빌드 (임시 APPDATA로 기동 확인)
- 미확인: 실제 화면에서 이력 탭과 단어 목록 새로고침 (수동)
