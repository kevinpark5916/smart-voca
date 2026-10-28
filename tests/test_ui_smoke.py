#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 화면 스모크 테스트: 창 생성, 암기 답하기, 시험 채점 흐름 (화면 없이 실행)
# 파일 위치: tests/test_ui_smoke.py
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # 실제 창을 띄우지 않고 실행한다

import pytest  # noqa: E402
from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from app_context import AppContext  # noqa: E402
from paths import WORDS_CSV_PATH  # noqa: E402
from quiz.question import DIRECTION_EN_KO, DIRECTION_KO_EN, TYPE_CHOICE, TYPE_OX, TYPE_SHORT  # noqa: E402
from storage.study_repository import RESULT_AGAIN, RESULT_KNOW  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.history_view import HistoryView  # noqa: E402
from ui.quiz_view import QuizView  # noqa: E402
from ui.study_view import StudyView  # noqa: E402
from ui.word_list_view import WordListView  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def context(tmp_path):
    """임시 DB와 임시 설정으로 앱 구성요소를 만들고, 실제 words.csv 전체를 불러온다."""
    app_context = AppContext.open(tmp_path / "ui.db", tmp_path / "config.json")
    count, errors = app_context.import_words_csv(WORDS_CSV_PATH)
    assert count == 2000 and errors == []
    yield app_context
    app_context.close()


def test_main_window_builds_with_all_tabs(qapp, context):
    window = MainWindow(context)
    tabs = window.centralWidget()
    assert [tabs.tabText(index) for index in range(tabs.count())] == ["홈", "암기", "시험", "이력", "단어 목록"]
    window.close()


def test_word_list_refresh_is_fast_with_all_words(qapp, context):
    """2000개 단어 새로고침이 화면을 멈추지 않는지 확인한다 (예전 QTableWidget은 수 분 걸렸다)."""
    view = WordListView(context)
    view.show()
    start = time.perf_counter()
    view.refresh()
    qapp.processEvents()
    elapsed = time.perf_counter() - start
    assert view._table.model().rowCount() == 2000
    assert elapsed < 2.0
    view.close()


def test_history_tab_shows_quiz_after_it_finishes(qapp, context):
    quiz_view = QuizView(context)
    quiz_view._count_spin.setValue(5)
    quiz_view._direction_combo.setCurrentIndex(quiz_view._direction_combo.findData(DIRECTION_EN_KO))
    quiz_view._type_combo.setCurrentIndex(quiz_view._type_combo.findData(TYPE_SHORT))
    quiz_view._start()
    for _ in range(5):
        quiz_view._submit("")
        quiz_view._next()

    history = HistoryView(context)
    history.refresh()
    assert history._quiz_model.rowCount() == 1
    assert history._quiz_model.data(history._quiz_model.index(0, 3)) == "5"  # 문제 수 5
    history._quiz_table.selectRow(0)
    qapp.processEvents()
    assert history._answer_model.rowCount() == 5
    assert "0 / 5 정답" in history._detail_label.text()
    history.close()
    quiz_view.close()


def test_study_view_flips_and_records_cards(qapp, context):
    view = StudyView(context)
    session = view._session
    assert session is not None and session.day_no == 1
    assert len(session.cards) == context.settings.daily_new_count

    # 첫 카드: 뒤집기 전에는 답 버튼이 막혀 있어야 한다
    assert not view._know_button.isEnabled()
    view._reveal()
    assert view._know_button.isEnabled()
    view._answer(RESULT_KNOW)
    assert view._session.answered_count == 1
    view.close()


def test_study_view_blocks_answer_before_flip_and_supports_undo(qapp, context):
    view = StudyView(context)
    view._answer(RESULT_KNOW)  # 뒤집기 전이라 무시되어야 한다
    assert view._session.answered_count == 0

    view._reveal()
    view._reveal()  # 두 번 눌러도 상태가 꼬이지 않는다
    view._answer(RESULT_AGAIN)
    assert view._session.answered_count == 1
    assert view._session.cards[0].result == RESULT_AGAIN
    assert view._undo_button.isEnabled()

    view._undo()
    assert view._session.answered_count == 0
    assert not view._revealed
    view.close()


