# 배포 정의서 (Deployment Spec)

**파일 위치**: `docs/SmartVoca_배포정의_v1.0_261125.md` (정본, 2026-11-25 승인)
**작성일**: 2026-11-25
**버전**: v1.0
**설명**: 소스 관리(Git), 실행 형태, exe 빌드 절차, 데이터 경로, 배포 전 체크리스트, 배포 전 게이트(라이선스, Python 버전)를 정의한다. Charter §6에서 "2차 (exe 배포 시) 작성"으로 계획했으나, exe가 이미 만들어졌으므로 지금 작성한다.

---

## 1. 배포 대상과 형태

| 형태 | 명령 또는 산출물 | 대상 | 상태 |
|------|------------------|------|------|
| 데스크톱 개발 실행 | `python src/main.py` | 개발자 PC | 사용 중 |
| 웹 개발 실행 | `python src/run_web.py` → `http://127.0.0.1:5000` | 개발자 PC | 사용 중 |
| 데스크톱 exe | `dist/SmartVoca.exe` (단일 파일, 약 39MB) | 사용자 PC | 빌드됨 (2026-10-21), **재빌드 필요** |

- 웹 버전은 exe에 포함하지 않는다. Python이 있는 PC에서 `run_web.py`로 실행한다 (DR-17).
- 배포 대상은 사용자 개인 PC 1대다 (Charter A-1). 서버 배포는 없다.

## 2. 소스 관리 (형상 관리)

| 항목 | 규칙 |
|------|------|
| 저장소 | Git, 원격 `https://github.com/kevinpark5916/smart-voca` (private) |
| 기본 브랜치 | `main`. 현재 브랜치 정책은 단일 브랜치 |
| 커밋 메시지 | Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) |
| 추적 ID | 기능 커밋은 FR/NFR ID를 넣는다 (NFR-08). 예: `feat: 단어 편집 추가 (FR-09)` |
| 커밋 크기 | 한 커밋에 한 가지 일만 담는다 (CLAUDE.md Git 규칙 2) |
| 커밋·푸시 | 사용자 승인 후에만 한다 (CLAUDE.md Git 규칙 3) |
| 제외 대상 | `data/*.db`, `data/backups/`, `build/`, `dist/`, `dist_new/`, `__pycache__/`, `.pytest_cache/`, `.env` |
| 추적 대상 | 소스, 테스트, 문서, `data/words.csv`, `requirements.txt`, `ai-agent/scripts/build_exe.py` |

### 2.1 문서 버전 관리

- 승인된 산출물은 `docs/`에 둔다. Claude는 `docs/`를 직접 고치지 않는다 (CLAUDE.md 문서 규칙 5).
- 버전을 올릴 때: `git mv docs/파일명 docs/old/파일명` → `cp`로 새 이름 복사 → 새 내용 수정.
- 파일명: `SmartVoca_{명칭}_v{X.X}_{YYMMDD}.md`. 명칭은 방법론 §2 산출물 이름을 쓰며, 이번 문서들은 한글 명칭을 썼다 (기본안, 현황분석 D-01에서 확인 필요).

## 3. 실행 환경

| 항목 | 값 | 근거 |
|------|----|------|
| 운영체제 | Windows 10/11 | C-1, NFR-01 |
| Python (개발 기준) | 3.15.0 | DR-12 |
| Python (최소) | 3.11 | C-1 |
| Python (권장 검토) | 3.12 또는 3.13 | DR-12 재검토 항목 |
| 패키지 | `requirements.txt` (PyQt6, flask, pytest, pyinstaller) | 설치 명령: `python -m pip install -r requirements.txt` |
| 네트워크 | 불필요 (웹은 127.0.0.1만 사용) | C-2, NFR-02 |

## 4. exe 빌드 절차

### 4.1 전제

- `data/words.csv`가 있어야 한다. 없으면 빌드 스크립트가 중단한다.
- 빌드 전에 `python -m pytest`가 모두 통과해야 한다.

