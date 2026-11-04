#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 연속 학습일(streak) 계산. UI(PyQt)와 웹이 함께 쓰도록 분리 (FR-17)
# 파일 위치: src/study/streak.py
from datetime import date, timedelta


def compute_streak(study_dates: list[str], today: date) -> int:
    """연속 학습일 수. 오늘 학습했으면 오늘부터, 아니면 어제부터 거꾸로 센다.

    study_dates는 'YYYY-MM-DD' 문자열 목록이다 (순서는 상관없다).
    """
    days = {date.fromisoformat(value) for value in study_dates}
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
