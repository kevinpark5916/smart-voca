#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 CSV 불러오기·저장 (FR-01, FR-02)
# 파일 위치: src/storage/word_csv.py
import csv
from pathlib import Path

from models.word import Word

REQUIRED_COLUMNS = ["id", "word", "pos", "meaning", "example", "level"]
TEXT_COLUMNS = ["word", "pos", "meaning", "example"]


def load_words_from_csv(path: Path) -> tuple[list[Word], list[str]]:
    """CSV를 읽어 (단어 목록, 오류 메시지 목록)을 돌려준다. 잘못된 행은 건너뛴다 (FR-02)."""
    words: list[Word] = []
    errors: list[str] = []
    seen_words: set[str] = set()
    # utf-8-sig: 엑셀이 붙인 BOM을 자동으로 제거한다
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return [], [f"필수 컬럼 없음: {', '.join(missing)}"]
        for line_no, row in enumerate(reader, start=2):  # 1행은 헤더
            try:
                word = _row_to_word(row)
            except ValueError as error:
                errors.append(f"{line_no}행: {error}")
                continue
            key = word.word.lower()
            if key in seen_words:
                errors.append(f"{line_no}행: 중복 단어 '{word.word}'")
                continue
            seen_words.add(key)
            words.append(word)
    return words, errors


def _row_to_word(row: dict) -> Word:
    """CSV 한 행을 Word로 바꾼다. 값이 비었거나 숫자가 아니면 ValueError."""
    values = {column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS}
    for column in TEXT_COLUMNS:
        if not values[column]:
            raise ValueError(f"'{column}' 값이 비어 있음")
    try:
        word_id = int(values["id"])
        level = int(values["level"])
    except ValueError as error:
        raise ValueError("id 또는 level이 숫자가 아님") from error
    return Word(
        id=word_id,
        word=values["word"],
        pos=values["pos"],
        meaning=values["meaning"],
        example=values["example"],
        level=level,
    )


def save_words_to_csv(path: Path, words: list[Word]) -> None:
    """단어 목록을 UTF-8 BOM CSV로 저장한다 (FR-02 내보내기).

    어느 파일에 쓸지는 호출하는 쪽(UI)이 정한다. 원본 덮어쓰기 방지는 UI에서 확인한다 (NFR-04).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(REQUIRED_COLUMNS)
        for word in words:
            writer.writerow([word.id, word.word, word.pos, word.meaning, word.example, word.level])
