#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - UI 개선 기능 테스트: 홈, 틀린 단어 재시험, 검색, 이력 기간 필터, 테마, 키보드 시험
# 파일 위치: tests/test_ui_upgrade.py
import os
from datetime import date, datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from app_context import AppContext  # noqa: E402
from config.settings import Settings  # noqa: E402
from paths import WORDS_CSV_PATH  # noqa: E402
from quiz.question import DIRECTION_EN_KO, DIRECTION_KO_EN, TYPE_CHOICE, TYPE_SHORT  # noqa: E402
from ui.history_view import HistoryView  # noqa: E402
from ui.home_view import HomeView, compute_streak  # noqa: E402
from ui.quiz_view import PAGE_RESULT, QuizView  # noqa: E402
from ui.theme import SCALE_FACTORS, apply_theme, scaled  # noqa: E402
from ui.word_list_view import WordListView  # noqa: E402

T0 = datetime(2026, 10, 21, 9, 0, 0)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def context(tmp_path):
    app_context = AppContext.open(tmp_path / "up.db", tmp_path / "config.json")
    app_context.import_words_csv(WORDS_CSV_PATH)
    yield app_context
    app_context.close()


def test_streak_counts_back_from_today_or_yesterday():
    today = date(2026, 10, 21)
    assert compute_streak(["2026-10-21", "2026-10-20", "2026-10-19"], today) == 3
    assert compute_streak(["2026-10-20", "2026-10-19"], today) == 2  # 오늘 아직 안 했으면 어제부터
    assert compute_streak(["2026-10-18"], today) == 0
    assert compute_streak([], today) == 0


def test_scale_factor_applies_to_pixel_sizes(qapp):
    apply_theme(qapp, Settings(font_scale="large"))
    assert scaled(20) == round(20 * SCALE_FACTORS["large"])
    apply_theme(qapp, Settings(font_scale="normal"))
    assert scaled(20) == 20


def test_home_view_shows_plan_and_navigates(qapp, context):
    home = HomeView(context)
    assert "1일차" in home._plan.text()
    received = []
    home.navigate.connect(received.append)
    home._make_nav_button("x", 2).click()
    assert received == [2]
    home.close()


def test_word_search_filters_rows(qapp, context):
    view = WordListView(context)
    view.show()
    view._search.setText("river")
    qapp.processEvents()
    visible = view._table.model().rowCount()
    assert 1 <= visible < 50  # 'river'를 포함하는 단어만 남는다
    view._search.setText("")
    qapp.processEvents()
    assert view._table.model().rowCount() == 2000
    view.close()


def test_word_sort_key_sorts_ids_numerically(context):
    from ui.word_table_model import WordTableModel

    model = WordTableModel(context.words.list_all()[:12])
    id_index = model.index(9, 0)  # id 10
    two_index = model.index(1, 0)  # id 2
    assert model.data(id_index, Qt.ItemDataRole.UserRole) > model.data(two_index, Qt.ItemDataRole.UserRole)


def test_history_date_range_excludes_sessions_outside(qapp, context):
    quiz_view = QuizView(context)
    quiz_view._count_spin.setValue(5)
    quiz_view._direction_combo.setCurrentIndex(quiz_view._direction_combo.findData(DIRECTION_EN_KO))
    quiz_view._type_combo.setCurrentIndex(quiz_view._type_combo.findData(TYPE_SHORT))
    quiz_view._start()
    for _ in range(5):
        quiz_view._submit("")
        quiz_view._next()

    history = HistoryView(context)
    assert history._quiz_model.rowCount() == 1  # 기본 기간(최근 30일)에 포함
    assert context.quiz.list_sessions(10, "2000-01-01", "2000-12-31") == []  # 다른 기간은 비어 있다
    history.close()
    quiz_view.close()


def test_retry_run_contains_only_wrong_words(context):
    quiz_view = QuizView(context)
    quiz_view._count_spin.setValue(5)
    quiz_view._direction_combo.setCurrentIndex(quiz_view._direction_combo.findData(DIRECTION_EN_KO))
    quiz_view._type_combo.setCurrentIndex(quiz_view._type_combo.findData(TYPE_SHORT))
    quiz_view._start()
    run = quiz_view._run
    # 첫 문항만 맞히고 나머지는 틀린다
    quiz_view._submit(run.questions[0].accepted[0])
    quiz_view._next()
    for _ in range(4):
        quiz_view._submit("틀림")
        quiz_view._next()
    assert quiz_view._stack.currentIndex() == PAGE_RESULT
    assert quiz_view._retry_button.isEnabled()

    quiz_view._retry_wrong()
    retry_run = quiz_view._run
    assert len(retry_run.questions) == 4
    assert {q.word.id for q in retry_run.questions} == {q.word.id for q in run.questions[1:]}
    quiz_view.close()


def test_retry_disabled_when_everything_correct(context):
    quiz_view = QuizView(context)
    quiz_view._count_spin.setValue(5)
    quiz_view._direction_combo.setCurrentIndex(quiz_view._direction_combo.findData(DIRECTION_KO_EN))
    quiz_view._type_combo.setCurrentIndex(quiz_view._type_combo.findData(TYPE_SHORT))
    quiz_view._start()
    run = quiz_view._run
    for question in run.questions:
        quiz_view._submit(question.accepted[0])
        quiz_view._next()
    assert not quiz_view._retry_button.isEnabled()
    quiz_view.close()


def test_keyboard_answers_choice_question(qapp, context):
    window_quiz = QuizView(context)
    window_quiz.show()
    window_quiz._count_spin.setValue(5)
    window_quiz._direction_combo.setCurrentIndex(window_quiz._direction_combo.findData(DIRECTION_EN_KO))
    window_quiz._type_combo.setCurrentIndex(window_quiz._type_combo.findData(TYPE_CHOICE))
    window_quiz._start()
    window_quiz.setFocus()
    qapp.processEvents()

    QTest.keyClick(window_quiz, Qt.Key.Key_1)  # 첫 번째 보기 선택
    assert window_quiz._run.answers[0] is not None
    QTest.keyClick(window_quiz, Qt.Key.Key_Return)  # 다음 문제로
    assert window_quiz._run.answers[0] is not None
    assert window_quiz._index == 1
    window_quiz.close()


def test_quiz_theme_palette_switches(qapp):
    apply_theme(qapp, Settings(theme="dark"))
    assert qapp.palette().window().color().lightness() < 100
    apply_theme(qapp, Settings(theme="light"))
    assert qapp.palette().window().color().lightness() > 100
