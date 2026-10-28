#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 프로그램 진입점: 앱 구성 후 메인 창 실행
# 파일 위치: src/main.py
import json
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from app_context import AppContext
from paths import CONFIG_PATH
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    try:
        context = AppContext.open()
    except (ValueError, json.JSONDecodeError) as error:
        QMessageBox.critical(None, "설정 파일 오류", f"{CONFIG_PATH}\n\n{error}")
        return 1

    apply_theme(app, context.settings)
    message = context.load_default_words_if_empty()
    window = MainWindow(context)
    window.show()
    if message:
        window.statusBar().showMessage(message, 8000)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
