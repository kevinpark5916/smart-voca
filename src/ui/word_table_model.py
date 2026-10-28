#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 목록 표의 데이터 모델 (칸마다 위젯을 만들지 않고 한 번에 교체)
# 파일 위치: src/ui/word_table_model.py
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from models.word import Word

WORD_COLUMNS = ["id", "단어", "품사", "뜻", "예문", "단계"]


class WordTableModel(QAbstractTableModel):
    """단어 목록을 표에 보여 준다.

    QTableWidget은 칸마다 항목을 만들고 열 너비를 자동 계산해서 2000행에서 매우 느리다.
    모델은 데이터만 들고 있고, 표가 보이는 칸만 값을 읽으므로 빠르다.
    """

    def __init__(self, words: list[Word] | None = None):
        super().__init__()
        self._words: list[Word] = list(words or [])

    def set_words(self, words: list[Word]) -> None:
        """전체 목록을 한 번에 바꾼다."""
        self.beginResetModel()
        self._words = list(words)
        self.endResetModel()

    def word_at(self, row: int) -> Word:
        return self._words[row]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008  (Qt 시그니처)
        return 0 if parent.isValid() else len(self._words)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(WORD_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        word = self._words[index.row()]
        values = (word.id, word.word, word.pos, word.meaning, word.example, word.level)
        if role == Qt.ItemDataRole.DisplayRole:
            return str(values[index.column()])
        if role == Qt.ItemDataRole.UserRole:
            # 정렬용 값: id와 단계는 숫자로 비교해야 10이 2보다 뒤에 온다
            return values[index.column()] if index.column() in (0, 5) else str(values[index.column()]).lower()
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return WORD_COLUMNS[section]
        return super().headerData(section, orientation, role)
