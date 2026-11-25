#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 테이블 저장소 (FR-01, FR-02)
# 파일 위치: src/storage/word_repository.py
import sqlite3

from models.word import Word
from storage.database import Database


class WordRepository:
    """word 테이블의 읽기·쓰기를 담당한다."""

    def __init__(self, database: Database):
        self._connection = database.connection

    def upsert_many(self, words: list[Word]) -> int:
        """id가 같은 단어는 갱신하고 없으면 추가한다. 반환값은 처리한 개수."""
        with self._connection:
            for word in words:
                self._connection.execute(
                    """INSERT INTO word (id, word, pos, meaning, example, level)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                    word = excluded.word, pos = excluded.pos, meaning = excluded.meaning,
                    example = excluded.example, level = excluded.level""",
                    (word.id, word.word, word.pos, word.meaning, word.example, word.level),
                )
        return len(words)

    def list_all(self) -> list[Word]:
        """모든 단어를 id 순서로 돌려준다. 일차별 진도는 이 순서를 따른다 (DR-06)."""
        rows = self._connection.execute("SELECT * FROM word ORDER BY id").fetchall()
        return [self._row_to_word(row) for row in rows]

    def count(self) -> int:
        return self._connection.execute("SELECT COUNT(*) FROM word").fetchone()[0]

    def get_by_ids(self, word_ids: list[int]) -> dict[int, Word]:
        """여러 id의 단어를 한 번에 가져온다. 암기 세션 카드 조립에 쓴다."""
        if not word_ids:
            return {}
        placeholders = ", ".join("?" for _ in word_ids)
        rows = self._connection.execute(
            f"SELECT * FROM word WHERE id IN ({placeholders})", word_ids
        ).fetchall()
        return {row["id"]: self._row_to_word(row) for row in rows}

    def next_id(self) -> int:
        """새 단어에 줄 번호. 지금 가장 큰 id 다음 값이다 (VOCA-FR-001)."""
        return self._connection.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM word").fetchone()[0]

    def insert_word(self, word: Word) -> None:
        """단어 한 개를 추가한다. 중복 검사는 호출하는 서비스가 한다."""
        with self._connection:
            self._connection.execute(
                "INSERT INTO word (id, word, pos, meaning, example, level) VALUES (?, ?, ?, ?, ?, ?)",
                (word.id, word.word, word.pos, word.meaning, word.example, word.level),
            )

    def update_word(self, word: Word) -> None:
        """id가 같은 단어의 내용을 바꾼다 (VOCA-FR-002)."""
        with self._connection:
            self._connection.execute(
                "UPDATE word SET word = ?, pos = ?, meaning = ?, example = ?, level = ? WHERE id = ?",
                (word.word, word.pos, word.meaning, word.example, word.level, word.id),
            )

    def delete_word(self, word_id: int) -> None:
        """단어를 지운다. 기록이 있는지는 호출하는 서비스가 먼저 확인한다."""
        with self._connection:
            self._connection.execute("DELETE FROM word WHERE id = ?", (word_id,))

    def get_by_id(self, word_id: int) -> Word | None:
        row = self._connection.execute("SELECT * FROM word WHERE id = ?", (word_id,)).fetchone()
        return self._row_to_word(row) if row else None

    def find_by_text_ignore_case(self, text: str, exclude_id: int | None = None) -> Word | None:
        """영단어가 같은 다른 단어를 대소문자 무시로 찾는다 (중복 검사)."""
        row = self._connection.execute(
            "SELECT * FROM word WHERE lower(word) = lower(?) AND id != ? LIMIT 1",
            (text, exclude_id if exclude_id is not None else -1),
        ).fetchone()
        return self._row_to_word(row) if row else None

    def has_study_or_quiz_records(self, word_id: int) -> bool:
        """암기 기록이나 시험 응답이 하나라도 있으면 True. 이 단어는 지울 수 없다."""
        row = self._connection.execute(
            """SELECT EXISTS (SELECT 1 FROM study_record WHERE word_id = ?)
            OR EXISTS (SELECT 1 FROM quiz_answer WHERE word_id = ?)""",
            (word_id, word_id),
        ).fetchone()
        return bool(row[0])

    @staticmethod
    def _row_to_word(row: sqlite3.Row) -> Word:
        return Word(
            id=row["id"],
            word=row["word"],
            pos=row["pos"],
            meaning=row["meaning"],
            example=row["example"],
            level=row["level"],
        )
