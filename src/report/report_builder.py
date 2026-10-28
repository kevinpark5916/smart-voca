#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-10-21 - SmartVoca - 보고서 요약을 HTML 파일로 저장 (FR-08)
# 파일 위치: src/report/report_builder.py
import html
from datetime import datetime
from pathlib import Path

from report.report_data import ReportSummary


def render_report_html(summary: ReportSummary, generated_at: datetime) -> str:
    """보고서 요약을 독립 실행 가능한 HTML 문자열로 만든다. 외부 파일 없이 스타일을 포함한다."""
    wrong_rows = "\n".join(
        f"<tr><td>{html.escape(item.word)}</td><td>{item.attempts}</td><td>{item.wrong}</td></tr>"
        for item in summary.top_wrong
    ) or '<tr><td colspan="3">오답 기록이 없습니다.</td></tr>'
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>SmartVoca 학습 보고서</title>
<style>
body {{ font-family: "Malgun Gothic", sans-serif; margin: 32px; color: #222; }}
h1 {{ font-size: 22px; }}
table {{ border-collapse: collapse; margin-top: 12px; min-width: 360px; }}
th, td {{ border: 1px solid #ccc; padding: 6px 12px; text-align: left; }}
th {{ background: #f2f2f2; }}
.num {{ font-size: 20px; font-weight: bold; }}
</style>
</head>
<body>
<h1>SmartVoca 학습 보고서</h1>
<p>기간: {summary.start_date.isoformat()} ~ {summary.end_date.isoformat()}</p>
<table>
<tr><th>항목</th><th>값</th></tr>
<tr><td>학습 일수</td><td class="num">{summary.study_days}</td></tr>
<tr><td>암기한 단어 수</td><td class="num">{summary.studied_words}</td></tr>
<tr><td>시험 횟수</td><td class="num">{summary.quiz_sessions}</td></tr>
<tr><td>응답 수</td><td>{summary.answer_count}</td></tr>
<tr><td>정답 수</td><td>{summary.correct_count}</td></tr>
<tr><td>평균 정답률</td><td class="num">{summary.accuracy:.1%}</td></tr>
</table>
<h2>자주 틀린 단어 TOP {len(summary.top_wrong)}</h2>
<table>
<tr><th>단어</th><th>응답 수</th><th>오답 수</th></tr>
{wrong_rows}
</table>
<p style="color:#888; margin-top:24px;">생성 시각: {generated_at.isoformat(timespec="seconds")}</p>
</body>
</html>
"""


def save_report_html(summary: ReportSummary, directory: Path, generated_at: datetime) -> Path:
    """보고서를 directory에 저장하고 경로를 돌려준다. 파일 이름에 생성 시각을 넣어 덮어쓰지 않는다."""
    directory.mkdir(parents=True, exist_ok=True)
    file_name = (
        f"report_{summary.start_date.isoformat()}_{summary.end_date.isoformat()}"
        f"_{generated_at:%H%M%S}.html"
    )
    path = directory / file_name
    path.write_text(render_report_html(summary, generated_at), encoding="utf-8")
    return path
