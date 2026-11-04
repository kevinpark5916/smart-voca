#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 웹 버전 진입점: 앱 구성 후 로컬 주소(127.0.0.1)에서 웹 서버 실행
# 파일 위치: src/run_web.py
import json
import sys

from app_context import AppContext
from paths import CONFIG_PATH
from web.app import create_app

HOST = "127.0.0.1"  # 개인 학습 기록 보호: 이 PC 밖에서는 접속하지 않는다 (NFR-07)
PORT = 5000


def main() -> int:
    try:
        context = AppContext.open()
    except (ValueError, json.JSONDecodeError) as error:
        print(f"설정 파일 오류: {CONFIG_PATH}\n{error}")
        return 1

    message = context.load_default_words_if_empty()
    if message:
        print(message)
    app = create_app(context)
    print(f"스마트 보카 웹 실행 중: http://{HOST}:{PORT}  (종료: Ctrl+C)")
    # 요청을 한 번에 하나씩 처리한다. 같은 DB 연결을 여러 스레드가 나눠 쓰지 않도록 하기 위해서다
    app.run(host=HOST, port=PORT, threaded=False, debug=False)
    context.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
