#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 홈 탭: 오늘 할 일, 전체 진도, 연속 학습일, 최근 정답률 (FR-07, FR-08)
# 파일 위치: src/ui/home_view.py
from datetime import date, timedelta

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from app_context import AppContext
from ui.theme import scaled

TAB_STUDY, TAB_QUIZ, TAB_HISTORY, TAB_WORDS = 1, 2, 3, 4  # 메인 창의 탭 번호
RECENT_QUIZ_COUNT = 5  # 정답률을 계산할 최근 시험 수


def compute_streak(study_dates: list[str], today: date) -> int:
    """연속 학습일 수. 오늘 학습했으면 오늘부터, 아니면 어제부터 거꾸로 센다.

    study_dates는 'YYYY-MM-DD' 문자열 목록이다 (순서는 상관없다).
    """
    days = {date.fromisoformat(value) for value in study_dates}
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


class HomeView(QWidget):
    """앱을 열면 가장 먼저 보이는 화면. 버튼으로 각 탭으로 이동한다."""

    navigate = pyqtSignal(int)  # 이동할 탭 번호

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self._context = context
        self._summary = ""
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self._title = QLabel()
        self._title.setStyleSheet(f"font-size: {scaled(26)}px; font-weight: bold;")
        self._plan = QLabel()
        self._plan.setStyleSheet(f"font-size: {scaled(17)}px;")
        self._progress = QProgressBar()
        self._progress_text = QLabel()
        self._progress_text.setStyleSheet(f"font-size: {scaled(14)}px; color: #555;")
        self._streak = QLabel()
        self._streak.setStyleSheet(f"font-size: {scaled(16)}px;")
        self._accuracy = QLabel()
        self._accuracy.setStyleSheet(f"font-size: {scaled(16)}px;")

        study_button = self._make_nav_button("오늘 암기하기", TAB_STUDY)
        quiz_button = self._make_nav_button("시험 보기", TAB_QUIZ)
        history_button = self._make_nav_button("이력 보기", TAB_HISTORY)
        words_button = self._make_nav_button("단어 목록", TAB_WORDS)
        buttons = QHBoxLayout()
        for button in (study_button, quiz_button, history_button, words_button):
            buttons.addWidget(button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._plan)
        layout.addSpacing(12)
        layout.addWidget(self._progress)
        layout.addWidget(self._progress_text)
        layout.addSpacing(12)
        layout.addWidget(self._streak)
        layout.addWidget(self._accuracy)
        layout.addStretch(1)
        layout.addLayout(buttons)

    def _make_nav_button(self, text: str, tab_index: int) -> QPushButton:
        button = QPushButton(text)
        button.setStyleSheet(f"font-size: {scaled(15)}px; padding: 12px;")
        button.clicked.connect(lambda: self.navigate.emit(tab_index))
        return button

    def summary_text(self) -> str:
        """상태바에 쓸 한 줄 요약."""
        return self._summary

    def refresh(self) -> None:
        """DB 값을 다시 읽어 모든 표시를 갱신한다."""
        settings = self._context.settings
        total = self._context.words.count()
        studied = self._context.study.total_studied_words()
        unfinished = self._context.study.find_unfinished_session()
        day_no = unfinished[1] if unfinished else self._context.study.last_day_no() + 1
        streak = compute_streak(self._context.study.studied_dates(), date.today())

        self._title.setText("오늘의 학습")
        if total == 0:
            self._plan.setText("단어가 없습니다. '단어 목록'에서 CSV를 불러오세요.")
        elif not unfinished and (day_no - 1) * settings.daily_new_count >= total:
            self._plan.setText("모든 단어를 외웠습니다!")
        else:
            state = " (진행 중)" if unfinished else ""
            self._plan.setText(
                f"{day_no}일차{state} · 신규 최대 {settings.daily_new_count}개 · 복습 최대 {settings.daily_review_count}개"
            )

        self._progress.setRange(0, max(total, 1))
        self._progress.setValue(studied)
        percent = studied / total if total else 0
        self._progress_text.setText(f"암기한 단어 {studied} / {total}개 ({percent:.0%})")

        self._streak.setText(f"연속 학습 {streak}일" if streak else "오늘 학습을 시작해 보세요.")
        answers, correct = self._context.quiz.recent_accuracy(RECENT_QUIZ_COUNT)
        if answers:
            self._accuracy.setText(f"최근 {RECENT_QUIZ_COUNT}회 시험 정답률 {correct / answers:.0%} ({answers}문항)")
        else:
            self._accuracy.setText("아직 시험 기록이 없습니다.")

        self._summary = f"{day_no}일차 · 암기 {studied}/{total} · 연속 {streak}일"
