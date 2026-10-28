#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 저장소·서비스 통합 테스트: 암기 흐름, 시험 흐름, 보고서 (FR-03~FR-08)
# 파일 위치: tests/test_services_storage.py
import random
from datetime import date, datetime, timedelta

import pytest

from config.settings import Settings, load_settings, save_settings
from report.report_builder import render_report_html, save_report_html
from report.report_data import build_report_summary
from services.quiz_service import QuizService
from services.study_service import StudyService
from storage.database import Database
from storage.quiz_repository import QuizRepository
from storage.study_repository import RESULT_AGAIN, RESULT_KNOW, StudyRepository
from storage.word_repository import WordRepository
from study.study_plan import KIND_REVIEW
from quiz.question import DIRECTION_EN_KO, TYPE_CHOICE, TYPE_SHORT
from conftest import make_word  # noqa: E402

T0 = datetime(2026, 10, 21, 9, 0, 0)


@pytest.fixture
def stack(tmp_path, sample_words):
    """DB, 저장소, 서비스를 임시 DB로 한 번에 만든다. 단어는 30개, 하루 5개."""
    database = Database(tmp_path / "test.db")
    settings = Settings(daily_new_count=5, daily_review_count=2, quiz_question_count=5)
    words = WordRepository(database)
    study = StudyRepository(database)
    quiz = QuizRepository(database)
    words.upsert_many(sample_words)
    study_service = StudyService(words, study, lambda: settings)
    quiz_service = QuizService(words, quiz, lambda: settings, random.Random(0))
    yield {
        "db": database, "words": words, "study": study, "quiz": quiz,
        "settings": settings, "study_service": study_service, "quiz_service": quiz_service,
    }
    database.close()


def finish_day(study_service, session, results, now):
    """세션의 모든 카드를 주어진 결과 순서대로 답한다. results는 카드 수와 같은 길이."""
    for card, result in zip(session.cards, results):
        session = study_service.answer(session, card.record_id, result, now)
    return session


def test_day_one_then_day_two_with_review(stack):
    study_service = stack["study_service"]
    day1 = study_service.start_or_resume(T0)
    assert day1.day_no == 1
    assert [card.word.id for card in day1.cards] == [1, 2, 3, 4, 5]

    # 2번, 4번은 '다시'로 표시
    results = [RESULT_KNOW, RESULT_AGAIN, RESULT_KNOW, RESULT_AGAIN, RESULT_KNOW]
    day1 = finish_day(study_service, day1, results, T0)
    assert day1.is_finished

    day2 = study_service.start_or_resume(T0 + timedelta(days=1))
    assert day2.day_no == 2
    review_cards = [card for card in day2.cards if card.kind == KIND_REVIEW]
    assert [card.word.id for card in review_cards] == [2, 4]
    assert [card.word.id for card in day2.cards if card.kind != KIND_REVIEW] == [6, 7, 8, 9, 10]


def test_unfinished_session_resumes_instead_of_starting_new_day(stack):
    study_service = stack["study_service"]
    first = study_service.start_or_resume(T0)
    study_service.answer(first, first.cards[0].record_id, RESULT_KNOW, T0)
    resumed = study_service.start_or_resume(T0 + timedelta(hours=1))
    assert resumed.session_id == first.session_id
    assert resumed.day_no == 1
    assert resumed.answered_count == 1


def test_undo_reopens_finished_session_and_clears_last_answer(stack):
    study_service = stack["study_service"]
    session = study_service.start_or_resume(T0)
    session = finish_day(study_service, session, [RESULT_KNOW] * 5, T0)
    assert session.is_finished

    undone = study_service.undo_last(session)
    assert undone.answered_count == 4
    assert undone.next_pending_index() == 4  # 마지막 카드가 다시 대기 상태가 된다
    assert stack["study"].find_unfinished_session() == (session.session_id, 1)


def test_undo_on_fresh_session_does_nothing(stack):
    study_service = stack["study_service"]
    session = study_service.start_or_resume(T0)
    assert study_service.undo_last(session).answered_count == 0


def test_next_day_starts_only_after_finish_is_confirmed(stack):
    study_service = stack["study_service"]
    session = study_service.start_or_resume(T0)
    session = finish_day(study_service, session, [RESULT_KNOW] * 5, T0)
    # 끝난 세션이 있으면 start_or_resume은 다음 일차를 만든다
    assert study_service.start_or_resume(T0).day_no == 2


def test_no_session_after_all_words_are_studied(stack):
    study_service = stack["study_service"]
    now = T0
    for _ in range(6):  # 6일 x 5개 = 30개 단어
        session = study_service.start_or_resume(now)
        assert session is not None
        finish_day(study_service, session, [RESULT_KNOW] * len(session.cards), now)
        now += timedelta(days=1)
    assert study_service.start_or_resume(now) is None


def test_quiz_run_is_weighted_graded_and_stored(stack):
    quiz_service = stack["quiz_service"]
    run = quiz_service.create_run(5, DIRECTION_EN_KO, TYPE_SHORT, T0)
    assert len(run.questions) == 5
    assert len({question.word.id for question in run.questions}) == 5

    first = run.questions[0]
    assert quiz_service.submit(run, 0, first.word.meaning_candidates()[0], T0) is True
    assert quiz_service.submit(run, 1, "틀린답", T0) is False
    with pytest.raises(ValueError):
        quiz_service.submit(run, 0, "다시", T0)

    quiz_service.finish(run, T0)
    stats = stack["quiz"].get_word_stats()
    assert stats[first.word.id].attempts == 1
    assert stats[first.word.id].wrong == 0
    assert stats[run.questions[1].word.id].wrong == 1


