#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 암기 탭: 카드 화면, 집계, 단축키, 되돌리기, 다음 일차 시작 (FR-03, FR-04)
# 파일 위치: src/ui/study_view.py
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from services.study_service import StudySession
from storage.study_repository import RESULT_AGAIN, RESULT_KNOW
from study.study_plan import KIND_REVIEW
from ui.theme import scaled


class StudyView(QWidget):
    """카드를 뒤집어 뜻을 확인한 뒤 '알았음' 또는 '다시 보기'로 표시한다."""

    # 답하거나 되돌릴 때마다 발생한다. 상태바 갱신에 쓴다.
    progress_changed = pyqtSignal()

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self._context = context
        self._session: StudySession | None = None
        self._revealed = False  # 현재 카드의 뜻을 봤는지 여부
        self._example_visible = False  # 예문 표시 여부 (뜻을 본 뒤 따로 연다)
        self._build_ui()
        self._build_shortcuts()
        self.reload()

    def _build_ui(self) -> None:
        self._header = QLabel()
        self._header.setStyleSheet(f"font-size: {scaled(16)}px; font-weight: bold;")
        self._progress = QProgressBar()
        self._counts = QLabel()
        self._counts.setStyleSheet(f"font-size: {scaled(14)}px; color: #555;")

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            "#card { border: 2px solid #8a8fa3; border-radius: 16px; padding: 16px; }"
        )
        self._card_word = QLabel()
        self._card_word.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._card_word.setStyleSheet(f"font-size: {scaled(40)}px; font-weight: bold;")
        self._card_detail = QLabel()
        self._card_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._card_detail.setWordWrap(True)
        self._card_detail.setStyleSheet(f"font-size: {scaled(18)}px;")
        self._card_example = QLabel()
        self._card_example.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._card_example.setWordWrap(True)
        self._card_example.setStyleSheet(f"font-size: {scaled(15)}px; color: #555;")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(self._card_word)
        card_layout.addWidget(self._card_detail)
        card_layout.addWidget(self._card_example)

        self._reveal_button = self._make_button("뒤집기 (Space)", self._reveal)
        self._example_button = self._make_button("예문 보기 (E)", self._toggle_example)
        self._again_button = self._make_button("다시 보기 (Backspace · 1)", lambda: self._answer(RESULT_AGAIN))
        self._know_button = self._make_button("알았음 (Enter · 2)", lambda: self._answer(RESULT_KNOW))
        self._undo_button = self._make_button("되돌리기 (Ctrl+Z)", self._undo)
        self._next_day_button = self._make_button("다음 일차 시작", self.reload)
        self._next_day_button.hide()

        buttons = QHBoxLayout()
        buttons.addWidget(self._undo_button)
        buttons.addWidget(self._example_button)
        buttons.addStretch(1)
        buttons.addWidget(self._reveal_button)
        buttons.addWidget(self._again_button)
        buttons.addWidget(self._know_button)

        hint = QLabel("단축키: Space 뒤집기 · E 예문 · Backspace 다시 보기 · Enter 알았음 · Ctrl+Z 되돌리기")
        hint.setStyleSheet(f"font-size: {scaled(12)}px; color: #888;")

        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addWidget(self._progress)
        layout.addWidget(self._counts)
        layout.addStretch(1)
        layout.addWidget(card)
        layout.addStretch(1)
        layout.addLayout(buttons)
        layout.addWidget(self._next_day_button, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(hint)

    @staticmethod
    def _make_button(text: str, slot) -> QPushButton:
        """버튼을 만든다. 포커스를 받지 않게 해서 키 입력이 단축키로만 쓰이게 한다."""
        button = QPushButton(text)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.clicked.connect(slot)
        return button

    def _build_shortcuts(self) -> None:
        """단축키: Space 뒤집기, E 예문, Backspace·1 다시 보기, Enter·2 알았음, Ctrl+Z 되돌리기.

        창 전체 범위(WindowShortcut)로 등록하고, 암기 탭이 보일 때만 실행한다.
        위젯 범위로 두면 포커스가 탭 안에 있어야만 동작해서 처음에는 키가 먹히지 않는다.
        """
        bindings = [
            ("Space", self._reveal),
            ("E", self._toggle_example),
            ("Backspace", lambda: self._answer(RESULT_AGAIN)),
            ("1", lambda: self._answer(RESULT_AGAIN)),
            ("Return", lambda: self._answer(RESULT_KNOW)),
            ("Enter", lambda: self._answer(RESULT_KNOW)),  # 숫자패드 Enter
            ("2", lambda: self._answer(RESULT_KNOW)),
            ("Ctrl+Z", self._undo),
        ]
        for key, slot in bindings:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(self._shortcut_action(slot))

    def _shortcut_action(self, slot):
        """암기 탭이 화면에 보일 때만 slot을 실행하는 함수를 만든다."""
        def run() -> None:
            if self.isVisible():
                slot()
        return run

    def reload(self) -> None:
        """끝나지 않은 세션을 이어 하거나 다음 일차를 시작한다."""
        self._session = self._context.study_service.start_or_resume(datetime.now())
        self._show_current_card()

    def _show_current_card(self) -> None:
        self._revealed = False
        self._example_visible = False
        self._next_day_button.hide()
        self._card_example.setText("")
        self.progress_changed.emit()
        if self._session is None:
            message = "단어가 없습니다. '단어 목록' 탭에서 CSV를 불러오세요." if self._context.words.count() == 0 else "모든 단어를 외웠습니다."
            self._header.setText(message)
            self._counts.setText("")
            self._card_word.setText("")
            self._card_detail.setText("")
            self._set_card_controls(enabled=False)
            self._undo_button.setEnabled(False)
            return
        self._progress.setRange(0, len(self._session.cards))
        self._progress.setValue(self._session.answered_count)
        self._undo_button.setEnabled(self._session.answered_count > 0)
        self._counts.setText(self._count_text())
        index = self._session.next_pending_index()
        if index is None:
            self._header.setText(f"{self._session.day_no}일차 암기 완료")
            self._card_word.setText("수고하셨습니다!")
            self._card_detail.setText("마지막 답을 되돌리려면 Ctrl+Z를 누르세요.")
            self._set_card_controls(enabled=False)
            self._next_day_button.show()
            return
        card = self._session.cards[index]
        kind_label = "복습" if card.kind == KIND_REVIEW else "신규"
        self._header.setText(f"{self._session.day_no}일차 · {kind_label} · {index + 1} / {len(self._session.cards)}")
        self._card_word.setText(card.word.word)
        self._card_detail.setText("")
        self._set_card_controls(enabled=True, revealed=False)

    def _count_text(self) -> str:
        """이번 일차의 집계: 알았음, 다시 보기, 남은 카드 수."""
        cards = self._session.cards
        know = sum(1 for card in cards if card.result == RESULT_KNOW)
        again = sum(1 for card in cards if card.result == RESULT_AGAIN)
        remaining = len(cards) - know - again
        return f"알았음 {know}  ·  다시 보기 {again}  ·  남음 {remaining}"

    def _reveal(self) -> None:
        index = self._session.next_pending_index() if self._session else None
        if index is None or self._revealed:
            return
        card = self._session.cards[index]
        self._card_detail.setText(f"{card.word.pos}  {card.word.meaning}")
        self._revealed = True
        self._set_card_controls(enabled=True, revealed=True)

    def _toggle_example(self) -> None:
        """뜻을 본 뒤에만 예문을 연다. 예문을 열면 버튼 글자가 '예문 숨기기'로 바뀐다."""
        index = self._session.next_pending_index() if self._session else None
        if index is None or not self._revealed:
            return
        self._example_visible = not self._example_visible
        example = self._session.cards[index].word.example
        self._card_example.setText(example if self._example_visible else "")
        self._example_button.setText("예문 숨기기 (E)" if self._example_visible else "예문 보기 (E)")

    def _answer(self, result: str) -> None:
        """뜻을 본 뒤에만 답할 수 있다. 뒤집기 전에는 아무 일도 하지 않는다."""
        index = self._session.next_pending_index() if self._session else None
        if index is None or not self._revealed:
            return
        card = self._session.cards[index]
        self._session = self._context.study_service.answer(self._session, card.record_id, result, datetime.now())
        self._show_current_card()

    def _undo(self) -> None:
        if self._session is None or self._session.answered_count == 0:
            return
        self._session = self._context.study_service.undo_last(self._session)
        self._show_current_card()

    def _set_card_controls(self, enabled: bool, revealed: bool = False) -> None:
        """뜻을 보기 전에는 '알았음/다시'를 막아 충분히 떠올린 뒤 답하도록 한다."""
        self._reveal_button.setEnabled(enabled and not revealed)
        self._example_button.setEnabled(enabled and revealed)
        self._know_button.setEnabled(enabled and revealed)
        self._again_button.setEnabled(enabled and revealed)
        self._example_button.setText("예문 보기 (E)")
