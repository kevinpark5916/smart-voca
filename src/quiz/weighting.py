#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 출제 가중치 계산과 가중 무작위 선택 (FR-05, DR-03)
# 파일 위치: src/quiz/weighting.py
import random
from datetime import datetime, timedelta

from config.settings import Settings
from models.word import Word
from models.word_stat import WordStat


def compute_word_weight(stat: WordStat | None, now: datetime, settings: Settings) -> float:
    """단어 하나의 출제 가중치.

    w = 1 + W_NEW(이력 없음) + W_OLD(마지막 시험 후 OLD_DAYS일 이상) + W_WRONG x 오답률
    이력이 없는 단어는 W_NEW만 받는다 (마지막 시험 시각이 없으므로 '오래됨'은 적용하지 않는다).
    """
    if stat is None or stat.attempts == 0:
        return 1.0 + settings.weight_new
    weight = 1.0
    if stat.last_tested_at is None or now - stat.last_tested_at >= timedelta(days=settings.old_days):
        weight += settings.weight_old
    wrong_rate = stat.wrong / stat.attempts
    return weight + settings.weight_wrong * wrong_rate


def pick_weighted_words(
    weighted_words: list[tuple[Word, float]],
    count: int,
    rng: random.Random,
) -> list[Word]:
    """가중치에 비례해 중복 없이 count개를 고른다. 가중치가 클수록 자주 뽑힌다.

    한 번 뽑힌 단어는 pool에서 빼고 다시 뽑는다 (같은 시험에서 같은 단어 반복 방지).
    """
    pool = list(weighted_words)
    picked: list[Word] = []
    for _ in range(min(count, len(pool))):
        total_weight = sum(weight for _, weight in pool)
        target = rng.uniform(0, total_weight)
        accumulated = 0.0
        chosen_index = len(pool) - 1
        for index, (_, weight) in enumerate(pool):
            accumulated += weight
            if target <= accumulated:
                chosen_index = index
                break
        picked.append(pool.pop(chosen_index)[0])
    return picked
