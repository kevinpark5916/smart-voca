#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 한 개를 나타내는 데이터 모델 (FR-01)
# 파일 위치: src/models/word.py
import re
from dataclasses import dataclass

# "시간(60분)"처럼 괄호 안 부가 설명을 떼어내기 위한 패턴
PARENTHESES_PATTERN = re.compile(r"\(.*?\)")


@dataclass(frozen=True)
class Word:
    """영단어 한 개. frozen=True라서 생성 후 값이 바뀌지 않는다."""

    id: int
    word: str
    pos: str
    meaning: str
    example: str
    level: int

    def meaning_candidates(self) -> list[str]:
        """뜻을 쉼표로 나눈 정답 후보 목록. 여러 뜻 중 하나만 맞아도 정답으로 인정한다 (FR-07)."""
        candidates: list[str] = []
        for part in self.meaning.split(","):
            cleaned = part.strip()
            if not cleaned:
                continue
            candidates.append(cleaned)
            # 괄호를 뗀 형태도 정답으로 인정 (예: "만(灣)" -> "만")
            without_paren = PARENTHESES_PATTERN.sub("", cleaned).strip()
            if without_paren and without_paren != cleaned:
                candidates.append(without_paren)
        return candidates
