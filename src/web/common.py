#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 웹 API 공통 도구: 앱 객체 가져오기, 요청 값 검증, 날짜 범위 파싱
# 파일 위치: src/web/common.py
from datetime import date

from flask import current_app, request

from app_context import AppContext

# 기간을 지정하지 않았을 때 쓰는 전체 범위 (데스크톱 이력 탭과 같은 값)
FAR_PAST = "0001-01-01"
FAR_FUTURE = "9999-12-31"


def get_context() -> AppContext:
    """요청을 처리하는 동안 쓰는 AppContext. create_app()에서 한 번 넣어 둔다."""
    return current_app.config["SMARTVOCA"]


def json_body() -> dict:
    """요청 본문을 dict로 읽는다. 본문이 없으면 빈 dict."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def require(data: dict, key: str):
    """필수 키 값을 꺼낸다. 없거나 빈 값이면 ValueError (HTTP 400)."""
    value = data.get(key)
    if value is None or value == "":
        raise ValueError(f"'{key}' 값이 필요합니다")
    return value


def read_date_range(args, required: bool = False) -> tuple[str, str]:
    """start/end 쿼리 값을 'YYYY-MM-DD'로 검증해 (시작, 끝)을 돌려준다.

    값이 없으면 전체 기간을 쓴다. required=True면 두 값 모두 있어야 한다.
    """
    start = args.get("start")
    end = args.get("end")
    if required and not (start and end):
        raise ValueError("시작일과 종료일을 입력해 주세요")
    start = start or FAR_PAST
    end = end or FAR_FUTURE
    # fromisoformat이 형식 오류를 ValueError로 알려 준다
    date.fromisoformat(start)
    date.fromisoformat(end)
    if start > end:
        raise ValueError("시작일이 종료일보다 늦습니다")
    return start, end
