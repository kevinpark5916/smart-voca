#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 상세 대화상자: 뜻, 예문, 시험 기록 (단어 목록 더블클릭)
# 파일 위치: src/ui/word_detail_dialog.py
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from app_context import AppContext
from models.word import Word
from ui.theme import scaled
from ui.history_view import format_time


class WordDetailDialog(QDialog):
    def __init__(self, context: AppContext, word: Word, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(word.word)
        stat = context.quiz.get_word_stats().get(word.id)

        if stat is None:
            history_text = "아직 시험을 본 적이 없습니다."
        else:
            last = format_time(stat.last_tested_at.isoformat()) if stat.last_tested_at else "-"
            history_text = f"응답 {stat.attempts}회 · 오답 {stat.wrong}회 · 마지막 시험 {last}"

        title = QLabel(word.word)
        title.setStyleSheet(f"font-size: {scaled(26)}px; font-weight: bold;")
        body = QLabel(f"{word.pos}  {word.meaning}\n\n예문: {word.example}\n\n단계: {word.level}\n\n{history_text}")
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size: {scaled(15)}px;")
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(close_button)
