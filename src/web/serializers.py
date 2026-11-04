#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 도메인 객체를 JSON으로 바꾸는 함수 모음 (웹 API 응답 형식)
# 파일 위치: src/web/serializers.py
from dataclasses import asdict

from config.settings import Settings
from models.word import Word
from quiz.question import Question
from services.study_service import StudySession
from services.quiz_service import QuizRun
from storage.quiz_repository import QuizAnswerDetail, QuizSessionSummary
from storage.study_repository import StudySessionSummary


def word_to_dict(word: Word) -> dict:
    return {
        "id": word.id,
        "word": word.word,
        "pos": word.pos,
        "meaning": word.meaning,
        "example": word.example,
        "level": word.level,
    }


def study_session_to_dict(session: StudySession) -> dict:
    """암기 세션 현재 상태. 카드마다 결과(know/again/None)를 담는다."""
    return {
        "sessionId": session.session_id,
        "dayNo": session.day_no,
        "isFinished": session.is_finished,
        "answeredCount": session.answered_count,
        "total": len(session.cards),
        "cards": [
            {
                "recordId": card.record_id,
                "kind": card.kind,
                "result": card.result,
                "word": word_to_dict(card.word),
            }
            for card in session.cards
        ],
    }


def question_to_dict(index: int, question: Question) -> dict:
    """문항을 화면용으로 바꾼다. 정답(expected, accepted)은 답하기 전에는 빼서 보내지 않는다."""
    return {
        "index": index,
        "prompt": question.prompt,
        "type": question.question_type,
        "direction": question.direction,
        "choices": list(question.choices),
        "candidate": question.candidate,
    }


def run_to_dict(run: QuizRun) -> dict:
    return {
        "runId": run.session_id,
        "total": len(run.questions),
        "questions": [question_to_dict(index, question) for index, question in enumerate(run.questions)],
    }


def run_summary_to_dict(run: QuizRun) -> dict:
    """시험이 끝났을 때의 결과. 틀린 문항만 정답과 내 답을 함께 준다."""
    total = len(run.questions)
    wrong = [
        {
            "index": index,
            "word": word_to_dict(question.word),
            "prompt": question.prompt,
            "expected": question.expected,
            "userAnswer": run.user_answers[index] or "",
        }
        for index, (question, answer) in enumerate(zip(run.questions, run.answers))
        if answer is False
    ]
    return {
        "correct": run.correct_count,
        "total": total,
        "accuracy": round(run.correct_count / total * 100, 1) if total else 0,
        "wrong": wrong,
    }


def quiz_session_to_dict(summary: QuizSessionSummary) -> dict:
    return {
        "sessionId": summary.session_id,
        "startedAt": summary.started_at,
        "direction": summary.direction,
        "questionType": summary.question_type,
        "total": summary.total,
        "answers": summary.answers,
        "correct": summary.correct,
    }


def quiz_answer_to_dict(detail: QuizAnswerDetail) -> dict:
    return {
        "answeredAt": detail.answered_at,
        "word": detail.word,
        "prompt": detail.prompt,
        "expected": detail.expected,
        "userAnswer": detail.user_answer,
        "isCorrect": detail.is_correct,
        "questionType": detail.question_type,
    }


def study_summary_to_dict(summary: StudySessionSummary) -> dict:
    return {
        "sessionId": summary.session_id,
        "dayNo": summary.day_no,
        "startedAt": summary.started_at,
        "finished": summary.finished,
        "total": summary.total,
        "know": summary.know_count,
        "again": summary.again_count,
    }


def settings_to_dict(settings: Settings) -> dict:
    return asdict(settings)
