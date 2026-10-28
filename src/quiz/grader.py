#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 시험 채점 로직 (FR-07, DR-04)
# 파일 위치: src/quiz/grader.py
from quiz.question import TYPE_CHOICE, TYPE_OX, TYPE_SHORT, Question


def normalize(text: str) -> str:
    """비교용 정규화: 앞뒤 공백 제거, 소문자화, 연속 공백을 한 칸으로 (DR-04)."""
    return " ".join(text.strip().lower().split())


def grade_answer(question: Question, user_answer: str) -> bool:
    """사용자 답이 맞는지 판정한다.

    - 단답형: 정규화 후 인정 답 목록 중 하나와 같으면 정답
    - 4지선다형: 선택한 보기가 정답 보기와 같으면 정답
    - OX형: 'O' 또는 'X'가 정답 표시와 같으면 정답
    """
    if question.question_type == TYPE_SHORT:
        target = normalize(user_answer)
        return bool(target) and target in {normalize(answer) for answer in question.accepted}
    if question.question_type == TYPE_CHOICE:
        return user_answer == question.expected
    if question.question_type == TYPE_OX:
        return user_answer.strip().upper() == question.expected
    raise ValueError(f"알 수 없는 문제 유형: {question.question_type}")