def test_choice_quiz_needs_at_least_four_words(tmp_path):
    database = Database(tmp_path / "few.db")
    words = WordRepository(database)
    words.upsert_many([make_word(1), make_word(2)])
    service = QuizService(words, QuizRepository(database), lambda: Settings(), random.Random(0))
    with pytest.raises(ValueError):
        service.create_run(5, DIRECTION_EN_KO, TYPE_CHOICE, T0)
    database.close()


def test_weights_push_wrong_words_into_next_quiz(stack):
    quiz_service = stack["quiz_service"]
    quiz_repo = stack["quiz"]
    session_id = quiz_repo.create_session(DIRECTION_EN_KO, TYPE_SHORT, 30, T0)
    # 1~5번 단어는 모두 틀린 이력을 만든다. 시험을 여러 번 해도 자주 나와야 한다.
    for word_id in range(1, 6):
        quiz_repo.record_answer(session_id, word_id, DIRECTION_EN_KO, TYPE_SHORT, "p", "e", "x", False, T0)
    # 다른 단어는 모두 맞힌 이력을 준다 (가중치 1)
    for word_id in range(6, 31):
        quiz_repo.record_answer(session_id, word_id, DIRECTION_EN_KO, TYPE_SHORT, "p", "e", "e", True, T0)
    counts = {word_id: 0 for word_id in range(1, 31)}
    for _ in range(40):
        run = quiz_service.create_run(5, DIRECTION_EN_KO, TYPE_SHORT, T0)
        for question in run.questions:
            counts[question.word.id] += 1
    wrong_total = sum(counts[word_id] for word_id in range(1, 6))
    right_total = sum(counts[word_id] for word_id in range(6, 31))
    assert wrong_total > right_total / 3  # 5개 단어가 25개 단어보다 훨씬 자주 뽑혀야 한다


def test_report_summary_counts_study_and_quiz(stack):
    study_service = stack["study_service"]
    quiz_service = stack["quiz_service"]
    session = study_service.start_or_resume(T0)
    finish_day(study_service, session, [RESULT_KNOW, RESULT_AGAIN, RESULT_KNOW, RESULT_KNOW, RESULT_KNOW], T0)

    run = quiz_service.create_run(5, DIRECTION_EN_KO, TYPE_SHORT, T0)
    for index, question in enumerate(run.questions):
        answer = question.word.meaning_candidates()[0] if index < 3 else "틀림"
        quiz_service.submit(run, index, answer, T0)
    quiz_service.finish(run, T0)

    summary = build_report_summary(stack["study"], stack["quiz"], date(2026, 10, 1), date(2026, 10, 31))
    assert summary.study_days == 1
    assert summary.studied_words == 5
    assert summary.quiz_sessions == 1
    assert summary.answer_count == 5
    assert summary.correct_count == 3
    assert summary.accuracy == pytest.approx(0.6)
    assert len(summary.top_wrong) == 2
    assert summary.top_wrong[0].wrong == 1


def test_report_html_is_written_and_escapes_text(stack, tmp_path):
    session_id = stack["quiz"].create_session(DIRECTION_EN_KO, TYPE_SHORT, 1, T0)
    stack["quiz"].record_answer(session_id, 1, DIRECTION_EN_KO, TYPE_SHORT, "p", "e", "x", False, T0)
    summary = build_report_summary(stack["study"], stack["quiz"], date(2026, 10, 1), date(2026, 10, 31))
    html_text = render_report_html(summary, T0)
    assert "SmartVoca 학습 보고서" in html_text
    path = save_report_html(summary, tmp_path / "reports", T0)
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_history_queries_return_sessions_and_answers(stack):
    study_service = stack["study_service"]
    quiz_service = stack["quiz_service"]
    session = study_service.start_or_resume(T0)
    finish_day(study_service, session, [RESULT_KNOW, RESULT_AGAIN, RESULT_KNOW, RESULT_KNOW, RESULT_KNOW], T0)
    study_sessions = stack["study"].list_sessions(10)
    assert len(study_sessions) == 1
    assert study_sessions[0].finished is True
    assert (study_sessions[0].know_count, study_sessions[0].again_count) == (4, 1)

    run = quiz_service.create_run(5, DIRECTION_EN_KO, TYPE_SHORT, T0)
    quiz_service.submit(run, 0, run.questions[0].word.meaning_candidates()[0], T0)
    for index in range(1, 5):
        quiz_service.submit(run, index, "틀림", T0)
    quiz_service.finish(run, T0)

    summaries = stack["quiz"].list_sessions(10)
    assert len(summaries) == 1
    assert (summaries[0].total, summaries[0].answers, summaries[0].correct) == (5, 5, 1)
    details = stack["quiz"].session_answers(run.session_id)
    assert len(details) == 5
    assert details[0].is_correct is True
    assert details[1].user_answer == "틀림"
    assert details[1].word == run.questions[1].word.word


def test_settings_round_trip_and_validation(tmp_path):
    path = tmp_path / "config.json"
    assert load_settings(path) == Settings()  # 파일이 없으면 기본값
    save_settings(path, Settings(daily_new_count=30))
    assert load_settings(path).daily_new_count == 30
    with pytest.raises(ValueError):
        save_settings(path, Settings(quiz_question_count=2))
    assert load_settings(path).daily_new_count == 30  # 잘못된 값은 저장되지 않는다
