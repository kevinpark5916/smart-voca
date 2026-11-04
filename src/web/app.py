#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 웹 앱 조립: Flask 인스턴스, API 블루프린트, JSON 오류 응답, 화면 페이지
# 파일 위치: src/web/app.py
from flask import Flask, jsonify, render_template
from werkzeug.exceptions import HTTPException

from app_context import AppContext
from web.api_history import history_bp
from web.api_home import home_bp
from web.api_quiz import quiz_bp
from web.api_study import study_bp
from web.api_words import words_bp

def create_app(context: AppContext) -> Flask:
    """AppContext를 받아 웹 앱을 만든다. 테스트에서는 임시 DB의 context를 넘긴다."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.json.ensure_ascii = False  # 한글을 \uXXXX가 아닌 그대로 보낸다
    app.config["SMARTVOCA"] = context
    app.config["QUIZ_RUNS"] = {}

    for blueprint in (home_bp, study_bp, quiz_bp, history_bp, words_bp):
        app.register_blueprint(blueprint)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(ValueError)
    @app.errorhandler(TypeError)
    def handle_bad_input(error):
        """잘못된 요청 값은 400과 메시지로 돌려준다. 화면이 이 메시지를 그대로 보여 준다."""
        return jsonify(error=str(error)), 400

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        """404 등도 HTML이 아니라 JSON으로 보내서 화면 스크립트가 항상 같은 방식으로 읽는다."""
        return jsonify(error=error.description), error.code

    return app
