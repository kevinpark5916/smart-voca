#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-25 - SmartVoca - 운영 서버(gunicorn) 진입점: 컨테이너에서 웹 앱을 조립해 app 객체를 넘긴다 (DR-18)
# 파일 위치: src/wsgi.py
# 실행 예: cd /app/src && gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 1 wsgi:app
from app_context import AppContext
from web.app import create_app

# gunicorn이 이 파일을 불러올 때 한 번 조립한다. DB 경로는 환경변수 DB_PATH를 따른다.
_context = AppContext.open()
_context.load_default_words_if_empty()
app = create_app(_context)
