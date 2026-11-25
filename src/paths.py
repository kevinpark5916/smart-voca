#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 경로 상수: 개발 실행, exe 배포본, Docker 컨테이너(DB_PATH)의 위치를 나눈다 (DR-07, FR-23, DR-18)
# 파일 위치: src/paths.py
import os
import sys
from pathlib import Path

# PyInstaller로 묶인 exe이면 True
IS_FROZEN = getattr(sys, "frozen", False)
# 컨테이너 배포 시 DB 파일 경로를 환경변수로 받는다 (예: /data/voca.db). 없으면 기본 위치를 쓴다
DB_PATH_OVERRIDE = os.environ.get("DB_PATH", "").strip()

if IS_FROZEN:
    # 읽기 전용 자원(기본 단어 CSV)은 exe 안에 풀린 임시 폴더에 있다
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS"))
    # 사용자 데이터(DB, 설정, 보고서)는 쓰기 가능한 APPDATA에 둔다
    USER_DATA_DIR = Path(os.environ["APPDATA"]) / "SmartVoca"
else:
    RESOURCE_DIR = Path(__file__).resolve().parent.parent
    USER_DATA_DIR = RESOURCE_DIR / "data"

if DB_PATH_OVERRIDE:
    # DB_PATH를 주면 설정·보고서도 같은 폴더(예: /data)에 둔다
    DB_PATH = Path(DB_PATH_OVERRIDE)
    USER_DATA_DIR = DB_PATH.parent
else:
    DB_PATH = USER_DATA_DIR / "smartvoca.db"

PROJECT_ROOT = RESOURCE_DIR
DATA_DIR = USER_DATA_DIR
# 기본 단어 CSV. 최초 실행 때 DB로 가져오며, 원본은 덮어쓰지 않는다 (NFR-04)
WORDS_CSV_PATH = RESOURCE_DIR / "data" / "words.csv"
CONFIG_PATH = USER_DATA_DIR / "config.json"
REPORT_DIR = USER_DATA_DIR / "reports"
