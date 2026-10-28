#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - SQLite 연결과 테이블 생성 (DR-02, FR-07)
# 파일 위치: src/storage/database.py
import sqlite3
from pathlib import Path

# 각 항목은 하나의 SQL 문이다. 문 안에는 빈 줄을 넣지 않는다 (CLAUDE.md 규칙 4).
SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS word (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL UNIQUE,
    pos TEXT NOT NULL,
    meaning TEXT NOT NULL,
    example TEXT NOT NULL,
    level INTEGER NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS study_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_no INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT
)""",
    """CREATE TABLE IF NOT EXISTS study_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES study_session(id),
    word_id INTEGER NOT NULL REFERENCES word(id),
    position INTEGER NOT NULL,
    kind TEXT NOT NULL,
    result TEXT,
    recorded_at TEXT
)""",
    """CREATE TABLE IF NOT EXISTS quiz_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    direction TEXT NOT NULL,
    question_type TEXT NOT NULL,
    total INTEGER NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS quiz_answer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_session_id INTEGER NOT NULL REFERENCES quiz_session(id),
    word_id INTEGER NOT NULL REFERENCES word(id),
    direction TEXT NOT NULL,
    question_type TEXT NOT NULL,
    prompt TEXT NOT NULL,
    expected TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    answered_at TEXT NOT NULL
)""",
    "CREATE INDEX IF NOT EXISTS idx_quiz_answer_word ON quiz_answer(word_id)",
    "CREATE INDEX IF NOT EXISTS idx_study_record_session ON study_record(session_id)",
)


class Database:
    """SQLite 연결을 열고 테이블을 만든다. 나머지 저장소 클래스가 이 연결을 공유한다."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        """테이블과 인덱스가 없으면 만든다. 이미 있으면 그대로 둔다."""
        for statement in SCHEMA_STATEMENTS:
            self.connection.execute(statement)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