### 4.2 절차

| 단계 | 명령 또는 작업 | 확인 |
|------|----------------|------|
| 1 | `python -m pytest` | 모든 테스트 통과 (현재 81개) |
| 2 | `python ai-agent/scripts/build_exe.py` | 종료 코드 0, "빌드 완료" 출력 |
| 3 | `dist/SmartVoca.exe` 크기 확인 | 약 39MB 전후 |
| 4 | 임시 APPDATA로 실행 (아래 §4.3) | 오류 없이 창이 뜸, DB에 단어 2000개 |
| 5 | 수동 확인 MT-09 (테스트 정의서 §5) | 결과 기록 |
| 6 | 버전 태그 또는 빌드 기록 (§7) | 승인 후 |

### 4.3 임시 APPDATA 기동 확인 (데이터 보호)

실제 사용자 데이터를 건드리지 않도록 임시 폴더를 쓴다.

```
PowerShell:
$env:APPDATA = "$env:TEMP\smartvoca_test_appdata"
& ".\dist\SmartVoca.exe"
```

- 종료 후 `$env:TEMP\smartvoca_test_appdata\SmartVoca\smartvoca.db`에 단어 2000행이 들어갔는지 확인한다.
- 실행 후 임시 폴더는 확인이 끝나면 지운다 (삭제는 승인 후).

### 4.4 빌드 옵션 (PyInstaller)

| 옵션 | 이유 |
|------|------|
| `--onefile` | 파일 하나로 배포 |
| `--windowed` | 콘솔 창 숨김 |
| `--add-data data/words.csv;data` | 기본 단어를 exe 안에 포함 (최초 실행 자동 적재) |
| `--paths src` | `src/` 모듈을 import 가능하게 |
| `--clean`, `--noconfirm` | 이전 빌드 캐시를 지우고 덮어씀 |

## 5. 데이터 경로

