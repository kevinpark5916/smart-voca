#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - PyInstaller로 SmartVoca.exe 단일 파일을 만든다 (FR-23)
# 파일 위치: ai-agent/scripts/build_exe.py
# 사용법: python ai-agent/scripts/build_exe.py  (결과: dist/SmartVoca.exe)
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
WORDS_CSV = PROJECT_ROOT / "data" / "words.csv"


def build_command() -> list[str]:
    """PyInstaller 실행 인자를 만든다."""
    return [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",  # 기존 결과를 묻지 않고 덮어쓴다
        "--clean",  # 빌드 캐시를 지우고 처음부터 만든다
        "--onefile",  # 실행 파일 하나로 묶는다
        "--windowed",  # 실행 시 콘솔 창을 띄우지 않는다
        "--name", "SmartVoca",
        "--paths", str(SRC_DIR),
        # 기본 단어 CSV를 exe 안의 data/ 폴더에 넣는다 (Windows에서는 구분자가 ';')
        "--add-data", f"{WORDS_CSV}{os.pathsep}data",
        "--distpath", str(PROJECT_ROOT / "dist"),
        "--workpath", str(PROJECT_ROOT / "build"),
        "--specpath", str(PROJECT_ROOT / "build"),
        str(SRC_DIR / "main.py"),
    ]


def main() -> int:
    if not WORDS_CSV.exists():
        print(f"기본 단어 파일이 없습니다: {WORDS_CSV}")
        return 1
    result = subprocess.run(build_command(), cwd=PROJECT_ROOT, check=False)
    if result.returncode == 0:
        print(f"빌드 완료: {PROJECT_ROOT / 'dist' / 'SmartVoca.exe'}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
