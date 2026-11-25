#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 일차별 암기 목록 생성 순수 로직 (FR-04, DR-06)
# 파일 위치: src/study/study_plan.py
from dataclasses import dataclass

from config.settings import Settings
from models.word import Word

KIND_NEW = "new"
KIND_REVIEW = "review"


@dataclass(frozen=True)
class PlanItem:
    word: Word
    kind: str  # KIND_NEW 또는 KIND_REVIEW


def build_day_plan(
    words: list[Word],
    day_no: int,
    settings: Settings,
    previous_again_ids: list[int],
    wrong_word_ids: tuple[int, ...] | list[int] = (),
) -> list[PlanItem]:
    """N일차 암기 목록을 만든다. 복습 단어가 앞, 신규 단어가 뒤에 온다.

    - 신규: id 순서대로 (day_no-1)*N 번째부터 N개 (DR-06)
    - 복습: 직전 세션에서 '다시'로 표시한 단어를 먼저, 그다음 자주 틀린 단어(wrong_word_ids, 오답률 높은 순)를
      최대 M개까지 담는다 (VOCA-FR-013). 오늘의 신규 단어와 겹치거나 중복되면 뺀다.
    """
    if day_no < 1:
        raise ValueError("일차는 1 이상이어야 합니다")
    ordered_words = sorted(words, key=lambda word: word.id)
    start = (day_no - 1) * settings.daily_new_count
    new_words = ordered_words[start : start + settings.daily_new_count]
    new_ids = {word.id for word in new_words}

    words_by_id = {word.id: word for word in ordered_words}
    review_words: list[Word] = []
    picked_ids: set[int] = set()
    for word_id in list(previous_again_ids) + list(wrong_word_ids):
        if len(review_words) >= settings.daily_review_count:
            break
        if word_id in new_ids or word_id in picked_ids or word_id not in words_by_id:
            continue
        picked_ids.add(word_id)
        review_words.append(words_by_id[word_id])

    return [PlanItem(word, KIND_REVIEW) for word in review_words] + [
        PlanItem(word, KIND_NEW) for word in new_words
    ]


def count_total_days(total_words: int, daily_new_count: int) -> int:
    """전체 단어를 하루 분량으로 나눴을 때 일수 (올림)."""
    return -(-total_words // daily_new_count)
