#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 열 이름과 값 튜플로 표를 채우는 범용 모델 (이력 탭에서 사용)
# 파일 위치: src/ui/list_table_model.py
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt


class ListTableModel(QAbstractTableModel):
    """headers 한 번 정하고, rows(값 튜플 목록)를 통째로 바꾼다."""

    def __init__(self, headers: list[str]):
        super().__init__()
        self._headers = headers
        self._rows: list[tuple] = []

    def set_rows(self, rows: list[tuple]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def row_at(self, row: int) -> tuple:
        return self._rows[row]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008  (Qt 시그니처)
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return str(self._rows[index.row()][index.column()])

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return super().headerData(section, orientation, role)
