#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-25 - SmartVoca - 학습 통계 API: 날짜별 정답률 추이, 자주 틀린 단어 TOP N. 모든 값은 DB 이력으로 계산 (VOCA-FR-032~034)
# 파일 위치: src/web/api_stats.py
from flask import Blueprint, jsonify, request

from web.common import get_context, read_date_range

stats_bp = Blueprint("stats", __name__, url_prefix="/api")
TOP_WRONG_LIMIT = 10  # 자주 틀린 단어 목록 개수 (VOCA-FR-033)


@stats_bp.get("/stats")
def learning_stats():
    """기간의 날짜별 정답률, 전체 정답률, 자주 틀린 단어 TOP N을 돌려준다. 기간을 주지 않으면 전체 기간."""
    context = get_context()
    start, end = read_date_range(request.args)
    daily_rows = context.quiz.daily_accuracy(start, end)
    daily = [
        {
            "date": day,
            "answers": answers,
            "correct": correct,
            "accuracy": round(correct / answers, 4) if answers else 0.0,
        }
        for day, answers, correct in daily_rows
    ]
    total_answers = sum(item["answers"] for item in daily)
    total_correct = sum(item["correct"] for item in daily)
    top_rows = context.quiz.top_wrong_between(start, end, TOP_WRONG_LIMIT)
    return jsonify(
        {
            "daily": daily,
            "totalAnswers": total_answers,
            "totalCorrect": total_correct,
            "accuracy": round(total_correct / total_answers, 4) if total_answers else 0.0,
            "topWrong": [
                {"word": word, "attempts": attempts, "wrong": wrong}
                for word, attempts, wrong in top_rows
            ],
        }
    )
