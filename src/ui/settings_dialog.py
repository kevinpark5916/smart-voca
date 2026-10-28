#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 설정 대화상자: 학습량, 시험, 가중치, 테마, 글자 크기 (FR-13, FR-22)
# 파일 위치: src/ui/settings_dialog.py
from dataclasses import replace

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from ui.theme import apply_theme


class SettingsDialog(QDialog):
    """학습량, 시험 문제 수, 가중치, 테마, 글자 크기를 바꾸고 config.json에 저장한다."""

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self._context = context
        self.setWindowTitle("설정")
        settings = context.settings

        self._daily_new = self._int_spin(1, 200, settings.daily_new_count)
        self._daily_review = self._int_spin(0, 100, settings.daily_review_count)
        self._quiz_count = self._int_spin(5, 100, settings.quiz_question_count)
        self._old_days = self._int_spin(1, 365, settings.old_days)
        self._weight_new = self._float_spin(settings.weight_new)
        self._weight_old = self._float_spin(settings.weight_old)
        self._weight_wrong = self._float_spin(settings.weight_wrong)
        self._theme = self._combo([("밝게", "light"), ("어둡게", "dark")], settings.theme)
        self._font_scale = self._combo(
            [("작게", "small"), ("보통", "normal"), ("크게", "large")], settings.font_scale
        )

        form = QFormLayout()
        form.addRow("하루 신규 단어 수", self._daily_new)
        form.addRow("하루 복습 단어 최대 수", self._daily_review)
        form.addRow("시험 문제 수 기본값", self._quiz_count)
        form.addRow("오래됨 기준 (일)", self._old_days)
        form.addRow("가중치: 시험 이력 없음", self._weight_new)
        form.addRow("가중치: 오래됨", self._weight_old)
        form.addRow("가중치: 오답률 배수", self._weight_wrong)
        form.addRow("테마", self._theme)
        form.addRow("글자 크기", self._font_scale)

        note = QLabel("글자 크기는 프로그램을 다시 시작하면 모든 화면에 적용됩니다.")
        note.setStyleSheet("color: #888;")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)

    @staticmethod
    def _int_spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin

    @staticmethod
    def _float_spin(value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 100.0)
        spin.setDecimals(1)
        spin.setSingleStep(0.5)
        spin.setValue(value)
        return spin

    @staticmethod
    def _combo(options: list[tuple[str, str]], current: str) -> QComboBox:
        combo = QComboBox()
        for label, value in options:
            combo.addItem(label, value)
        combo.setCurrentIndex(combo.findData(current))
        return combo

    def _save(self) -> None:
        new_settings = replace(
            self._context.settings,
            daily_new_count=self._daily_new.value(),
            daily_review_count=self._daily_review.value(),
            quiz_question_count=self._quiz_count.value(),
            old_days=self._old_days.value(),
            weight_new=self._weight_new.value(),
            weight_old=self._weight_old.value(),
            weight_wrong=self._weight_wrong.value(),
            theme=self._theme.currentData(),
            font_scale=self._font_scale.currentData(),
        )
        try:
            self._context.update_settings(new_settings)
        except ValueError as error:
            QMessageBox.warning(self, "설정 오류", str(error))
            return
        apply_theme(QApplication.instance(), self._context.settings)
        self.accept()
