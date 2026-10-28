#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 시험 탭: 설정 / 문제 / 결과 3단계 화면, 키보드 조작, 틀린 단어 재시험 (FR-05~FR-07)
# 파일 위치: src/ui/quiz_view.py
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from quiz.question import (
    DIRECTION_EN_KO,
    DIRECTION_KO_EN,
    DIRECTION_MIXED,
    TYPE_CHOICE,
    TYPE_MIXED,
    TYPE_OX,
    TYPE_SHORT,
    Question,
)
from services.quiz_service import QuizRun
from ui.list_table_model import ListTableModel
from ui.theme import scaled

PAGE_SETUP, PAGE_QUESTION, PAGE_RESULT = 0, 1, 2
CHOICE_KEYS = [Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4]

# 피드백 색상: 정답은 초록, 오답은 빨강 배경
CORRECT_STYLE = "background: #e6f4ea; color: #1b7f3b; border-radius: 8px;"
WRONG_STYLE = "background: #fce8e6; color: #b3261e; border-radius: 8px;"


class QuizView(QWidget):
    """설정 -> 문제 -> 결과 순서로 진행한다. 문항마다 바로 채점하고 결과 화면에서 틀린 단어를 모아 본다."""

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self._context = context
        self._run: QuizRun | None = None
        self._last_run: QuizRun | None = None  # 결과 화면에서 틀린 단어 재시험에 쓴다
        self._index = 0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # 문제 화면의 키 입력을 받기 위해
        self._build_ui()

    def _build_ui(self) -> None:
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_setup_page())
        self._stack.addWidget(self._build_question_page())
        self._stack.addWidget(self._build_result_page())
        layout = QVBoxLayout(self)
        layout.addWidget(self._stack)

    def _build_setup_page(self) -> QWidget:
        self._count_spin = QSpinBox()
        self._count_spin.setRange(5, 100)
        self._count_spin.setValue(self._context.settings.quiz_question_count)
        self._direction_combo = QComboBox()
        for label, value in [("한 → 영", DIRECTION_KO_EN), ("영 → 한", DIRECTION_EN_KO), ("혼합", DIRECTION_MIXED)]:
            self._direction_combo.addItem(label, value)
        self._type_combo = QComboBox()
        for label, value in [("단답형", TYPE_SHORT), ("4지선다형", TYPE_CHOICE), ("OX형", TYPE_OX), ("혼합", TYPE_MIXED)]:
            self._type_combo.addItem(label, value)

        form = QFormLayout()
        form.addRow("문제 수", self._count_spin)
        form.addRow("방향", self._direction_combo)
        form.addRow("유형", self._type_combo)
        group = QGroupBox("시험 설정")
        group.setLayout(form)

        hint = QLabel("안 본 단어, 오래된 단어, 많이 틀린 단어가 더 자주 나옵니다.")
        hint.setStyleSheet(f"font-size: {scaled(13)}px; color: #666;")
        start_button = QPushButton("시험 시작")
        start_button.setStyleSheet(f"font-size: {scaled(16)}px; padding: 12px;")
        start_button.clicked.connect(self._start)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(group)
        layout.addWidget(hint)
        layout.addWidget(start_button)
        layout.addStretch(1)
        return page

    def _build_question_page(self) -> QWidget:
        self._progress_label = QLabel()
        self._progress_label.setStyleSheet(f"font-size: {scaled(14)}px; color: #555;")
        self._prompt_label = QLabel()
        self._prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._prompt_label.setWordWrap(True)
        self._prompt_label.setStyleSheet(f"font-size: {scaled(30)}px; font-weight: bold; padding: 16px;")
        self._candidate_label = QLabel()
        self._candidate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._candidate_label.setStyleSheet(f"font-size: {scaled(22)}px; padding: 8px;")

        self._answer_edit = QLineEdit()
        self._answer_edit.setPlaceholderText("답을 입력하고 Enter")
        self._answer_edit.returnPressed.connect(self._on_return)

        self._choice_grid = QGridLayout()
        self._choice_buttons: list[QPushButton] = []
        for position in range(4):
            button = QPushButton()
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setStyleSheet(f"font-size: {scaled(16)}px; padding: 10px;")
            button.clicked.connect(lambda _, slot=position: self._submit_choice(slot))
            self._choice_grid.addWidget(button, position // 2, position % 2)
            self._choice_buttons.append(button)

        ox_row = QHBoxLayout()
        self._ox_buttons: dict[str, QPushButton] = {}
        for mark in ("O", "X"):
            button = QPushButton(mark)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setStyleSheet(f"font-size: {scaled(24)}px; padding: 12px;")
            button.clicked.connect(lambda _, value=mark: self._submit(value))
            ox_row.addWidget(button)
            self._ox_buttons[mark] = button

        self._feedback_label = QLabel()
        self._feedback_label.setWordWrap(True)
        self._feedback_label.setStyleSheet(f"font-size: {scaled(15)}px; padding: 8px;")
        self._next_button = QPushButton("다음 문제 (Enter)")
        self._next_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._next_button.clicked.connect(self._next)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._progress_label)
        layout.addWidget(self._prompt_label)
        layout.addWidget(self._candidate_label)
        layout.addWidget(self._answer_edit)
        layout.addLayout(self._choice_grid)
        layout.addLayout(ox_row)
        layout.addWidget(self._feedback_label)
        layout.addWidget(self._next_button)
        layout.addStretch(1)
        self._next_button.hide()
        return page

    def _build_result_page(self) -> QWidget:
        self._result_label = QLabel()
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setStyleSheet(f"font-size: {scaled(24)}px; font-weight: bold; padding: 12px;")
        self._wrong_model = ListTableModel(["단어", "문제", "정답", "내 답"])
        self._wrong_table = QTableView()
        self._wrong_table.setModel(self._wrong_model)
        self._wrong_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._wrong_table.horizontalHeader().setStretchLastSection(True)
        self._retry_button = QPushButton("틀린 단어만 다시 시험")
        self._retry_button.clicked.connect(self._retry_wrong)
        new_button = QPushButton("새 시험")
        new_button.clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_SETUP))

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self._retry_button)
        buttons.addWidget(new_button)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._result_label)
        layout.addWidget(self._wrong_table, stretch=1)
        layout.addLayout(buttons)
        return page

    # ----- 흐름 -----

    def _start(self) -> None:
        try:
            run = self._context.quiz_service.create_run(
                self._count_spin.value(),
                self._direction_combo.currentData(),
                self._type_combo.currentData(),
                datetime.now(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "시험 시작 실패", str(error))
            return
        self._begin(run)

    def _retry_wrong(self) -> None:
        if self._last_run is None:
            return
        try:
            run = self._context.quiz_service.create_retry_run(
                self._last_run,
                self._direction_combo.currentData(),
                self._type_combo.currentData(),
                datetime.now(),
            )
        except ValueError as error:
            QMessageBox.information(self, "재시험", str(error))
            return
        self._begin(run)

    def _begin(self, run: QuizRun) -> None:
        self._run = run
        self._index = 0
        self._stack.setCurrentIndex(PAGE_QUESTION)
        self._show_question()

    def _current_question(self) -> Question | None:
        if self._run is None or self._index >= len(self._run.questions):
            return None
        return self._run.questions[self._index]

    def _show_question(self) -> None:
        if self._run is None:
            return
        if self._index >= len(self._run.questions):
            self._finish()
            return
        question = self._run.questions[self._index]
        self._progress_label.setText(
            f"{self._index + 1} / {len(self._run.questions)}   정답 {self._run.correct_count}개"
        )
        self._prompt_label.setText(question.prompt)
        self._candidate_label.setText(question.candidate if question.question_type == TYPE_OX else "")
        self._feedback_label.setText("")
        self._feedback_label.setStyleSheet(f"font-size: {scaled(15)}px; padding: 8px;")
        self._next_button.hide()
        self._set_inputs(question)
        # 키 입력을 받을 위치로 포커스를 옮긴다
        if question.question_type == TYPE_SHORT:
            self._answer_edit.setFocus()
        else:
            self.setFocus()

    def _set_inputs(self, question: Question) -> None:
        """문제 유형에 맞는 입력 위젯만 보이게 하고, 모두 다시 누를 수 있게 만든다."""
        is_short = question.question_type == TYPE_SHORT
        self._answer_edit.setVisible(is_short)
        self._answer_edit.setEnabled(True)
        self._answer_edit.clear()
        for position, button in enumerate(self._choice_buttons):
            is_choice = question.question_type == TYPE_CHOICE
            button.setVisible(is_choice)
            button.setEnabled(True)
            if is_choice and position < len(question.choices):
                button.setText(f"{position + 1}. {question.choices[position]}")
        for button in self._ox_buttons.values():
            button.setVisible(question.question_type == TYPE_OX)
            button.setEnabled(True)

    def _disable_inputs(self) -> None:
        self._answer_edit.setEnabled(False)
        for button in self._choice_buttons + list(self._ox_buttons.values()):
            button.setEnabled(False)

    def _submit_choice(self, position: int) -> None:
        question = self._current_question()
        if question is None or position >= len(question.choices):
            return
        self._submit(question.choices[position])

    def _submit(self, user_answer: str) -> None:
        """현재 문항을 채점한다. 이미 답한 문항이면 무시한다."""
        if self._run is None or self._index >= len(self._run.questions):
            return
        if self._run.answers[self._index] is not None:
            return
        question = self._run.questions[self._index]
        is_correct = self._context.quiz_service.submit(self._run, self._index, user_answer, datetime.now())
        self._show_feedback(question, is_correct)
        self._disable_inputs()
        self._next_button.show()
        self.setFocus()

    def _show_feedback(self, question: Question, is_correct: bool) -> None:
        verdict = "정답입니다!" if is_correct else "틀렸습니다."
        # OX형은 정답이 O/X 표시이므로 단어 뜻을 함께 보여 줘야 이해하기 쉽다
        meaning_text = f"\n{question.word.word}  {question.word.meaning}\n{question.word.example}"
        self._feedback_label.setText(f"{verdict}  정답: {question.expected}{meaning_text}")
        style = CORRECT_STYLE if is_correct else WRONG_STYLE
        self._feedback_label.setStyleSheet(f"font-size: {scaled(15)}px; padding: 8px; {style}")

    def _next(self) -> None:
        if self._run is None or self._run.answers[self._index] is None:
            return
        self._index += 1
        self._show_question()

    def _on_return(self) -> None:
        """Enter: 답하기 전이면 단답형 입력을 제출하고, 답한 뒤면 다음 문제로 간다."""
        question = self._current_question()
        if question is None:
            return
        if self._run.answers[self._index] is not None:
            self._next()
        elif question.question_type == TYPE_SHORT and self._answer_edit.text().strip():
            self._submit(self._answer_edit.text())

    def keyPressEvent(self, event) -> None:  # noqa: N802  (Qt 메서드 이름 규칙)
        """문제 화면의 키보드 조작: Enter 제출/다음, 4지선다는 1~4, OX는 O/X."""
        if self._stack.currentIndex() != PAGE_QUESTION or self._run is None:
            super().keyPressEvent(event)
            return
        key = event.key()
        question = self._current_question()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_return()
            return
        if question is not None and self._run.answers[self._index] is None:
            if question.question_type == TYPE_CHOICE and key in CHOICE_KEYS:
                self._submit_choice(CHOICE_KEYS.index(key))
                return
            if question.question_type == TYPE_OX and key in (Qt.Key.Key_O, Qt.Key.Key_X):
                self._submit("O" if key == Qt.Key.Key_O else "X")
                return
        super().keyPressEvent(event)

    def _finish(self) -> None:
        if self._run is None or not self._run.is_finished:
            return
        self._context.quiz_service.finish(self._run, datetime.now())
        total = len(self._run.questions)
        correct = self._run.correct_count
        accuracy = correct / total * 100
        self._result_label.setText(f"{correct} / {total} 정답 ({accuracy:.0f}%)")
        wrong_rows = [
            (
                question.word.word,
                question.prompt,
                question.expected,
                self._run.user_answers[position] or "(빈 답)",
            )
            for position, (question, answer) in enumerate(zip(self._run.questions, self._run.answers))
            if answer is False
        ]
        self._wrong_model.set_rows(wrong_rows)
        self._retry_button.setEnabled(bool(wrong_rows))
        self._last_run = self._run
        self._run = None
        self._stack.setCurrentIndex(PAGE_RESULT)
