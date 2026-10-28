#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어별 시험 통계 모델 (FR-05 가중치 계산 입력값)
# 파일 위치: src/models/word_stat.py
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WordStat:
    """단어 하나의 시험 이력 요약. 가중치 계산에 쓴다."""

    attempts: int  # 전체 응답 수
    wrong: int  # 오답 수
    last_tested_at: datetime | None  # 마지막 응답 시각 (없으면 None)
