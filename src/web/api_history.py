#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 이력·보고서 API: 시험/암기 이력 목록, 문항별 응답, 기간 보고서 HTML (FR-07, FR-08)
# 파일 위치: src/web/api_history.py
from datetime import date

from flask import Blueprint, jsonify, request, send_file

from paths import REPORT_DIR
from report.report_builder import save_report_html
from report.report_data import build_report_summary
from web.common import get_context, read_date_range
from web.serializers import quiz_answer_to_dict, quiz_session_to_dict, study_summary_to_dict

history_bp = Blueprint("history", __name__, url_prefix="/api")
MAX_LIST_LIMIT = 200


def _limit() -> int:
    """목록 개수. 기본 50, 1~200 사이로 제한한다."""
    try:
        value = int(request.args.get("limit", 50))
    except ValueError as error:
        raise ValueError("limit은 숫자여야 합니다") from error
    return max(1, min(value, MAX_LIST_LIMIT))


@history_bp.get("/history/quiz")
def quiz_history():
    context = get_context()
    start, end = read_date_range(request.args)
    sessions = context.quiz.list_sessions(_limit(), start, end)
    return jsonify([quiz_session_to_dict(session) for session in sessions])


@history_bp.get("/history/quiz/<int:session_id>/answers")
def quiz_answers(session_id: int):
    context = get_context()
    answers = context.quiz.session_answers(session_id)
    return jsonify([quiz_answer_to_dict(answer) for answer in answers])


@history_bp.get("/history/study")
def study_history():
    context = get_context()
    start, end = read_date_range(request.args)
    sessions = context.study.list_sessions(_limit(), start, end)
    return jsonify([study_summary_to_dict(session) for session in sessions])


@history_bp.get("/report")
def download_report():
    """기간 보고서를 만들어 data/reports(배포 시 APPDATA)에 저장하고 파일을 내려 준다 (FR-08)."""
    context = get_context()
    start, end = read_date_range(request.args, required=True)
    now = context.now()
    summary = build_report_summary(
        context.study,
        context.quiz,
        date.fromisoformat(start),
        date.fromisoformat(end),
    )
    path = save_report_html(summary, REPORT_DIR, now)
    return send_file(path, mimetype="text/html", as_attachment=True, download_name=path.name)

