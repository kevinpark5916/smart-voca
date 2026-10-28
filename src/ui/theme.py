#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 밝은/어두운 테마와 글자 크기 배율 적용 (FR-22)
# 파일 위치: src/ui/theme.py
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from config.settings import Settings

SCALE_FACTORS = {"small": 0.85, "normal": 1.0, "large": 1.25}

# 화면마다 스타일 시트에 px 값을 직접 쓰므로, 배율을 곱해 글자 크기를 맞춘다
_scale = 1.0
_base_point_size: float | None = None


def scaled(px: int) -> int:
    """기본 글자 크기(px)에 현재 배율을 곱한다. 스타일 시트 값을 만들 때 쓴다."""
    return round(px * _scale)


def apply_theme(app: QApplication, settings: Settings) -> None:
    """테마와 글자 크기를 앱 전체에 적용한다.

    글자 크기는 이미 만들어진 화면의 px 값을 바꾸지 못하므로, 완전히 적용하려면 재시작이 필요하다.
    """
    global _scale, _base_point_size
    if _base_point_size is None:
        point_size = app.font().pointSizeF()
        _base_point_size = point_size if point_size > 0 else 10.0
    _scale = SCALE_FACTORS[settings.font_scale]

    font = app.font()
    font.setPointSizeF(_base_point_size * _scale)
    app.setFont(font)

    app.setStyle("Fusion")  # 어두운 팔레트가 모든 위젯에 일관되게 보이도록 Fusion 스타일을 쓴다
    if settings.theme == "dark":
        app.setPalette(_dark_palette())
    else:
        app.setPalette(app.style().standardPalette())


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(32, 33, 36))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(230, 230, 230))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 26, 28))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 41, 45))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(40, 41, 45))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(230, 230, 230))
    palette.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
    palette.setColor(QPalette.ColorRole.Button, QColor(50, 52, 56))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(230, 230, 230))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 80, 80))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(66, 133, 244))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(150, 150, 150))
    return palette
