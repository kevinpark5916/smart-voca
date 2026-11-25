#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 앱 구성요소(DB, 저장소, 서비스, 설정)를 한곳에서 조립
# 파일 위치: src/app_context.py
import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dataclasses import replace

from config.settings import Settings, load_settings, save_settings
from models.word import Word
from paths import CONFIG_PATH, DB_PATH, WORDS_CSV_PATH
from services.quiz_service import QuizService
from services.study_service import StudyService
from services.word_service import WordService
from storage.database import Database
from storage.quiz_repository import QuizRepository
from storage.study_repository import StudyRepository
from storage.word_csv import SIMPLE_ID_PLACEHOLDER, load_words_from_csv, save_words_to_csv
from storage.word_repository import WordRepository

WRONG_WORD_POOL_SIZE = 50  # 암기 복습에 섞을 자주 틀린 단어 후보 수 (VOCA-FR-013)


@dataclass
class AppContext:
    """UI가 쓰는 객체 묶음. 설정 값이 바뀌면 settings 속성만 갈아 끼우면 서비스도 따라간다."""

    database: Database
    words: WordRepository
    study: StudyRepository
    quiz: QuizRepository
    settings: Settings
    settings_path: Path
    study_service: StudyService
    quiz_service: QuizService
    word_service: WordService

    @classmethod
    def open(cls, db_path: Path = DB_PATH, settings_path: Path = CONFIG_PATH) -> "AppContext":
        database = Database(db_path)
        settings = load_settings(settings_path)
        words = WordRepository(database)
        study = StudyRepository(database)
        quiz = QuizRepository(database)
        context = cls(
            database=database,
            words=words,
            study=study,
            quiz=quiz,
            settings=settings,
            settings_path=settings_path,
            study_service=None,  # type: ignore[arg-type]  # 아래에서 바로 채운다
            quiz_service=None,  # type: ignore[arg-type]
            word_service=WordService(words),
        )
        # 서비스는 항상 현재 설정을 읽도록 람다로 넘긴다
        wrong_provider = lambda: quiz.wrong_word_ids(WRONG_WORD_POOL_SIZE)  # noqa: E731
        context.study_service = StudyService(words, study, lambda: context.settings, wrong_provider)
        context.quiz_service = QuizService(words, quiz, lambda: context.settings, random.Random())
        return context

    def load_default_words_if_empty(self) -> str | None:
        """단어 테이블이 비어 있고 data/words.csv가 있으면 자동으로 가져온다. 메시지를 돌려준다."""
        if self.words.count() > 0 or not WORDS_CSV_PATH.exists():
            return None
        count, errors = self.import_words_csv(WORDS_CSV_PATH)
        return f"기본 단어 {count}개를 불러왔습니다." + (f" (오류 {len(errors)}건)" if errors else "")

    def import_words_csv(self, path: Path) -> tuple[int, list[str]]:
        """CSV를 읽어 DB에 반영한다. 반환값은 (저장 개수, 오류 메시지 목록)."""
        words, errors = load_words_from_csv(path)
        if not words:
            return 0, errors
        if words[0].id == SIMPLE_ID_PLACEHOLDER:
            return self._import_simple_words(words, errors)
        try:
            count = self.words.upsert_many(words)
        except sqlite3.IntegrityError as error:
            return 0, errors + [f"DB 저장 실패: {error}"]
        return count, errors

    def _import_simple_words(self, words: list[Word], errors: list[str]) -> tuple[int, list[str]]:
        """영단어·뜻 형식: DB에 이미 있는 영단어(대소문자 무시)는 건너뛰고, 나머지에 새 번호를 준다 (VOCA-FR-003)."""
        existing = {word.word.lower() for word in self.words.list_all()}
        next_number = self.words.next_id()
        to_add: list[Word] = []
        for word in words:
            if word.word.lower() in existing:
                errors.append(f"'{word.word}': 이미 있는 단어라 건너뜀")
                continue
            existing.add(word.word.lower())
            to_add.append(replace(word, id=next_number))
            next_number += 1
        try:
            count = self.words.upsert_many(to_add) if to_add else 0
        except sqlite3.IntegrityError as error:
            return 0, errors + [f"DB 저장 실패: {error}"]
        return count, errors

    def export_words_csv(self, path: Path) -> int:
        words = self.words.list_all()
        save_words_to_csv(path, words)
        return len(words)

    def update_settings(self, settings: Settings) -> None:
        save_settings(self.settings_path, settings)
        self.settings = settings

    def now(self) -> datetime:
        return datetime.now()

    def close(self) -> None:
        self.database.close()
