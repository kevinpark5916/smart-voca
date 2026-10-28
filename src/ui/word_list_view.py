#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 목록 탭: 검색, 정렬, 상세 보기, CSV 불러오기·저장 (FR-02)
# 파일 위치: src/ui/word_list_view.py
from pathlib import Path

from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from paths import DATA_DIR, WORDS_CSV_PATH
from ui.theme import scaled
from ui.word_table_model import WordTableModel
from ui.word_detail_dialog import WordDetailDialog

# 열 너비는 고정값으로 준다. 내용에 맞추면 2000행에서 화면이 멈춘다.
COLUMN_WIDTHS = [60, 140, 70, 220, 420, 60]


class WordListView(QWidget):
    """단어 전체를 표로 보여 주고, 검색·정렬하며, CSV 파일로 불러오거나 저장한다."""

    def __init__(self, context: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self._context = context
        self._model = WordTableModel()
        # 검색과 정렬은 원본 모델을 감싸는 프록시가 맡는다 (원본 데이터는 그대로 둔다)
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # 모든 열에서 검색
        self._proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self._search = QLineEdit()
        self._search.setPlaceholderText("단어, 품사, 뜻, 예문에서 검색")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._proxy.setFilterFixedString)
        self._count_label = QLabel()

        load_button = QPushButton("CSV 불러오기")
        load_button.clicked.connect(self._load_csv)
        save_button = QPushButton("CSV 저장")
        save_button.clicked.connect(self._save_csv)
        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.refresh)

        top = QHBoxLayout()
        top.addWidget(self._search, stretch=1)
        top.addWidget(self._count_label)
        for button in (load_button, save_button, refresh_button):
            top.addWidget(button)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSortingEnabled(True)
        self._table.doubleClicked.connect(self._show_detail)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        for column, width in enumerate(COLUMN_WIDTHS):
            header.resizeSection(column, scaled(width))
        header.setStretchLastSection(True)
        self._table.verticalHeader().setDefaultSectionSize(scaled(24))
        # 검색으로 행이 걸러지면 개수 표시를 갱신한다
        for signal in (self._proxy.layoutChanged, self._proxy.rowsInserted, self._proxy.rowsRemoved, self._proxy.modelReset):
            signal.connect(self._update_count)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self._table)

    def refresh(self) -> None:
        """DB의 단어 목록을 다시 읽어 표에 넣는다. 검색어는 유지된다."""
        self._model.set_words(self._context.words.list_all())
        self._update_count()

    def _update_count(self, *_args) -> None:
        self._count_label.setText(f"{self._proxy.rowCount()} / {self._model.rowCount()}개")

    def _show_detail(self, index) -> None:
        """행을 더블클릭하면 단어 상세(뜻, 예문, 시험 이력)를 보여 준다."""
        source_row = self._proxy.mapToSource(index).row()
        word = self._model.word_at(source_row)
        WordDetailDialog(self._context, word, self).exec()

    def _load_csv(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "단어 CSV 불러오기", str(DATA_DIR), "CSV 파일 (*.csv)")
        if not file_name:
            return
        count, errors = self._context.import_words_csv(Path(file_name))
        message = f"{count}개 단어를 저장했습니다."
        if errors:
            shown = "\n".join(errors[:10])
            more = f"\n... 외 {len(errors) - 10}건" if len(errors) > 10 else ""
            message += f"\n\n건너뛴 행 {len(errors)}건:\n{shown}{more}"
        QMessageBox.information(self, "불러오기 결과", message)
        self.refresh()

    def _save_csv(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(self, "단어 CSV 저장", str(DATA_DIR / "words_export.csv"), "CSV 파일 (*.csv)")
        if not file_name:
            return
        target = Path(file_name)
        # NFR-04: 원본 단어 파일은 앱이 덮어쓰지 않는다
        if target.resolve() == WORDS_CSV_PATH.resolve():
            QMessageBox.warning(self, "저장 취소", "원본 data/words.csv는 덮어쓰지 않습니다. 다른 이름을 선택하세요.")
            return
        count = self._context.export_words_csv(target)
        QMessageBox.information(self, "저장 완료", f"{count}개 단어를 저장했습니다.\n{target}")
