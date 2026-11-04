#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 시험 API: 출제, 문항별 채점, 결과 요약, 틀린 단어 재시험 (FR-05, FR-06, FR-07, FR-12)
# 파일 위치: src/web/api_quiz.py
from flask import Blueprint, abort, current_app, jsonify

from quiz.question import DIRECTION_EN_KO, DIRECTION_KO_EN, DIRECTION_MIXED, TYPE_CHOICE, TYPE_MIXED, TYPE_OX, TYPE_SHORT
from services.quiz_service import QuizRun
from web.common import get_context, json_body, require
from web.serializers import run_summary_to_dict, run_to_dict, word_to_dict

quiz_bp = Blueprint("quiz", __name__, url_prefix="/api/quiz")
VALID_DIRECTIONS = (DIRECTION_KO_EN, DIRECTION_EN_KO, DIRECTION_MIXED)
VALID_TYPES = (TYPE_SHORT, TYPE_CHOICE, TYPE_OX, TYPE_MIXED)
QUESTION_COUNT_RANGE = (5, 100)  # 설정 검증과 같은 범위 (FR-05)


def _check_options(direction: str, question_type: str) -> None:
    if direction not in VALID_DIRECTIONS:
        raise ValueError("방향 값이 올바르지 않습니다")
    if question_type not in VALID_TYPES:
        raise ValueError("유형 값이 올바르지 않습니다")


def _runs() -> dict:
    """진행 중인 시험을 서버 메모리에 둔다. 1인용 로컬 앱이라 DB에는 응답 결과만 저장한다."""
    return current_app.config["QUIZ_RUNS"]


def _get_run(run_id: int) -> QuizRun:
    run = _runs().get(run_id)
    if run is None:
        abort(404, description="시험을 찾을 수 없습니다. 새 시험을 시작해 주세요.")
    return run


@quiz_bp.post("/runs")
def create_run():
    context = get_context()
    body = json_body()
    count = int(require(body, "count"))
    low, high = QUESTION_COUNT_RANGE
    if not low <= count <= high:
        raise ValueError(f"문제 수는 {low}~{high}이어야 합니다")
    direction = require(body, "direction")
    question_type = require(body, "questionType")
    _check_options(direction, question_type)
    run = context.quiz_service.create_run(count, direction, question_type, context.now())
    _runs()[run.session_id] = run
    return jsonify(run_to_dict(run)), 201


@quiz_bp.post("/runs/<int:run_id>/retry")
def retry_wrong(run_id: int):
    """방금 시험에서 틀린 단어만 다시 출제한다."""
    context = get_context()
    body = json_body()
    direction = require(body, "direction")
    question_type = require(body, "questionType")
    _check_options(direction, question_type)
    previous = _get_run(run_id)
    run = context.quiz_service.create_retry_run(previous, direction, question_type, context.now())
    _runs()[run.session_id] = run
    return jsonify(run_to_dict(run)), 201


@quiz_bp.post("/runs/<int:run_id>/answers")
def submit_answer(run_id: int):
    """문항 하나를 채점한다. 마지막 문항이면 시험을 끝내고 결과 요약을 함께 준다."""
    context = get_context()
    run = _get_run(run_id)
    body = json_body()
    index = int(require(body, "index"))
    if not 0 <= index < len(run.questions):
        raise ValueError("문항 번호가 범위를 벗어났습니다")
    user_answer = str(body.get("answer", "")).strip()
    is_correct = context.quiz_service.submit(run, index, user_answer, context.now())
    question = run.questions[index]
    payload = {
        "index": index,
        "correct": is_correct,
        "expected": question.expected,
        "word": word_to_dict(question.word),
        "userAnswer": user_answer,
        "isFinished": run.is_finished,
    }
    if run.is_finished:
        context.quiz_service.finish(run, context.now())
        payload["summary"] = run_summary_to_dict(run)
    return jsonify(payload)
