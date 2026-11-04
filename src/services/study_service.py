#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 암기 흐름 조율 서비스: 세션 시작·이어 하기·답 기록 (FR-03, FR-04)
# 파일 위치: src/services/study_service.py
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from config.settings import Settings
from models.word import Word
from storage.study_repository import StudyRepository
from storage.word_repository import WordRepository
from study.study_plan import build_day_plan


@dataclass(frozen=True)
class StudyCard:
    """화면에 보여 줄 카드 한 장."""

    record_id: int
    word: Word
    kind: str  # 'new' 또는 'review'
    result: str | None  # None이면 아직 답하지 않음


@dataclass(frozen=True)
class StudySession:
    """오늘(N일차) 암기 세션의 현재 상태."""

    session_id: int
    day_no: int
    cards: tuple[StudyCard, ...]

    @property
    def is_finished(self) -> bool:
        return all(card.result is not None for card in self.cards)

    @property
    def answered_count(self) -> int:
        return sum(1 for card in self.cards if card.result is not None)

    def next_pending_index(self) -> int | None:
        """아직 답하지 않은 첫 카드의 위치. 다 끝났으면 None."""
        for index, card in enumerate(self.cards):
            if card.result is None:
                return index
        return None


class StudyService:
    """암기 세션의 시작, 이어 하기, 답 기록을 한곳에서 처리한다."""

    def __init__(
        self,
        words: WordRepository,
        study: StudyRepository,
        settings_provider: Callable[[], Settings],
    ):
        self._words = words
        self._study = study
        self._settings_provider = settings_provider

    def start_or_resume(self, now: datetime) -> StudySession | None:
        """끝나지 않은 세션이 있으면 이어 하고, 없으면 다음 일차를 새로 만든다.

        모든 단어를 다 외웠으면 None을 돌려준다.
        """
        unfinished = self._study.find_unfinished_session()
        if unfinished:
            session_id, day_no = unfinished
            return self.load(session_id, day_no)

        all_words = self._words.list_all()
        if not all_words:
            return None
        settings = self._settings_provider()
        day_no = self._study.last_day_no() + 1
        if (day_no - 1) * settings.daily_new_count >= len(all_words):
            return None

        previous_session_id = self._study.last_finished_session_id()
        review_ids = self._study.again_word_ids(previous_session_id) if previous_session_id else []
        plan = build_day_plan(all_words, day_no, settings, review_ids)
        session_id = self._study.create_session(
            day_no, [(item.word.id, item.kind) for item in plan], now
        )
        return self.load(session_id, day_no)

    def answer(self, session: StudySession, record_id: int, result: str, now: datetime) -> StudySession:
        """현재 카드에 알았음/다시를 기록하고 갱신된 세션을 돌려준다. 마지막 카드면 세션을 끝낸다."""
        self._study.set_result(record_id, result, now)
        updated = self.load(session.session_id, session.day_no)
        if updated.is_finished:
            self._study.finish_session(session.session_id, now)
        return updated

    def undo_last(self, session: StudySession) -> StudySession:
        """가장 마지막으로 답한 카드의 응답을 지운다. 끝난 세션이었으면 다시 연다.

        화면에 보이는 세션은 항상 가장 최근 세션이므로, 이 함수는 현재 세션 안에서만 동작한다.
        """
        answered = [card for card in session.cards if card.result is not None]
        if not answered:
            return session
        self._study.clear_result(answered[-1].record_id)
        self._study.reopen_session(session.session_id)
        return self.load(session.session_id, session.day_no)

    def load(self, session_id: int, day_no: int) -> StudySession:
        records = self._study.get_records(session_id)
        words_by_id = self._words.get_by_ids([record.word_id for record in records])
        cards = tuple(
            StudyCard(
                record_id=record.record_id,
                word=words_by_id[record.word_id],
                kind=record.kind,
                result=record.result,
            )
            for record in records
        )
        return StudySession(session_id=session_id, day_no=day_no, cards=cards)
