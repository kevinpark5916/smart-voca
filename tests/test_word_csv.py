#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 단어 CSV 불러오기·저장 테스트 (FR-01, FR-02)
# 파일 위치: tests/test_word_csv.py
from pathlib import Path

from conftest import make_word  # noqa: E402
from paths import WORDS_CSV_PATH
from storage.word_csv import load_words_from_csv, save_words_to_csv

HEADER = "id,word,pos,meaning,example,level\n"


def write_csv(path: Path, body: str) -> Path:
    path.write_text(HEADER + body, encoding="utf-8-sig")
    return path


def test_load_valid_rows(tmp_path):
    path = write_csv(tmp_path / "w.csv", '1,apple,n.,"사과","An apple a day.",1\n')
    words, errors = load_words_from_csv(path)
    assert errors == []
    assert words[0].word == "apple"
    assert words[0].meaning == "사과"
    assert words[0].level == 1


def test_bad_rows_are_skipped_with_line_numbers(tmp_path):
    body = (
        '1,apple,n.,"사과","An apple.",1\n'
        ',broken,n.,"뜻","Example.",1\n'  # id 없음
        '3,dog,n.,"","Example.",1\n'  # 뜻 없음
        '4,cat,n.,"고양이","A cat.",x\n'  # level이 숫자가 아님
        '5,APPLE,n.,"사과2","Dup word.",1\n'  # 중복 (대소문자 무시)
    )
    words, errors = load_words_from_csv(write_csv(tmp_path / "w.csv", body))
    assert [word.word for word in words] == ["apple"]
    assert len(errors) == 4
    assert errors[0].startswith("3행")
    assert any("중복" in error for error in errors)


def test_missing_column_returns_single_error(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("id,word,meaning\n1,apple,사과\n", encoding="utf-8")
    words, errors = load_words_from_csv(path)
    assert words == []
    assert "필수 컬럼 없음" in errors[0]


def test_save_then_load_round_trip(tmp_path):
    original = [make_word(1, "apple", "사과, 능금"), make_word(2, "river", "강", level=2)]
    path = tmp_path / "out.csv"
    save_words_to_csv(path, original)
    loaded, errors = load_words_from_csv(path)
    assert errors == []
    assert loaded == original


def test_saved_file_has_bom_for_excel(tmp_path):
    path = tmp_path / "out.csv"
    save_words_to_csv(path, [make_word(1)])
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_project_word_list_is_valid():
    """실제 data/words.csv가 2000개이고 오류가 없어야 한다 (FR-01)."""
    words, errors = load_words_from_csv(WORDS_CSV_PATH)
    assert errors == []
    assert len(words) == 2000
    assert [word.id for word in words] == list(range(1, 2001))
