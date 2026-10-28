#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 메인 창: 홈·암기·시험·이력·단어 목록 탭, 상태바, 창 크기 기억
# 파일 위치: src/ui/main_window.py
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QTabWidget

from app_context import AppContext
from ui.history_view import HistoryView
from ui.home_view import HomeView
from ui.quiz_view import QuizView
from ui.report_dialog import ReportDialog
from ui.settings_dialog import SettingsDialog
from ui.study_view import StudyView
from ui.word_list_view import WordListView

TAB_HOME = 0


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext):
        super().__init__()
        self._context = context
        self.setWindowTitle("SmartVoca - 스마트 보카")
        self._restore_geometry()

        self._home_view = HomeView(context)
        self._study_view = StudyView(context)
        self._history_view = HistoryView(context)
        self._tabs = QTabWidget()
        self._tabs.addTab(self._home_view, "홈")
        self._tabs.addTab(self._study_view, "암기")
        self._tabs.addTab(QuizView(context), "시험")
        self._tabs.addTab(self._history_view, "이력")
        self._tabs.addTab(WordListView(context), "단어 목록")
        self.setCentralWidget(self._tabs)

        # 홈의 버튼은 해당 탭으로 옮긴다
        self._home_view.navigate.connect(self._tabs.setCurrentIndex)
        # 암기 진행이 바뀌면 홈과 상태바를 갱신한다
        self._study_view.progress_changed.connect(self._refresh_home)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._refresh_home()

        report_action = QAction("보고서 만들기...", self)
        report_action.triggered.connect(self._open_report)
        settings_action = QAction("설정...", self)
        settings_action.triggered.connect(self._open_settings)
        tools_menu = self.menuBar().addMenu("도구")
        tools_menu.addAction(report_action)
        tools_menu.addAction(settings_action)

    def _refresh_home(self) -> None:
        self._home_view.refresh()
        self.statusBar().showMessage(self._home_view.summary_text())

    def _on_tab_changed(self, index: int) -> None:
        widget = self._tabs.widget(index)
        if widget is self._history_view:
            self._history_view.refresh()  # 시험이 끝난 뒤 열면 최신 기록이 보인다
        if index == TAB_HOME:
            self._refresh_home()

    def _restore_geometry(self) -> None:
        """마지막으로 닫았을 때의 창 크기와 위치를 복원한다. 기록이 없으면 기본 크기."""
        saved = QSettings("SmartVoca", "SmartVoca").value("geometry")
        if saved is not None:
            self.restoreGeometry(saved)
        else:
            self.resize(900, 640)

    def _open_report(self) -> None:
        ReportDialog(self._context, self).exec()

    def _open_settings(self) -> None:
        SettingsDialog(self._context, self).exec()
        self._refresh_home()

    def closeEvent(self, event) -> None:  # noqa: N802  (Qt 메서드 이름 규칙)
        QSettings("SmartVoca", "SmartVoca").setValue("geometry", self.saveGeometry())
        self._context.close()
        super().closeEvent(event)
