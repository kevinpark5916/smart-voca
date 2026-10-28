#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 일차별 암기 목록 테스트 (FR-04)
# 파일 위치: tests/test_study_plan.py
import pytest

from config.settings import Settings
from study.study_plan import KIND_NEW, KIND_REVIEW, build_day_plan, count_total_days


def ids_of(plan):
    return [item.word.id for item in plan]


def test_day_one_takes_first_n_words_by_id(sample_words):
    plan = build_day_plan(sample_words, 1, Settings(daily_new_count=5), [])
    assert ids_of(plan) == [1, 2, 3, 4, 5]
    assert all(item.kind == KIND_NEW for item in plan)


def test_day_two_continues_from_next_block(sample_words):
    plan = build_day_plan(sample_words, 2, Settings(daily_new_count=5), [])
    assert ids_of(plan) == [6, 7, 8, 9, 10]


def test_review_words_come_first_and_are_capped(sample_words):
    settings = Settings(daily_new_count=5, daily_review_count=2)
    plan = build_day_plan(sample_words, 2, settings, previous_again_ids=[20, 21, 22])
    assert ids_of(plan) == [20, 21, 6, 7, 8, 9, 10]
    assert [item.kind for item in plan[:2]] == [KIND_REVIEW, KIND_REVIEW]


def test_review_word_already_in_today_new_block_is_not_duplicated(sample_words):
    settings = Settings(daily_new_count=5, daily_review_count=10)
    plan = build_day_plan(sample_words, 1, settings, previous_again_ids=[3, 25])
    assert ids_of(plan) == [25, 1, 2, 3, 4, 5]
    assert len(set(ids_of(plan))) == len(plan)


def test_unknown_review_id_is_ignored(sample_words):
    plan = build_day_plan(sample_words, 1, Settings(daily_new_count=3), previous_again_ids=[999])
    assert ids_of(plan) == [1, 2, 3]


def test_day_must_be_positive(sample_words):
    with pytest.raises(ValueError):
        build_day_plan(sample_words, 0, Settings(), [])


def test_count_total_days_rounds_up():
    assert count_total_days(2000, 20) == 100
    assert count_total_days(2001, 20) == 101
