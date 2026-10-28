#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 기간별 보고서 요약 데이터 계산 (FR-08)
# 파일 위치: src/report/report_data.py
from dataclasses import dataclass
from datetime import date

from storage.quiz_repository import QuizRepository
from storage.study_repository import StudyRepository


@dataclass(frozen=True)
class WrongWordStat:
    word: str
    attempts: int
    wrong: int


@dataclass(frozen=True)
class ReportSummary:
    start_date: date
    end_date: date
    study_days: int
    studied_words: int
    quiz_sessions: int
    answer_count: int
    correct_count: int
    top_wrong: tuple[WrongWordStat, ...]

    @property
    def accuracy(self) -> float:
        """정답률 (0~1). 응답이 없으면 0."""
        return self.correct_count / self.answer_count if self.answer_count else 0.0


def build_report_summary(
    study: StudyRepository,
    quiz: QuizRepository,
    start_date: date,
    end_date: date,
    top_limit: int = 10,
) -> ReportSummary:
    """기간(양 끝 포함)의 학습·시험 지표를 모은다. 날짜 비교는 'YYYY-MM-DD' 문자열로 한다."""
    start_text = start_date.isoformat()
    end_text = end_date.isoformat()
    sessions, answers, correct = quiz.summary_between(start_text, end_text)
    top_wrong = tuple(
        WrongWordStat(word=word, attempts=attempts, wrong=wrong)
        for word, attempts, wrong in quiz.top_wrong_between(start_text, end_text, top_limit)
    )
    return ReportSummary(
        start_date=start_date,
        end_date=end_date,
        study_days=study.study_days_between(start_text, end_text),
        studied_words=study.studied_words_between(start_text, end_text),
        quiz_sessions=sessions,
        answer_count=answers,
        correct_count=correct,
        top_wrong=top_wrong,
    )
