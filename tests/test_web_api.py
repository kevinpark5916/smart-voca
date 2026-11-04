#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - SmartVoca - 웹 API 테스트: 암기·시험·이력·단어·설정 엔드포인트를 임시 DB로 검증 (FR-02~FR-08, FR-13, NFR-06)
# 파일 위치: tests/test_web_api.py
import io

import pytest

from app_context import AppContext
from web import api_history
from web.app import create_app


@pytest.fixture
def context(tmp_path, sample_words):
    """임시 DB와 설정 파일을 쓰는 AppContext. 단어 30개(id 1~30)를 미리 넣는다."""
    app_context = AppContext.open(db_path=tmp_path / "test.db", settings_path=tmp_path / "config.json")
    app_context.words.upsert_many(sample_words)
    yield app_context
    app_context.close()


@pytest.fixture
def client(context, tmp_path, monkeypatch):
    # 보고서는 실제 data/reports 대신 임시 폴더에 쓴다
    monkeypatch.setattr(api_history, "REPORT_DIR", tmp_path / "reports")
    app = create_app(context)
    app.config["TESTING"] = True
    return app.test_client()


def test_home_reports_total_and_first_day(client):
    body = client.get("/api/home").get_json()
    assert body["total"] == 30
    assert body["studied"] == 0
    assert body["dayNo"] == 1
    assert body["inProgress"] is False


def test_study_start_creates_new_day_and_answers_in_order(client):
    started = client.post("/api/study/start").get_json()
    session = started["session"]
    assert started["state"] == "in_progress"
    assert session["dayNo"] == 1
    assert session["total"] == 20  # 기본 하루 신규 단어 수 (FR-04)

    session_id, day_no = session["sessionId"], session["dayNo"]
    result = None
    for _ in range(20):
        result = client.post(
            "/api/study/answer",
            json={"sessionId": session_id, "dayNo": day_no, "result": "know"},
        ).get_json()["session"]
    assert result["isFinished"] is True

    # 모두 외운 뒤 다음 일차를 시작하면 2일차는 10개 (FR-04)
    next_day = client.post("/api/study/start").get_json()["session"]
    assert next_day["dayNo"] == 2
    assert next_day["total"] == 10


def test_study_undo_reopens_last_answer(client):
    session = client.post("/api/study/start").get_json()["session"]
    base = {"sessionId": session["sessionId"], "dayNo": session["dayNo"]}
    client.post("/api/study/answer", json={**base, "result": "again"})

    undone = client.post("/api/study/undo", json=base).get_json()["session"]
    assert undone["answeredCount"] == 0


def test_study_answer_rejects_invalid_result(client):
    session = client.post("/api/study/start").get_json()["session"]
    response = client.post(
        "/api/study/answer",
        json={"sessionId": session["sessionId"], "dayNo": session["dayNo"], "result": "maybe"},
    )
    assert response.status_code == 400


def test_quiz_questions_hide_expected_answers_until_submitted(client):
    run = client.post("/api/quiz/runs", json={"count": 5, "direction": "en_ko", "questionType": "short"})
    assert run.status_code == 201
    body = run.get_json()
    assert body["total"] == 5
    assert all("expected" not in question for question in body["questions"])
    assert all("accepted" not in question for question in body["questions"])


def test_quiz_full_run_summarises_wrong_answers_and_retries_them(client):
    run_id = client.post(
        "/api/quiz/runs", json={"count": 5, "direction": "en_ko", "questionType": "short"}
    ).get_json()["runId"]

    last = None
    for index in range(5):
        # 첫 문항만 틀리게 답한다. 정답을 모르니 채점 결과로 판단한다
        answer = "definitely-wrong-answer" if index == 0 else "wrong"
        last = client.post(f"/api/quiz/runs/{run_id}/answers", json={"index": index, "answer": answer}).get_json()

    assert last["isFinished"] is True
    summary = last["summary"]
    assert summary["total"] == 5
    assert len(summary["wrong"]) >= 1

    retry = client.post(
        f"/api/quiz/runs/{run_id}/retry", json={"direction": "en_ko", "questionType": "short"}
    )
    assert retry.status_code == 201
    assert retry.get_json()["total"] == len(summary["wrong"])


def test_quiz_rejects_out_of_range_count_and_bad_options(client):
    too_few = client.post("/api/quiz/runs", json={"count": 2, "direction": "en_ko", "questionType": "short"})
    bad_direction = client.post("/api/quiz/runs", json={"count": 5, "direction": "up", "questionType": "short"})
    assert too_few.status_code == 400
    assert bad_direction.status_code == 400


def test_quiz_unknown_run_returns_json_404(client):
    response = client.post("/api/quiz/runs/999999/answers", json={"index": 0, "answer": "x"})
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_quiz_history_lists_finished_sessions(client):
    run_id = client.post(
        "/api/quiz/runs", json={"count": 5, "direction": "en_ko", "questionType": "short"}
    ).get_json()["runId"]
    for index in range(5):
        client.post(f"/api/quiz/runs/{run_id}/answers", json={"index": index, "answer": "x"})

    sessions = client.get("/api/history/quiz").get_json()
    assert sessions[0]["sessionId"] == run_id
    assert sessions[0]["answers"] == 5
    answers = client.get(f"/api/history/quiz/{run_id}/answers").get_json()
    assert len(answers) == 5


def test_word_search_matches_word_and_meaning(client):
    by_word = client.get("/api/words?q=word7").get_json()
    by_meaning = client.get("/api/words?q=뜻12").get_json()
    assert {item["id"] for item in by_word["items"]} == {7}
    assert {item["id"] for item in by_meaning["items"]} == {12}
    assert by_word["total"] == 30


def test_words_import_reports_errors_and_saves_valid_rows(client):
    csv_text = (
        "id,word,pos,meaning,example,level\n"
        "101,apple,n.,사과,An apple a day.,1\n"
        "102,,n.,빈 단어,,1\n"
    )
    data = {"file": (io.BytesIO(csv_text.encode("utf-8")), "upload.csv")}
    body = client.post("/api/words/import", data=data, content_type="multipart/form-data").get_json()
    assert body["count"] == 1
    assert len(body["errors"]) == 1
    assert client.get("/api/words?q=apple").get_json()["total"] == 31


def test_words_export_returns_csv_with_header(client):
    response = client.get("/api/words/export")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert response.data.decode("utf-8-sig").splitlines()[0] == "id,word,pos,meaning,example,level"


def test_settings_save_and_validation(client):
    saved = client.put("/api/settings", json={"daily_new_count": 15}).get_json()
    assert saved["daily_new_count"] == 15
    assert client.get("/api/settings").get_json()["daily_new_count"] == 15

    invalid = client.put("/api/settings", json={"daily_new_count": 0})
    assert invalid.status_code == 400
    assert "1~200" in invalid.get_json()["error"]


def test_report_download_writes_html_file(client, tmp_path):
    response = client.get("/api/report?start=2026-01-01&end=2026-12-31")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"SmartVoca" in response.data
    assert list((tmp_path / "reports").glob("report_*.html"))


def test_report_requires_dates_and_ordered_range(client):
    assert client.get("/api/report").status_code == 400
    assert client.get("/api/report?start=2026-12-31&end=2026-01-01").status_code == 400


def test_index_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "스마트 보카".encode("utf-8") in response.data
