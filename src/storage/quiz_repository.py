#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 시험 세션·응답 저장소와 단어별 통계 (FR-05, FR-07, FR-08)
# 파일 위치: src/storage/quiz_repository.py
from dataclasses import dataclass
from datetime import datetime

from models.word_stat import WordStat
from storage.database import Database


@dataclass(frozen=True)
class QuizSessionSummary:
    """이력 목록의 시험 한 줄 요약."""

    session_id: int
    started_at: str
    direction: str
    question_type: str
    total: int
    answers: int
    correct: int


@dataclass(frozen=True)
class QuizAnswerDetail:
    """시험 세션 안의 문항 한 개 응답."""

    answered_at: str
    word: str
    prompt: str
    expected: str
    user_answer: str
    is_correct: bool
    question_type: str


class QuizRepository:
    """quiz_session, quiz_answer 테이블을 다룬다."""

    def __init__(self, database: Database):
        self._connection = database.connection

    def create_session(self, direction: str, question_type: str, total: int, now: datetime) -> int:
        with self._connection:
            cursor = self._connection.execute(
                """INSERT INTO quiz_session (started_at, direction, question_type, total)
                VALUES (?, ?, ?, ?)""",
                (now.isoformat(timespec="seconds"), direction, question_type, total),
            )
        return cursor.lastrowid

    def finish_session(self, session_id: int, now: datetime) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE quiz_session SET finished_at = ? WHERE id = ?",
                (now.isoformat(timespec="seconds"), session_id),
            )

    def record_answer(
        self,
        session_id: int,
        word_id: int,
        direction: str,
        question_type: str,
        prompt: str,
        expected: str,
        user_answer: str,
        is_correct: bool,
        now: datetime,
    ) -> None:
        """문항 하나의 응답을 저장한다. 혼합 출제일 수 있으므로 방향·유형은 문항마다 기록한다."""
        with self._connection:
            self._connection.execute(
                """INSERT INTO quiz_answer (quiz_session_id, word_id, direction, question_type,
                prompt, expected, user_answer, is_correct, answered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    word_id,
                    direction,
                    question_type,
                    prompt,
                    expected,
                    user_answer,
                    int(is_correct),
                    now.isoformat(timespec="seconds"),
                ),
            )

    def get_word_stats(self) -> dict[int, WordStat]:
        """단어 id -> 시험 통계. 한 번도 안 본 단어는 dict에 없다."""
        rows = self._connection.execute(
            """SELECT word_id, COUNT(*) AS attempts, SUM(1 - is_correct) AS wrong,
            MAX(answered_at) AS last_tested_at FROM quiz_answer GROUP BY word_id"""
        ).fetchall()
        return {
            row["word_id"]: WordStat(
                attempts=row["attempts"],
                wrong=row["wrong"],
                last_tested_at=datetime.fromisoformat(row["last_tested_at"]),
            )
            for row in rows
        }

    def summary_between(self, start_date: str, end_date: str) -> tuple[int, int, int]:
        """기간 안의 (시험 횟수, 응답 수, 정답 수)."""
        sessions = self._connection.execute(
            """SELECT COUNT(*) FROM quiz_session
            WHERE started_at >= ? AND substr(started_at, 1, 10) BETWEEN ? AND ?""",
            (start_date, start_date, end_date),
        ).fetchone()[0]
        row = self._connection.execute(
            """SELECT COUNT(*) AS answers, COALESCE(SUM(is_correct), 0) AS correct FROM quiz_answer
            WHERE substr(answered_at, 1, 10) BETWEEN ? AND ?""",
            (start_date, end_date),
        ).fetchone()
        return sessions, row["answers"], row["correct"]

    def wrong_word_ids(self, limit: int) -> list[int]:
        """오답률이 높은 단어 id 목록 (오답이 1번 이상인 단어만). 암기 복습에 섞는다 (VOCA-FR-013)."""
        rows = self._connection.execute(
            """SELECT word_id FROM quiz_answer GROUP BY word_id
            HAVING SUM(1 - is_correct) > 0
            ORDER BY SUM(1 - is_correct) * 1.0 / COUNT(*) DESC, SUM(1 - is_correct) DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [row["word_id"] for row in rows]

    def daily_accuracy(self, start_date: str, end_date: str) -> list[tuple[str, int, int]]:
        """날짜별 (날짜, 응답 수, 정답 수). 날짜 오름차순. 정답률 추이 그래프에 쓴다 (VOCA-FR-032)."""
        rows = self._connection.execute(
            """SELECT substr(answered_at, 1, 10) AS day, COUNT(*) AS answers, SUM(is_correct) AS correct
            FROM quiz_answer WHERE substr(answered_at, 1, 10) BETWEEN ? AND ?
            GROUP BY day ORDER BY day""",
            (start_date, end_date),
        ).fetchall()
        return [(row["day"], row["answers"], row["correct"]) for row in rows]

    def top_wrong_between(self, start_date: str, end_date: str, limit: int) -> list[tuple[str, int, int]]:
        """기간 안에서 자주 틀린 단어 목록 (단어, 응답 수, 오답 수). 오답이 많은 순."""
        rows = self._connection.execute(
            """SELECT w.word AS word, COUNT(*) AS attempts, SUM(1 - a.is_correct) AS wrong
            FROM quiz_answer a JOIN word w ON w.id = a.word_id
            WHERE substr(a.answered_at, 1, 10) BETWEEN ? AND ?
            GROUP BY a.word_id HAVING wrong > 0
            ORDER BY wrong DESC, attempts ASC LIMIT ?""",
            (start_date, end_date, limit),
        ).fetchall()
        return [(row["word"], row["attempts"], row["wrong"]) for row in rows]

    def list_sessions(
        self, limit: int, start_date: str = "0001-01-01", end_date: str = "9999-12-31"
    ) -> list[QuizSessionSummary]:
        """최근 시험 세션부터 요약을 돌려준다 (이력 탭). 날짜 범위로 거를 수 있다."""
        rows = self._connection.execute(
            """SELECT s.id, s.started_at, s.direction, s.question_type, s.total,
            COUNT(a.id) AS answers, COALESCE(SUM(a.is_correct), 0) AS correct
            FROM quiz_session s LEFT JOIN quiz_answer a ON a.quiz_session_id = s.id
            WHERE substr(s.started_at, 1, 10) BETWEEN ? AND ?
            GROUP BY s.id ORDER BY s.id DESC LIMIT ?""",
            (start_date, end_date, limit),
        ).fetchall()
        return [
            QuizSessionSummary(
                session_id=row["id"],
                started_at=row["started_at"],
                direction=row["direction"],
                question_type=row["question_type"],
                total=row["total"],
                answers=row["answers"],
                correct=row["correct"],
            )
            for row in rows
        ]

    def recent_accuracy(self, limit: int) -> tuple[int, int]:
        """최근 limit개 시험의 (응답 수 합계, 정답 수 합계). 홈 화면 정답률에 쓴다."""
        row = self._connection.execute(
            """SELECT COALESCE(SUM(answers), 0) AS answers, COALESCE(SUM(correct), 0) AS correct FROM (
            SELECT s.id, COUNT(a.id) AS answers, COALESCE(SUM(a.is_correct), 0) AS correct
            FROM quiz_session s JOIN quiz_answer a ON a.quiz_session_id = s.id
            GROUP BY s.id ORDER BY s.id DESC LIMIT ?)""",
            (limit,),
        ).fetchone()
        return row["answers"], row["correct"]

    def session_answers(self, session_id: int) -> list[QuizAnswerDetail]:
        """한 시험 세션의 문항별 응답 (문제 순서대로)."""
        rows = self._connection.execute(
            """SELECT a.answered_at, w.word AS word, a.prompt, a.expected, a.user_answer,
            a.is_correct, a.question_type
            FROM quiz_answer a JOIN word w ON w.id = a.word_id
            WHERE a.quiz_session_id = ? ORDER BY a.id""",
            (session_id,),
        ).fetchall()
        return [
            QuizAnswerDetail(
                answered_at=row["answered_at"],
                word=row["word"],
                prompt=row["prompt"],
                expected=row["expected"],
                user_answer=row["user_answer"],
                is_correct=bool(row["is_correct"]),
                question_type=row["question_type"],
            )
            for row in rows
        ]
