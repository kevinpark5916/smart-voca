#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 하나로 시험 문항을 만드는 로직 (FR-06)
# 파일 위치: src/quiz/question_builder.py
import random

from models.word import Word
from quiz.question import (
    DIRECTION_EN_KO,
    DIRECTION_KO_EN,
    DIRECTION_MIXED,
    TYPE_CHOICE,
    TYPE_MIXED,
    TYPE_OX,
    TYPE_SHORT,
    Question,
)

CHOICE_COUNT = 4  # 4지선다 보기 개수 (정답 1 + 오답 3)


class QuestionBuilder:
    """전체 단어 목록을 보기·오답 후보로 쓰면서 문항을 만든다."""

    def __init__(self, words: list[Word], rng: random.Random):
        self._words = words
        self._rng = rng

    def build(self, word: Word, direction: str, question_type: str) -> Question:
        """혼합(mixed) 설정이면 방향과 유형을 무작위로 정한 뒤 문항을 만든다."""
        actual_direction = self._rng.choice([DIRECTION_KO_EN, DIRECTION_EN_KO]) if direction == DIRECTION_MIXED else direction
        actual_type = self._rng.choice([TYPE_SHORT, TYPE_CHOICE, TYPE_OX]) if question_type == TYPE_MIXED else question_type
        if actual_type == TYPE_SHORT:
            return self._build_short(word, actual_direction)
        if actual_type == TYPE_CHOICE:
            return self._build_choice(word, actual_direction)
        if actual_type == TYPE_OX:
            return self._build_ox(word, actual_direction)
        raise ValueError(f"알 수 없는 문제 유형: {actual_type}")

    def _build_short(self, word: Word, direction: str) -> Question:
        prompt, expected = _prompt_and_answer(word, direction)
        return Question(
            word=word,
            direction=direction,
            question_type=TYPE_SHORT,
            prompt=prompt,
            expected=expected,
            accepted=_accepted_answers(word, direction),
        )

    def _build_choice(self, word: Word, direction: str) -> Question:
        prompt, answer = _prompt_and_answer(word, direction)
        # 정답과 같은 답 문자열을 가진 단어는 오답 후보에서 뺀다 (뜻이 같은 단어 방지)
        others = [other for other in self._words if other.id != word.id and _answer_side(other, direction) != answer]
        distractors = self._rng.sample(others, k=min(CHOICE_COUNT - 1, len(others)))
        options = [answer] + [_answer_side(other, direction) for other in distractors]
        self._rng.shuffle(options)
        return Question(
            word=word,
            direction=direction,
            question_type=TYPE_CHOICE,
            prompt=prompt,
            expected=answer,
            choices=tuple(options),
        )

    def _build_ox(self, word: Word, direction: str) -> Question:
        prompt, answer = _prompt_and_answer(word, direction)
        others = [other for other in self._words if other.id != word.id and _answer_side(other, direction) != answer]
        # 절반은 정답 짝(O), 절반은 다른 단어의 짝(X)을 보여 준다
        show_correct = self._rng.random() < 0.5 or not others
        if show_correct:
            candidate, expected = answer, "O"
        else:
            candidate, expected = _answer_side(self._rng.choice(others), direction), "X"
        return Question(
            word=word,
            direction=direction,
            question_type=TYPE_OX,
            prompt=prompt,
            expected=expected,
            candidate=candidate,
        )


def _prompt_and_answer(word: Word, direction: str) -> tuple[str, str]:
    """방향에 따라 (문제로 보여 줄 것, 정답 문자열)을 돌려준다."""
    if direction == DIRECTION_EN_KO:
        return word.word, word.meaning
    return word.meaning, word.word


def _answer_side(word: Word, direction: str) -> str:
    """방향에 따른 '답 쪽' 문자열. 영->한이면 뜻, 한->영이면 영단어."""
    return word.meaning if direction == DIRECTION_EN_KO else word.word


def _accepted_answers(word: Word, direction: str) -> tuple[str, ...]:
    """단답형에서 맞는 것으로 인정할 답 목록. 뜻은 쉼표로 나눈 각 항목이 모두 정답이다."""
    if direction == DIRECTION_EN_KO:
        return tuple(word.meaning_candidates())
    return (word.word,)
