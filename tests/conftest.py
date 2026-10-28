#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - pytest 공통 설정: src 경로 등록과 샘플 단어 fixture
# 파일 위치: tests/conftest.py
import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from models.word import Word  # noqa: E402  (src 경로를 등록한 뒤 import해야 한다)


def make_word(word_id: int, text: str | None = None, meaning: str | None = None, level: int = 1) -> Word:
    """테스트용 단어를 만든다. 뜻은 기본적으로 '뜻<id>'."""
    return Word(
        id=word_id,
        word=text or f"word{word_id}",
        pos="n.",
        meaning=meaning or f"뜻{word_id}",
        example=f"Example sentence {word_id}.",
        level=level,
    )


@pytest.fixture
def sample_words() -> list[Word]:
    """id 1~30 단어 30개. 4지선다와 가중치 테스트에 충분한 양이다."""
    return [make_word(i) for i in range(1, 31)]
