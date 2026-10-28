#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 암기 세션·기록 저장소 (FR-03, FR-04)
# 파일 위치: src/storage/study_repository.py
from dataclasses import dataclass
from datetime import datetime

from storage.database import Database

RESULT_KNOW = "know"  # 알았음
RESULT_AGAIN = "again"  # 다시


@dataclass(frozen=True)
class StudySessionSummary:
    """이력 목록의 암기 세션 한 줄 요약."""

    session_id: int
    day_no: int
    started_at: str
    finished: bool
    total: int
    know_count: int
    again_count: int


@dataclass(frozen=True)
class StudyRecord:
    """암기 세션 안의 단어 한 개 기록. result가 None이면 아직 답하지 않은 카드다."""

    record_id: int
    word_id: int
    position: int
    kind: str  # 'new' 또는 'review'
    result: str | None


class StudyRepository:
    """study_session, study_record 테이블을 다룬다."""

    def __init__(self, database: Database):
        self._connection = database.connection

    def create_session(self, day_no: int, plan: list[tuple[int, str]], now: datetime) -> int:
        """새 일차 세션과 카드 목록을 한 번에 저장한다. plan은 (word_id, kind) 목록."""
        with self._connection:
            cursor = self._connection.execute(
                "INSERT INTO study_session (day_no, started_at) VALUES (?, ?)",
                (day_no, now.isoformat(timespec="seconds")),
            )
            session_id = cursor.lastrowid
            for position, (word_id, kind) in enumerate(plan):
                self._connection.execute(
                    "INSERT INTO study_record (session_id, word_id, position, kind) VALUES (?, ?, ?, ?)",
                    (session_id, word_id, position, kind),
                )
        return session_id

    def find_unfinished_session(self) -> tuple[int, int] | None:
        """끝나지 않은 가장 최근 세션의 (session_id, day_no)를 돌려준다. 이어 하기용."""
        row = self._connection.execute(
            "SELECT id, day_no FROM study_session WHERE finished_at IS NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return (row["id"], row["day_no"]) if row else None

    def last_finished_session_id(self) -> int | None:
        row = self._connection.execute(
            "SELECT id FROM study_session WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["id"] if row else None

    def last_day_no(self) -> int:
        """지금까지 시작한 세션 중 가장 큰 일차 번호. 세션이 없으면 0."""
        return self._connection.execute("SELECT COALESCE(MAX(day_no), 0) FROM study_session").fetchone()[0]

    def get_records(self, session_id: int) -> list[StudyRecord]:
        rows = self._connection.execute(
            "SELECT id, word_id, position, kind, result FROM study_record WHERE session_id = ? ORDER BY position",
            (session_id,),
        ).fetchall()
        return [
            StudyRecord(
                record_id=row["id"],
                word_id=row["word_id"],
                position=row["position"],
                kind=row["kind"],
                result=row["result"],
            )
            for row in rows
        ]

    def set_result(self, record_id: int, result: str, now: datetime) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE study_record SET result = ?, recorded_at = ? WHERE id = ?",
                (result, now.isoformat(timespec="seconds"), record_id),
            )

    def finish_session(self, session_id: int, now: datetime) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE study_session SET finished_at = ? WHERE id = ?",
                (now.isoformat(timespec="seconds"), session_id),
            )

    def list_sessions(
        self, limit: int, start_date: str = "0001-01-01", end_date: str = "9999-12-31"
    ) -> list[StudySessionSummary]:
        """최근 암기 세션부터 요약 (이력 탭). 알았음/다시 개수를 함께 준다. 날짜 범위로 거를 수 있다."""
        rows = self._connection.execute(
            """SELECT s.id, s.day_no, s.started_at, s.finished_at, COUNT(r.id) AS total,
            COALESCE(SUM(CASE WHEN r.result = 'know' THEN 1 ELSE 0 END), 0) AS know_count,
            COALESCE(SUM(CASE WHEN r.result = 'again' THEN 1 ELSE 0 END), 0) AS again_count
            FROM study_session s LEFT JOIN study_record r ON r.session_id = s.id
            WHERE substr(s.started_at, 1, 10) BETWEEN ? AND ?
            GROUP BY s.id ORDER BY s.id DESC LIMIT ?""",
            (start_date, end_date, limit),
        ).fetchall()
        return [
            StudySessionSummary(
                session_id=row["id"],
                day_no=row["day_no"],
                started_at=row["started_at"],
                finished=row["finished_at"] is not None,
                total=row["total"],
                know_count=row["know_count"],
                again_count=row["again_count"],
            )
            for row in rows
        ]

    def total_studied_words(self) -> int:
        """지금까지 한 번이라도 답한 서로 다른 단어 수 (홈 진도 표시)."""
        return self._connection.execute(
            "SELECT COUNT(DISTINCT word_id) FROM study_record WHERE result IS NOT NULL"
        ).fetchone()[0]

    def studied_dates(self) -> list[str]:
        """학습 기록이 있는 날짜 목록 (최신순). 연속 학습일 계산에 쓴다."""
        rows = self._connection.execute(
            """SELECT DISTINCT substr(recorded_at, 1, 10) AS day FROM study_record
            WHERE result IS NOT NULL ORDER BY day DESC"""
        ).fetchall()
        return [row["day"] for row in rows]

    def clear_result(self, record_id: int) -> None:
        """응답을 지워 카드를 다시 미응답 상태로 만든다 (되돌리기)."""
        with self._connection:
            self._connection.execute(
                "UPDATE study_record SET result = NULL, recorded_at = NULL WHERE id = ?",
                (record_id,),
            )

    def reopen_session(self, session_id: int) -> None:
        """끝난 세션을 다시 진행 중으로 바꾼다 (되돌리기 후)."""
        with self._connection:
            self._connection.execute("UPDATE study_session SET finished_at = NULL WHERE id = ?", (session_id,))

    def again_word_ids(self, session_id: int) -> list[int]:
        """세션에서 '다시'로 표시한 단어 id (순서 유지). 다음 날 복습 목록의 원료다."""
        rows = self._connection.execute(
            "SELECT word_id FROM study_record WHERE session_id = ? AND result = ? ORDER BY position",
            (session_id, RESULT_AGAIN),
        ).fetchall()
        return [row["word_id"] for row in rows]

    def study_days_between(self, start_date: str, end_date: str) -> int:
        """기간 안에서 암기 기록이 있었던 날짜 수. 날짜는 'YYYY-MM-DD' 문자열."""
        return self._connection.execute(
            """SELECT COUNT(DISTINCT substr(recorded_at, 1, 10)) FROM study_record
            WHERE result IS NOT NULL AND substr(recorded_at, 1, 10) BETWEEN ? AND ?""",
            (start_date, end_date),
        ).fetchone()[0]

    def studied_words_between(self, start_date: str, end_date: str) -> int:
        """기간 안에서 답한(알았음/다시) 서로 다른 단어 수."""
        return self._connection.execute(
            """SELECT COUNT(DISTINCT word_id) FROM study_record
            WHERE result IS NOT NULL AND substr(recorded_at, 1, 10) BETWEEN ? AND ?""",
            (start_date, end_date),
        ).fetchone()[0]
