#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 시험 문항 데이터 모델과 상수 (FR-06)
# 파일 위치: src/quiz/question.py
from dataclasses import dataclass

from models.word import Word

DIRECTION_KO_EN = "ko_en"  # 한 -> 영
DIRECTION_EN_KO = "en_ko"  # 영 -> 한
DIRECTION_MIXED = "mixed"  # 혼합 (문항마다 무작위)

TYPE_SHORT = "short"  # 단답형
TYPE_CHOICE = "choice"  # 4지선다형
TYPE_OX = "ox"  # OX형
TYPE_MIXED = "mixed"  # 혼합 (문항마다 무작위)


@dataclass(frozen=True)
class Question:
    """시험 문항 한 개. 채점에 필요한 정답 정보를 모두 담는다."""

    word: Word
    direction: str  # 실제 적용된 방향 (DIRECTION_KO_EN 또는 DIRECTION_EN_KO)
    question_type: str  # 실제 적용된 유형 (TYPE_SHORT, TYPE_CHOICE, TYPE_OX)
    prompt: str  # 화면에 먼저 보여 줄 문제 (영단어 또는 뜻)
    expected: str  # 정답 표시: 단답·4지선다는 정답 문자열, OX는 "O" 또는 "X"
    accepted: tuple[str, ...] = ()  # 단답형에서 맞는 것으로 인정하는 답 목록
    choices: tuple[str, ...] = ()  # 4지선다 보기 (섞인 순서)
    candidate: str = ""  # OX형에서 제시하는 짝 (정답 또는 오답)