def test_shortcuts_work_from_main_window_key_events(qapp, context):
    """실제 창에 키 입력을 보내서 단축키가 동작하는지 확인한다 (버튼 직접 호출이 아님)."""
    window = MainWindow(context)
    window.show()
    qapp.processEvents()
    study_view = window.centralWidget().widget(1)
    window.centralWidget().setCurrentIndex(1)
    qapp.processEvents()

    QTest.keyClick(window, Qt.Key.Key_Space)
    assert study_view._revealed
    QTest.keyClick(window, Qt.Key.Key_2)
    assert study_view._session.answered_count == 1
    QTest.keyClick(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert study_view._session.answered_count == 0

    # 시험 탭으로 옮기면 암기 단축키는 동작하지 않아야 한다 (입력란의 Space 등을 방해하지 않도록)
    window.centralWidget().setCurrentIndex(2)
    qapp.processEvents()
    QTest.keyClick(window, Qt.Key.Key_Space)
    assert not study_view._revealed
    window.close()


def test_backspace_and_enter_answer_cards(qapp, context):
    window = MainWindow(context)
    window.show()
    qapp.processEvents()
    study_view = window.centralWidget().widget(1)
    window.centralWidget().setCurrentIndex(1)
    qapp.processEvents()

    QTest.keyClick(window, Qt.Key.Key_Space)  # 뒤집기
    QTest.keyClick(window, Qt.Key.Key_Backspace)  # 다시 보기
    assert study_view._session.cards[0].result == RESULT_AGAIN

    QTest.keyClick(window, Qt.Key.Key_Space)
    QTest.keyClick(window, Qt.Key.Key_Return)  # 알았음
    assert study_view._session.cards[1].result == RESULT_KNOW
    window.close()


def test_next_day_button_appears_after_day_is_finished(qapp, context):
    view = StudyView(context)
    total = len(view._session.cards)
    for _ in range(total):
        view._reveal()
        view._answer(RESULT_KNOW)
    assert view._next_day_button.isVisibleTo(view)
    view._next_day_button.click()
    assert view._session.day_no == 2
    assert not view._next_day_button.isVisibleTo(view)
    view.close()


def test_quiz_view_runs_short_answer_quiz(qapp, context):
    view = QuizView(context)
    view._count_spin.setValue(5)
    view._direction_combo.setCurrentIndex(view._direction_combo.findData(DIRECTION_KO_EN))
    view._type_combo.setCurrentIndex(view._type_combo.findData(TYPE_SHORT))
    view._start()
    run = view._run
    assert run is not None and len(run.questions) == 5

    # 첫 문항은 정답을 입력하고, 나머지는 빈 답으로 제출한다
    first = run.questions[0]
    view._answer_edit.setText(first.accepted[0])
    view._submit(view._answer_edit.text())
    assert run.answers[0] is True
    view._next()
    for _ in range(4):
        view._submit("")
        view._next()
    assert view._run is None  # 시험이 끝나면 실행 상태를 비운다
    view.close()


def test_quiz_view_choice_and_ox_modes_render(qapp, context):
    view = QuizView(context)
    view._count_spin.setValue(5)
    view._direction_combo.setCurrentIndex(view._direction_combo.findData(DIRECTION_EN_KO))
    view._type_combo.setCurrentIndex(view._type_combo.findData(TYPE_CHOICE))
    view._start()
    assert sum(button.isVisibleTo(view) for button in view._choice_buttons) == 4
    view._submit_choice(0)
    assert view._run.answers[0] is not None
    assert view._next_button.isVisibleTo(view)

    view._next()
    view._type_combo.setCurrentIndex(view._type_combo.findData(TYPE_OX))
    view._start()
    assert view._ox_buttons["O"].isVisibleTo(view)
    assert not view._choice_buttons[0].isVisibleTo(view)
    view._submit("O")
    assert view._run.answers[0] is not None
    view.close()
