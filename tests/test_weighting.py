#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 출제 가중치 테스트 (FR-05)
# 파일 위치: tests/test_weighting.py
import random
from datetime import datetime, timedelta

from config.settings import Settings
from models.word_stat import WordStat
from quiz.weighting import compute_word_weight, pick_weighted_words

NOW = datetime(2026, 10, 21, 12, 0, 0)


def test_unseen_word_gets_new_bonus_only():
    weight = compute_word_weight(None, NOW, Settings())
    assert weight == 1.0 + 3.0


def test_recent_word_with_no_wrong_answers_has_base_weight():
    stat = WordStat(attempts=4, wrong=0, last_tested_at=NOW - timedelta(days=1))
    assert compute_word_weight(stat, NOW, Settings()) == 1.0


def test_old_word_gets_old_bonus():
    stat = WordStat(attempts=1, wrong=0, last_tested_at=NOW - timedelta(days=7))
    assert compute_word_weight(stat, NOW, Settings()) == 1.0 + 2.0


def test_wrong_rate_adds_weight_proportionally():
    stat = WordStat(attempts=4, wrong=2, last_tested_at=NOW - timedelta(days=1))
    assert compute_word_weight(stat, NOW, Settings()) == 1.0 + 4.0 * 0.5


def test_weights_follow_settings():
    settings = Settings(weight_new=10.0, weight_old=0.0, weight_wrong=0.0)
    assert compute_word_weight(None, NOW, settings) == 11.0


def test_pick_returns_distinct_words_up_to_count(sample_words):
    weighted = [(word, 1.0) for word in sample_words]
    picked = pick_weighted_words(weighted, 10, random.Random(1))
    assert len(picked) == 10
    assert len({word.id for word in picked}) == 10


def test_pick_never_exceeds_pool_size(sample_words):
    weighted = [(word, 1.0) for word in sample_words[:3]]
    assert len(pick_weighted_words(weighted, 50, random.Random(1))) == 3


def test_heavy_weight_is_picked_much_more_often(sample_words):
    # 1번 단어만 가중치 100, 나머지는 1. 여러 번 뽑으면 1번이 거의 항상 포함되어야 한다.
    weighted = [(word, 100.0 if word.id == 1 else 1.0) for word in sample_words]
    rng = random.Random(42)
    hits = sum(
        1 for _ in range(200)
        if any(word.id == 1 for word in pick_weighted_words(weighted, 5, rng))
    )
    assert hits > 180
