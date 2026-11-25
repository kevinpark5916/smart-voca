#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 단어·설정 API: 단어 검색, CSV 불러오기·내보내기, 설정 조회·저장 (FR-01, FR-02, FR-13)
# 파일 위치: src/web/api_words.py
import tempfile
from dataclasses import fields
from pathlib import Path

from flask import Blueprint, Response, jsonify, request

from config.settings import Settings
from web.common import get_context, json_body
from web.serializers import settings_to_dict, word_to_dict

words_bp = Blueprint("words", __name__, url_prefix="/api")


@words_bp.get("/words")
def list_words():
    """단어 전체 목록. q가 있으면 단어·품사·뜻·예문에서 대소문자 무시 검색한다."""
    context = get_context()
    keyword = request.args.get("q", "").strip().lower()
    words = context.words.list_all()
    if keyword:
        words = [
            word
            for word in words
            if any(keyword in text.lower() for text in (word.word, word.pos, word.meaning, word.example))
        ]
    return jsonify({"total": context.words.count(), "items": [word_to_dict(word) for word in words]})


@words_bp.post("/words")
def add_word():
    """단어를 한 개 추가한다 (VOCA-FR-001). 필수 값은 영단어와 뜻이다."""
    context = get_context()
    word = context.word_service.add(json_body())
    return jsonify(word_to_dict(word)), 201


@words_bp.put("/words/<int:word_id>")
def update_word(word_id: int):
    """단어 내용을 고친다 (VOCA-FR-002)."""
    context = get_context()
    word = context.word_service.update(word_id, json_body())
    return jsonify(word_to_dict(word))


@words_bp.delete("/words/<int:word_id>")
def delete_word(word_id: int):
    """단어를 지운다. 학습·시험 기록이 있으면 400으로 막는다 (VOCA-FR-002)."""
    context = get_context()
    context.word_service.delete(word_id)
    return jsonify(ok=True)


@words_bp.post("/words/import")
def import_words():
    """업로드한 CSV를 DB에 반영한다. 잘못된 행은 건너뛰고 사유 목록을 돌려준다 (FR-02)."""
    context = get_context()
    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename == "":
        raise ValueError("CSV 파일을 선택해 주세요")
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "upload.csv"
        uploaded.save(path)
        count, errors = context.import_words_csv(path)
    return jsonify({"count": count, "errors": errors})


@words_bp.get("/words/export")
def export_words():
    """현재 단어를 CSV 파일로 내려 준다. 원본 data/words.csv는 건드리지 않는다 (NFR-04)."""
    context = get_context()
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "words_export.csv"
        context.export_words_csv(path)
        data = path.read_bytes()
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="words_export.csv"'},
    )


@words_bp.get("/settings")
def get_settings():
    return jsonify(settings_to_dict(get_context().settings))


@words_bp.put("/settings")
def update_settings():
    """받은 값만 덮어써 저장한다. 범위 검사는 Settings.validate()가 한다 (FR-13)."""
    context = get_context()
    body = json_body()
    merged = settings_to_dict(context.settings)
    known_names = {field.name for field in fields(Settings)}
    for key, value in body.items():
        if key in known_names:
            merged[key] = value
    new_settings = Settings(**merged)
    new_settings.validate()
    context.update_settings(new_settings)
    return jsonify(settings_to_dict(new_settings))
