#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 보고서 대화상자: 기간 선택 후 HTML 생성·열기 (FR-08)
# 파일 위치: src/ui/report_dialog.py
import webbrowser
from datetime import date, datetime

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from paths import REPORT_DIR
from report.report_builder import save_report_html
from report.report_data import build_report_summary


class ReportDialog(QDialog):
    """기간을 고르면 요약을 계산해 HTML 파일로 저장하고, 브라우저로 연다."""

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self._context = context
        self.setWindowTitle("학습 보고서")

        today = date.today()
        self._start_edit = QDateEdit(QDate(today.year, today.month, 1))
        self._end_edit = QDateEdit(QDate(today.year, today.month, today.day))
        for edit in (self._start_edit, self._end_edit):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("yyyy-MM-dd")

        form = QFormLayout()
        form.addRow("시작일", self._start_edit)
        form.addRow("종료일", self._end_edit)

        create_button = QPushButton("보고서 만들기")
        create_button.clicked.connect(self._create_report)
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(create_button)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def _create_report(self) -> None:
        start = self._start_edit.date().toPyDate()
        end = self._end_edit.date().toPyDate()
        if start > end:
            QMessageBox.warning(self, "기간 오류", "시작일이 종료일보다 늦습니다.")
            return
        now = datetime.now()
        summary = build_report_summary(self._context.study, self._context.quiz, start, end)
        path = save_report_html(summary, REPORT_DIR, now)
        webbrowser.open(path.as_uri())
        QMessageBox.information(self, "보고서 저장", f"보고서를 저장했습니다.\n{path}")