| 항목 | 개발 실행 | exe 실행 | 근거 |
|------|-----------|----------|------|
| DB | `data/smartvoca.db` | `%APPDATA%\SmartVoca\smartvoca.db` | DR-07 |
| 설정 | `data/config.json` | `%APPDATA%\SmartVoca\config.json` | FR-13 |
| 보고서 | `data/reports/` | `%APPDATA%\SmartVoca\reports\` | FR-08 |
| 기본 단어 | `data/words.csv` (프로젝트) | exe 내부 `data/words.csv` | FR-01 |

- 경로 분기는 `src/paths.py`에서 `sys.frozen` 값으로 한다.
- exe는 설치 폴더에 쓰지 않는다 (권한 문제 방지, DR-07).

## 6. 배포 전 체크리스트

| ID | 항목 | 확인 방법 | 상태 |
|----|------|-----------|------|
| CK-01 | 자동 테스트 전체 통과 | `python -m pytest` | 2026-11-25 확인 (81 passed) |
| CK-02 | 수동 테스트 MT-01 ~ MT-08 완료 | 테스트 정의서 §5 | 미완료 |
| CK-03 | Python 3.11 ~ 3.13에서 테스트 통과 | 각 버전 가상 환경 | 미확인 (P1-5) |
| CK-04 | exe 재빌드 후 기동 확인 | §4 절차 | 미완료 (현재 exe는 2026-10-21 빌드, 이후 소스 변경 있음) |
| CK-05 | 임시 APPDATA 기동 확인 | §4.3 | 2026-10-21 확인 |
| CK-06 | 다른 PC(Python 없음)에서 실행 | 실제 PC | 미확인 (MT-10) |
| CK-07 | 라이선스 재검토 (PyQt6 GPL) | §8 | 미완료 |
| CK-08 | 비밀정보, 개인정보가 빌드에 없음 | `data/config.json`, `.env`가 포함되지 않았는지 확인 | 확인 필요 (빌드 스크립트는 `words.csv`만 넣음) |
| CK-09 | 문서 갱신 (CHANGELOG 또는 작업 일지) | 작업 일지 기록 | 진행 중 |
| CK-10 | 사용자 승인 | 배포 전 확인 | 필요 |

## 7. 산출물과 기록

| 항목 | 위치 | 보관 |
|------|------|------|
| exe | `dist/SmartVoca.exe` | Git 제외. 필요하면 외부 보관 |
| 빌드 기록 | 작업 일지 (`ai-agent/claude/SmartVoca_Work_Log_*.md`) | 빌드 날짜, 커밋 해시, 테스트 결과 |
| 이전 exe | 덮어쓰기 전에 `dist/SmartVoca_버전.exe`로 복사 | 롤백용 (승인 후 복사) |

- 현재 `dist_new/SmartVoca.exe`가 남아 있다. 용도가 불명확하므로 정리 대상으로 둔다. 삭제는 승인 후 한다 (현황분석 F-06).

## 8. 배포 전 게이트 (반드시 확인)

### 8.1 PyQt6 라이선스 (R-4, DR-01)

- PyQt6는 GPL 또는 상용 라이선스다.
- 개인 PC에서만 쓰는 현재 조건은 문제가 없다.
- **exe를 다른 사람에게 배포하면** GPL 조건을 검토해야 한다. PySide6(LGPL)로 바꾸는 방안은 DR-01에 정리되어 있다.
- 배포 결정 전에 사용자와 확인한다 (현황분석 D-13).

### 8.2 Python 버전 (DR-12)

- 개발 환경은 3.15.0이다. 3.15는 최신이라 패키지 호환성 위험이 있다.
- exe 빌드에 쓴 Python 버전을 작업 일지에 기록한다.
- 배포 전에 3.12 또는 3.13으로 빌드 검증을 한 번 한다 (CK-03). 기준 버전 결정은 현황분석 D-14.

## 9. 운영 (Operations)

- Charter §6에 따라 **Operations Manual은 생략**한다. 개인 데스크톱 앱이다.
- 대신 아래 간단한 운영 메모를 둔다.
  - 데이터 백업: 1차 NFR-04 백업 기능 완료 후 `data/backups/`(개발) 또는 `%APPDATA%\SmartVoca\backups\`(배포)에 백업
  - 장애 복구: 학습 DB가 깨지면 최근 백업 파일을 `smartvoca.db`로 복사 (백업 기능 구현 후 절차 확정)
  - 설정 초기화: `config.json` 삭제 후 기동 (기본값으로 돌아감)
  - 단어 초기화: DB 파일 삭제 후 기동 (기본 단어 2000개 재적재. 학습 기록도 함께 사라짐 — 주의)

## 10. 알려진 배포 이슈

| ID | 내용 | 조치 |
|----|------|------|
| DP-01 | `dist/SmartVoca.exe`가 2026-10-21 빌드이고, 이후 `src/ui`, `src/study` 등이 바뀌었다 | 재빌드 후 CK-04 |
| DP-02 | `dist_new/` 폴더가 남아 있다 | 정리 대상 (승인 후) |
| DP-03 | 빌드 스크립트 주석 `--add-data`의 구분자는 Windows 기준 `;`이다 | 현재 Windows 전용, 문제 없음 |
| DP-04 | 웹 버전은 exe에 포함되지 않음 | 계획된 동작 (DR-17) |
| DP-05 | 빌드 산출물(`build/SmartVoca.spec` 등)이 저장소 폴더에 있다 | `.gitignore`로 제외됨, 문제 없음 |

## 11. 롤백 절차

1. 새 exe에 문제가 있으면 이전 exe(`dist/SmartVoca_버전.exe`)를 실행한다.
2. 데이터 손상이 의심되면 백업 파일을 `smartvoca.db`로 복사한다 (백업 기능 구현 후).
3. 소스 문제면 해당 커밋을 되돌린다 (`git revert`는 승인 후).
