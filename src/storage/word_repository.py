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
