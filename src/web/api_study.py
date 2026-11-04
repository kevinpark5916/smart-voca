#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 암기 API: 현재 세션 조회, 다음 일차 시작, 알았음/다시 기록, 되돌리기 (FR-03, FR-04)
# 파일 위치: src/web/api_study.py
from flask import Blueprint, jsonify

from storage.study_repository import RESULT_AGAIN, RESULT_KNOW
from web.common import get_context, json_body, require
from web.serializers import study_session_to_dict

study_bp = Blueprint("study", __name__, url_prefix="/api/study")
VALID_RESULTS = (RESULT_KNOW, RESULT_AGAIN)


def _idle_response():
    """진행 중인 세션이 없을 때 이유를 함께 준다: 단어 없음 / 모두 외움 / 다음 일차 시작 가능."""
    context = get_context()
    if context.words.count() == 0:
        return jsonify(session=None, state="no_words")
    day_no = context.study.last_day_no() + 1
    if (day_no - 1) * context.settings.daily_new_count >= context.words.count():
        return jsonify(session=None, state="all_done")
    return jsonify(session=None, state="ready")


@study_bp.get("/session")
def current_session():
    """끝나지 않은 세션이 있으면 돌려준다. 없으면 새 세션을 만들지 않고 상태만 알려 준다."""
    context = get_context()
    unfinished = context.study.find_unfinished_session()
    if unfinished is None:
        return _idle_response()
    session_id, day_no = unfinished
    session = context.study_service.load(session_id, day_no)
    return jsonify(session=study_session_to_dict(session), state="in_progress")


@study_bp.post("/start")
def start_session():
    """이어 할 세션이 있으면 이어 하고, 없으면 다음 일차를 새로 만든다 (데스크톱 '다음 일차 시작')."""
    context = get_context()
    session = context.study_service.start_or_resume(context.now())
    if session is None:
        return _idle_response()
    return jsonify(session=study_session_to_dict(session), state="in_progress")


def _load_session_from_body(context, body: dict):
    session_id = int(require(body, "sessionId"))
    day_no = int(require(body, "dayNo"))
    return context.study_service.load(session_id, day_no)


@study_bp.post("/answer")
def answer_card():
    """다음으로 답할 카드에 알았음/다시를 기록한다. 순서는 서버가 정한다."""
    context = get_context()
    body = json_body()
    result = require(body, "result")
    if result not in VALID_RESULTS:
        raise ValueError("결과는 know 또는 again이어야 합니다")
    session = _load_session_from_body(context, body)
    index = session.next_pending_index()
    if index is None:
        raise ValueError("이미 끝난 세션입니다")
    updated = context.study_service.answer(session, session.cards[index].record_id, result, context.now())
    return jsonify(session=study_session_to_dict(updated), state="in_progress")


@study_bp.post("/undo")
def undo_answer():
    """마지막으로 답한 카드의 응답을 지운다. 끝난 세션이면 다시 연다."""
    context = get_context()
    session = _load_session_from_body(context, json_body())
    updated = context.study_service.undo_last(session)
    return jsonify(session=study_session_to_dict(updated), state="in_progress")
