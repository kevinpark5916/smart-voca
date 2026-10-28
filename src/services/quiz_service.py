#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 시험 출제·채점·저장 흐름 서비스 (FR-05, FR-06, FR-07)
# 파일 위치: src/services/quiz_service.py
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from config.settings import Settings
from quiz.grader import grade_answer
from quiz.question import TYPE_CHOICE, TYPE_MIXED, Question
from quiz.question_builder import CHOICE_COUNT, QuestionBuilder
from quiz.weighting import compute_word_weight, pick_weighted_words
from storage.quiz_repository import QuizRepository
from storage.word_repository import WordRepository


@dataclass
class QuizRun:
    """진행 중인 시험 한 번. answers[i]는 i번 문항의 채점 결과(None이면 아직 안 품)."""

    session_id: int
    questions: tuple[Question, ...]
    answers: list[bool | None] = field(default_factory=list)
    user_answers: list[str | None] = field(default_factory=list)  # 사용자가 입력한 답 (결과 화면에 쓴다)

    @property
    def is_finished(self) -> bool:
        return all(answer is not None for answer in self.answers)

    @property
    def correct_count(self) -> int:
        return sum(1 for answer in self.answers if answer)


class QuizService:
    """가중치 출제 -> 채점 -> 저장 순서를 묶어 준다."""

    def __init__(
        self,
        words: WordRepository,
        quiz: QuizRepository,
        settings_provider: Callable[[], Settings],
        rng: random.Random,
    ):
        self._words = words
        self._quiz = quiz
        self._settings_provider = settings_provider
        self._rng = rng

    def create_run(self, count: int, direction: str, question_type: str, now: datetime) -> QuizRun:
        """가중치에 따라 단어를 뽑아 문항을 만들고, 시험 세션을 저장한다."""
        all_words = self._words.list_all()
        self._check_enough_words(all_words, question_type)
        stats = self._quiz.get_word_stats()
        settings = self._settings_provider()
        weighted = [(word, compute_word_weight(stats.get(word.id), now, settings)) for word in all_words]
        picked = pick_weighted_words(weighted, count, self._rng)
        return self._start_run(picked, all_words, direction, question_type, now)

    def create_retry_run(self, run: QuizRun, direction: str, question_type: str, now: datetime) -> QuizRun:
        """방금 시험에서 틀린 단어만 다시 출제한다."""
        wrong_words = [question.word for question, answer in zip(run.questions, run.answers) if answer is False]
        if not wrong_words:
            raise ValueError("틀린 단어가 없습니다")
        all_words = self._words.list_all()
        self._check_enough_words(all_words, question_type)
        return self._start_run(wrong_words, all_words, direction, question_type, now)

    @staticmethod
    def _check_enough_words(all_words, question_type: str) -> None:
        needs_choices = question_type in (TYPE_CHOICE, TYPE_MIXED)
        if len(all_words) < (CHOICE_COUNT if needs_choices else 1):
            raise ValueError("시험을 만들 단어가 부족합니다 (4지선다는 단어 4개 이상 필요)")

    def _start_run(self, words, all_words, direction: str, question_type: str, now: datetime) -> QuizRun:
        """주어진 단어로 문항을 만들고 시험 세션을 저장한다. 보기·OX 짝은 전체 단어에서 고른다."""
        builder = QuestionBuilder(all_words, self._rng)
        questions = tuple(builder.build(word, direction, question_type) for word in words)
        session_id = self._quiz.create_session(direction, question_type, len(questions), now)
        return QuizRun(
            session_id=session_id,
            questions=questions,
            answers=[None] * len(questions),
            user_answers=[None] * len(questions),
        )

    def submit(self, run: QuizRun, index: int, user_answer: str, now: datetime) -> bool:
        """index번 문항의 답을 채점하고 저장한다. 반환값은 정답 여부."""
        if run.answers[index] is not None:
            raise ValueError("이미 답한 문항입니다")
        question = run.questions[index]
        is_correct = grade_answer(question, user_answer)
        self._quiz.record_answer(
            session_id=run.session_id,
            word_id=question.word.id,
            direction=question.direction,
            question_type=question.question_type,
            prompt=question.prompt,
            expected=question.expected,
            user_answer=user_answer,
            is_correct=is_correct,
            now=now,
        )
        run.answers[index] = is_correct
        run.user_answers[index] = user_answer
        return is_correct

    def finish(self, run: QuizRun, now: datetime) -> None:
        self._quiz.finish_session(run.session_id, now)
