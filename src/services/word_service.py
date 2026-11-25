#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-25 - SmartVoca - 단어 추가·수정·삭제 규칙: 입력 검사, 중복 검사, 기록이 있는 단어 보호 (VOCA-FR-001, VOCA-FR-002)
# 파일 위치: src/services/word_service.py
from models.word import Word
from storage.word_repository import WordRepository

MAX_LEVEL = 9  # 표시용 단계의 최대값 (level은 정렬에 쓰지 않는다)


class WordService:
    """단어 편집 규칙을 한곳에 둔다. 웹 API와 데스크톱 화면이 함께 쓴다."""

    def __init__(self, words: WordRepository):
        self._words = words

    def add(self, data: dict) -> Word:
        """새 단어를 추가하고 저장된 단어를 돌려준다. 같은 영단어(대소문자 무시)는 막는다."""
        word = self._build(self._words.next_id(), data)
        self._ensure_unique(word, exclude_id=None)
        self._words.insert_word(word)
        return word

    def update(self, word_id: int, data: dict) -> Word:
        """단어 내용을 바꾼다. 기존 시험·암기 기록은 그대로 남는다 (시험 문항은 당시 값을 스냅샷으로 가진다)."""
        if self._words.get_by_id(word_id) is None:
            raise ValueError("해당 단어를 찾을 수 없습니다")
        word = self._build(word_id, data)
        self._ensure_unique(word, exclude_id=word_id)
        self._words.update_word(word)
        return word

    def delete(self, word_id: int) -> None:
        """단어를 지운다. 학습·시험 기록이 있으면 이력 보존을 위해 막는다."""
        if self._words.get_by_id(word_id) is None:
            raise ValueError("해당 단어를 찾을 수 없습니다")
        if self._words.has_study_or_quiz_records(word_id):
            raise ValueError("학습 또는 시험 기록이 있는 단어는 지울 수 없습니다. 뜻이나 예문을 고쳐 주세요.")
        self._words.delete_word(word_id)

    @staticmethod
    def _build(word_id: int, data: dict) -> Word:
        """입력 값을 검사해 Word를 만든다. 빈 영단어나 뜻은 거부한다."""
        text = str(data.get("word", "")).strip()
        meaning = str(data.get("meaning", "")).strip()
        if not text:
            raise ValueError("영단어를 입력해 주세요")
        if not meaning:
            raise ValueError("뜻을 입력해 주세요")
        raw_level = data.get("level")
        try:
            level = 1 if raw_level in (None, "") else int(raw_level)
        except (TypeError, ValueError) as error:
            raise ValueError("단계는 숫자여야 합니다") from error
        if not 1 <= level <= MAX_LEVEL:
            raise ValueError(f"단계는 1~{MAX_LEVEL} 사이여야 합니다")
        return Word(
            id=word_id,
            word=text,
            pos=str(data.get("pos", "") or "").strip(),
            meaning=meaning,
            example=str(data.get("example", "") or "").strip(),
            level=level,
        )

    def _ensure_unique(self, word: Word, exclude_id: int | None) -> None:
        duplicate = self._words.find_by_text_ignore_case(word.word, exclude_id=exclude_id)
        if duplicate is not None:
            raise ValueError(f"이미 있는 단어입니다: {duplicate.word} (번호 {duplicate.id})")
