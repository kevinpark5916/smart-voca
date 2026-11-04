#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 홈 API: 오늘 일차, 전체 진도, 연속 학습일, 최근 정답률 (FR-03, FR-17)
# 파일 위치: src/web/api_home.py
from datetime import date

from flask import Blueprint, jsonify

from study.streak import compute_streak
from web.common import get_context

home_bp = Blueprint("home", __name__, url_prefix="/api")
RECENT_QUIZ_COUNT = 5  # 정답률을 계산할 최근 시험 수 (데스크톱 홈과 같은 값)


@home_bp.get("/home")
def home_overview():
    context = get_context()
    settings = context.settings
    total = context.words.count()
    studied = context.study.total_studied_words()
    unfinished = context.study.find_unfinished_session()
    day_no = unfinished[1] if unfinished else context.study.last_day_no() + 1
    all_done = not unfinished and total > 0 and (day_no - 1) * settings.daily_new_count >= total
    streak = compute_streak(context.study.studied_dates(), date.today())
    answers, correct = context.quiz.recent_accuracy(RECENT_QUIZ_COUNT)
    return jsonify(
        {
            "total": total,
            "studied": studied,
            "dayNo": day_no,
            "inProgress": unfinished is not None,
            "allDone": all_done,
            "streak": streak,
            "dailyNewCount": settings.daily_new_count,
            "dailyReviewCount": settings.daily_review_count,
            "recentAnswers": answers,
            "recentCorrect": correct,
            "recentQuizCount": RECENT_QUIZ_COUNT,
        }
    )
