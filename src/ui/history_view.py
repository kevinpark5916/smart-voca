#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 이력 탭: 시험 이력(문항 상세 포함)과 암기 이력 조회 (FR-07)
# 파일 위치: src/ui/history_view.py
from datetime import date, timedelta

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from ui.list_table_model import ListTableModel

HISTORY_LIMIT = 300  # 목록에 보여 줄 최대 세션 수 (최근 것부터)
DEFAULT_DAYS = 30  # 처음 열 때 보여 줄 기간 (최근 며칠)
ALL_START = "0001-01-01"
ALL_END = "9999-12-31"


def format_time(stored: str) -> str:
    """저장된 ISO 시각 'YYYY-MM-DDTHH:MM:SS'를 'YYYY-MM-DD HH:MM'으로 줄인다."""
    return stored[:16].replace("T", " ")


def format_direction(direction: str) -> str:
    return {"ko_en": "한→영", "en_ko": "영→한", "mixed": "혼합"}.get(direction, direction)


def format_type(question_type: str) -> str:
    return {"short": "단답형", "choice": "4지선다", "ox": "OX", "mixed": "혼합"}.get(question_type, question_type)


class HistoryView(QWidget):
    """시험 이력을 고르면 문항별 응답을 아래에 보여 주고, 암기 이력은 따로 본다."""

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self._context = context
        self._session_ids: list[int] = []  # 시험 이력 표의 행 순서대로 세션 id
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        today = date.today()
        self._start_edit = QDateEdit(QDate(*(today - timedelta(days=DEFAULT_DAYS)).timetuple()[:3]))
        self._end_edit = QDateEdit(QDate(today.year, today.month, today.day))
        for edit in (self._start_edit, self._end_edit):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("yyyy-MM-dd")
        search_button = QPushButton("기간 조회")
        search_button.clicked.connect(self.refresh)
        all_button = QPushButton("전체 보기")
        all_button.clicked.connect(self._show_all)
        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.refresh)
        top = QHBoxLayout()
        top.addWidget(QLabel("기간"))
        top.addWidget(self._start_edit)
        top.addWidget(QLabel("~"))
        top.addWidget(self._end_edit)
        top.addWidget(search_button)
        top.addWidget(all_button)
        top.addStretch(1)
        top.addWidget(refresh_button)

        # 시험 이력: 세션 목록 + 선택한 세션의 문항 상세
        self._quiz_model = ListTableModel(["시작 시각", "방향", "유형", "문제 수", "정답", "정답률"])
        self._quiz_table = self._make_table(self._quiz_model)
        self._quiz_table.selectionModel().currentRowChanged.connect(self._show_selected_quiz)
        self._answer_model = ListTableModel(["시각", "단어", "문제", "정답", "내 답", "결과"])
        self._answer_table = self._make_table(self._answer_model)
        self._detail_label = QLabel("시험을 고르면 문항별 응답이 보입니다.")

        quiz_tab = QWidget()
        quiz_layout = QVBoxLayout(quiz_tab)
        quiz_layout.addWidget(self._quiz_table, stretch=1)
        quiz_layout.addWidget(self._detail_label)
        quiz_layout.addWidget(self._answer_table, stretch=1)

        # 암기 이력: 일차별 요약
        self._study_model = ListTableModel(["일차", "시작 시각", "상태", "카드 수", "알았음", "다시 보기"])
        self._study_table = self._make_table(self._study_model)

        tabs = QTabWidget()
        tabs.addTab(quiz_tab, "시험 이력")
        tabs.addTab(self._study_table, "암기 이력")

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(tabs)

    @staticmethod
    def _make_table(model: ListTableModel) -> QTableView:
        table = QTableView()
        table.setModel(model)
        table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        return table

    def _selected_range(self) -> tuple[str, str]:
        start = self._start_edit.date().toPyDate().isoformat()
        end = self._end_edit.date().toPyDate().isoformat()
        return start, end

    def _show_all(self) -> None:
        self._start_edit.setDate(QDate(1, 1, 1))
        self._end_edit.setDate(QDate(9999, 12, 31))
        self.refresh()

    def refresh(self) -> None:
        """선택한 기간의 이력을 DB에서 다시 읽는다. 시험이 끝난 뒤 탭을 열면 자동으로 호출된다."""
        start, end = self._selected_range()
        quiz_sessions = self._context.quiz.list_sessions(HISTORY_LIMIT, start, end)
        self._session_ids = [session.session_id for session in quiz_sessions]
        self._quiz_model.set_rows(
            [
                (
                    format_time(session.started_at),
                    format_direction(session.direction),
                    format_type(session.question_type),
                    session.total,
                    session.correct,
                    f"{session.correct / session.answers:.0%}" if session.answers else "-",
                )
                for session in quiz_sessions
            ]
        )
        self._answer_model.set_rows([])
        self._detail_label.setText("시험을 고르면 문항별 응답이 보입니다.")

        study_sessions = self._context.study.list_sessions(HISTORY_LIMIT, start, end)
        self._study_model.set_rows(
            [
                (
                    session.day_no,
                    format_time(session.started_at),
                    "완료" if session.finished else "진행 중",
                    session.total,
                    session.know_count,
                    session.again_count,
                )
                for session in study_sessions
            ]
        )

    def _show_selected_quiz(self, current, _previous) -> None:
        if not current.isValid():
            return
        session_id = self._session_ids[current.row()]
        answers = self._context.quiz.session_answers(session_id)
        self._answer_model.set_rows(
            [
                (
                    format_time(answer.answered_at),
                    answer.word,
                    answer.prompt,
                    answer.expected,
                    answer.user_answer or "(빈 답)",
                    "정답" if answer.is_correct else "오답",
                )
                for answer in answers
            ]
        )
        correct = sum(1 for answer in answers if answer.is_correct)
        self._detail_label.setText(f"선택한 시험: {correct} / {len(answers)} 정답")
