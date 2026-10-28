#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 문항 생성과 채점 테스트 (FR-06, FR-07, DR-04)
# 파일 위치: tests/test_quiz_grading.py
import random

import pytest

from conftest import make_word  # noqa: E402
from quiz.grader import grade_answer, normalize
from quiz.question import (
    DIRECTION_EN_KO,
    DIRECTION_KO_EN,
    DIRECTION_MIXED,
    TYPE_CHOICE,
    TYPE_MIXED,
    TYPE_OX,
    TYPE_SHORT,
)
from quiz.question_builder import QuestionBuilder


def test_normalize_trims_case_and_spaces():
    assert normalize("  Hello   World ") == "hello world"


def test_short_answer_accepts_any_comma_separated_meaning():
    word = make_word(1, "river", "강, 하천")
    builder = QuestionBuilder([word], random.Random(0))
    question = builder.build(word, DIRECTION_EN_KO, TYPE_SHORT)
    assert grade_answer(question, "하천")
    assert grade_answer(question, " 강 ")
    assert not grade_answer(question, "바다")


def test_short_answer_english_is_case_insensitive():
    word = make_word(1, "River", "강")
    question = QuestionBuilder([word], random.Random(0)).build(word, DIRECTION_KO_EN, TYPE_SHORT)
    assert grade_answer(question, "river")
    assert grade_answer(question, "  RIVER ")


def test_empty_short_answer_is_wrong():
    word = make_word(1, "river", "강")
    question = QuestionBuilder([word], random.Random(0)).build(word, DIRECTION_KO_EN, TYPE_SHORT)
    assert not grade_answer(question, "   ")


def test_parenthesis_is_optional_in_short_answer():
    word = make_word(1, "bay", "만(灣)")
    question = QuestionBuilder([word], random.Random(0)).build(word, DIRECTION_EN_KO, TYPE_SHORT)
    assert grade_answer(question, "만")
    assert grade_answer(question, "만(灣)")


def test_choice_has_four_distinct_options_including_answer(sample_words):
    word = sample_words[0]
    question = QuestionBuilder(sample_words, random.Random(3)).build(word, DIRECTION_EN_KO, TYPE_CHOICE)
    assert len(question.choices) == 4
    assert len(set(question.choices)) == 4
    assert question.expected in question.choices
    assert grade_answer(question, question.expected)
    wrong = next(option for option in question.choices if option != question.expected)
    assert not grade_answer(question, wrong)


def test_choice_skips_distractors_with_same_meaning():
    same_meaning = [make_word(1, "a1", "같은뜻"), make_word(2, "a2", "같은뜻"), make_word(3, "a3", "다른뜻")]
    question = QuestionBuilder(same_meaning, random.Random(0)).build(same_meaning[0], DIRECTION_EN_KO, TYPE_CHOICE)
    assert question.choices.count("같은뜻") == 1


def test_ox_expected_matches_candidate(sample_words):
    word = sample_words[0]
    builder = QuestionBuilder(sample_words, random.Random(5))
    for _ in range(30):
        question = builder.build(word, DIRECTION_KO_EN, TYPE_OX)
        is_true_pair = question.candidate == word.word
        assert question.expected == ("O" if is_true_pair else "X")
        assert grade_answer(question, question.expected)
        assert not grade_answer(question, "O" if question.expected == "X" else "X")


def test_mixed_direction_and_type_resolve_to_concrete_values(sample_words):
    builder = QuestionBuilder(sample_words, random.Random(9))
    seen_directions, seen_types = set(), set()
    for word in sample_words:
        question = builder.build(word, DIRECTION_MIXED, TYPE_MIXED)
        seen_directions.add(question.direction)
        seen_types.add(question.question_type)
    assert seen_directions <= {DIRECTION_KO_EN, DIRECTION_EN_KO}
    assert len(seen_types) >= 2


def test_ko_en_prompt_is_meaning_and_answer_is_word():
    word = make_word(1, "river", "강")
    question = QuestionBuilder([word], random.Random(0)).build(word, DIRECTION_KO_EN, TYPE_SHORT)
    assert question.prompt == "강"
    assert question.accepted == ("river",)


def test_unknown_question_type_raises():
    word = make_word(1)
    with pytest.raises(ValueError):
        QuestionBuilder([word], random.Random(0)).build(word, DIRECTION_KO_EN, "essay")
