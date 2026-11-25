#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-25 - SmartVoca - 단어 추가·수정·삭제 규칙과 영단어·뜻 CSV 가져오기 테스트 (VOCA-FR-001, VOCA-FR-002, VOCA-FR-003)
# 파일 위치: tests/test_word_edit.py
from datetime import datetime

import pytest

from app_context import AppContext
from services.word_service import WordService
from storage.database import Database
from storage.word_repository import WordRepository


@pytest.fixture
def words(tmp_path):
    database = Database(tmp_path / "edit.db")
    yield WordRepository(database)
    database.close()


def test_add_assigns_next_number_and_saves(words):
    service = WordService(words)
    words.upsert_many([])  # 빈 저장소
    added = service.add({"word": "apple", "meaning": "사과", "pos": "n.", "example": "An apple.", "level": 2})
    assert added.id == 1
    assert words.get_by_id(1).word == "apple"


def test_add_rejects_duplicate_ignoring_case(words):
    service = WordService(words)
    service.add({"word": "Apple", "meaning": "사과"})
    with pytest.raises(ValueError, match="이미 있는 단어"):
        service.add({"word": "apple", "meaning": "사과2"})


def test_add_requires_word_and_meaning(words):
    service = WordService(words)
    with pytest.raises(ValueError, match="영단어"):
        service.add({"word": "  ", "meaning": "뜻"})
    with pytest.raises(ValueError, match="뜻"):
        service.add({"word": "dog", "meaning": ""})


def test_level_must_be_in_range(words):
    service = WordService(words)
    with pytest.raises(ValueError, match="단계"):
        service.add({"word": "dog", "meaning": "개", "level": 0})


def test_update_changes_fields_and_allows_same_word(words):
    service = WordService(words)
    first = service.add({"word": "cat", "meaning": "고양이"})
    updated = service.update(first.id, {"word": "cat", "meaning": "고양이, 괭이"})
    assert updated.meaning == "고양이, 괭이"
    assert words.get_by_id(first.id).meaning == "고양이, 괭이"


def test_update_rejects_taking_another_words_text(words):
    service = WordService(words)
    service.add({"word": "cat", "meaning": "고양이"})
    second = service.add({"word": "dog", "meaning": "개"})
    with pytest.raises(ValueError, match="이미 있는 단어"):
        service.update(second.id, {"word": "CAT", "meaning": "개"})


def test_delete_without_records_removes_word(words):
    service = WordService(words)
    added = service.add({"word": "bird", "meaning": "새"})
    service.delete(added.id)
    assert words.get_by_id(added.id) is None


def test_delete_refused_when_study_record_exists(tmp_path):
    context = AppContext.open(db_path=tmp_path / "rec.db", settings_path=tmp_path / "config.json")
    try:
        context.word_service.add({"word": "fish", "meaning": "물고기"})
        context.study.create_session(1, [(1, "new")], datetime(2026, 11, 25, 9, 0))
        with pytest.raises(ValueError, match="기록이 있는 단어"):
            context.word_service.delete(1)
    finally:
        context.close()


def test_simple_csv_gets_new_numbers_and_skips_existing(tmp_path):
    context = AppContext.open(db_path=tmp_path / "simple.db", settings_path=tmp_path / "config.json")
    try:
        context.word_service.add({"word": "apple", "meaning": "사과"})
        path = tmp_path / "simple.csv"
        path.write_text("영단어,뜻\nbanana,바나나\nAPPLE,사과2\ncherry,체리\n", encoding="utf-8-sig")
        count, errors = context.import_words_csv(path)
        assert count == 2
        assert any("APPLE" in error or "건너뜀" in error for error in errors)
        assert context.words.get_by_id(2).word == "banana"
        assert context.words.get_by_id(3).word == "cherry"
    finally:
        context.close()


def test_simple_csv_reports_duplicate_inside_file(tmp_path):
    context = AppContext.open(db_path=tmp_path / "dup.db", settings_path=tmp_path / "config.json")
    try:
        path = tmp_path / "dup.csv"
        path.write_text("word,meaning\nkiwi,키위\nKIWI,키위2\n", encoding="utf-8-sig")
        count, errors = context.import_words_csv(path)
        assert count == 1
        assert any("중복" in error for error in errors)
    finally:
        context.close()
