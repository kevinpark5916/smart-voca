#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 CSV 불러오기·저장. 전체 형식(id 포함)과 간단 형식(영단어,뜻) 지원 (FR-01, FR-02, VOCA-FR-003)
# 파일 위치: src/storage/word_csv.py
import csv
from pathlib import Path

from models.word import Word

REQUIRED_COLUMNS = ["id", "word", "pos", "meaning", "example", "level"]
TEXT_COLUMNS = ["word", "pos", "meaning", "example"]
# 간단 형식: id 열 없이 영단어와 뜻만 있는 파일 (과제 제공 CSV). 열 이름은 영문과 한글 둘 다 받는다
SIMPLE_WORD_NAMES = ("word", "영단어")
SIMPLE_MEANING_NAMES = ("meaning", "뜻")
SIMPLE_ID_PLACEHOLDER = 0  # 간단 형식의 id는 가져올 때 DB에서 정한다


def load_words_from_csv(path: Path) -> tuple[list[Word], list[str]]:
    """CSV를 읽어 (단어 목록, 오류 메시지 목록)을 돌려준다. 잘못된 행은 건너뛴다 (FR-02).

    간단 형식이면 id가 0인 단어를 돌려주고, id는 AppContext가 DB에서 정한다.
    """
    words: list[Word] = []
    errors: list[str] = []
    seen_words: set[str] = set()
    # utf-8-sig: 엑셀이 붙인 BOM을 자동으로 제거한다
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        if "id" not in fieldnames and _simple_columns(fieldnames):
            return _load_simple(reader)
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
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


def _simple_columns(fieldnames: list[str]) -> tuple[str, str] | None:
    """간단 형식의 영단어·뜻 열 이름을 찾는다. 없으면 None."""
    word_name = next((name for name in SIMPLE_WORD_NAMES if name in fieldnames), None)
    meaning_name = next((name for name in SIMPLE_MEANING_NAMES if name in fieldnames), None)
    if word_name and meaning_name:
        return word_name, meaning_name
    return None


def _load_simple(reader: csv.DictReader) -> tuple[list[Word], list[str]]:
    """영단어·뜻 두 열만 있는 행을 읽는다. 같은 파일 안의 중복은 건너뛴다."""
    word_name, meaning_name = _simple_columns(reader.fieldnames or [])
    words: list[Word] = []
    errors: list[str] = []
    seen_words: set[str] = set()
    for line_no, row in enumerate(reader, start=2):
        text = (row.get(word_name) or "").strip()
        meaning = (row.get(meaning_name) or "").strip()
        if not text or not meaning:
            errors.append(f"{line_no}행: 영단어 또는 뜻이 비어 있음")
            continue
        key = text.lower()
        if key in seen_words:
            errors.append(f"{line_no}행: 중복 단어 '{text}'")
            continue
        seen_words.add(key)
        words.append(Word(id=SIMPLE_ID_PLACEHOLDER, word=text, pos="", meaning=meaning, example="", level=1))
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
    """단어 목록을 UTF-8 BOM CSV(전체 형식)로 저장한다 (FR-02 내보내기).

    어느 파일에 쓸지는 호출하는 쪽(UI)이 정한다. 원본 덮어쓰기 방지는 UI에서 확인한다 (NFR-04).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(REQUIRED_COLUMNS)
        for word in words:
            writer.writerow([word.id, word.word, word.pos, word.meaning, word.example, word.level])
