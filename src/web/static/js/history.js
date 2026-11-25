// 2026-11-04 - SmartVoca - 이력 화면: 시험·암기 이력 조회, 문항별 응답, 기간 보고서 다운로드 (FR-07, FR-08)
// 파일 위치: src/web/static/js/history.js

const DIRECTION_NAME = { ko_en: "한→영", en_ko: "영→한", mixed: "혼합" };
const QUESTION_TYPE_NAME = { short: "단답형", choice: "4지선다", ox: "OX", mixed: "혼합" };

window.Views.history = function renderHistory(root) {
  const startInput = el("input", { type: "date", id: "history-start" });
  const endInput = el("input", { type: "date", id: "history-end" });
  const quizPane = el("div", { class: "history-pane" });
  const studyPane = el("div", { class: "history-pane", hidden: true });
  const reportPane = el("div", { class: "history-pane", hidden: true });

  const panes = { quiz: quizPane, study: studyPane, report: reportPane };
  const tabButtons = [
    ["quiz", "시험 이력"],
    ["study", "암기 이력"],
    ["report", "보고서"],
  ].map(([key, label]) =>
    el("button", {
      text: label,
      "data-pane": key,
      onclick: () => showPane(key, panes, root),
    })
  );

  root.replaceChildren(
    el("section", { class: "card" }, [
      el("div", { class: "button-row" }, tabButtons),
      el("div", { class: "button-row" }, [
        el("label", { class: "form-row inline" }, [el("span", { text: "기간" }), startInput]),
        el("span", { text: "~" }),
        endInput,
        el("button", { text: "기간 조회", onclick: () => loadHistory(startInput, endInput, panes) }),
        el("button", { text: "전체 보기", onclick: () => { startInput.value = ""; endInput.value = ""; loadHistory(startInput, endInput, panes); } }),
      ]),
      quizPane,
      studyPane,
      reportPane,
    ])
  );
  drawReportPane(reportPane, startInput, endInput);
  showPane("quiz", panes, root);
  loadHistory(startInput, endInput, panes);
};

function showPane(key, panes) {
  for (const [name, pane] of Object.entries(panes)) {
    pane.hidden = name !== key;
  }
  document.querySelectorAll("[data-pane]").forEach((button) => {
    button.classList.toggle("primary", button.dataset.pane === key);
  });
}

async function loadHistory(startInput, endInput, panes) {
  const query = new URLSearchParams();
  if (startInput.value) query.set("start", startInput.value);
  if (endInput.value) query.set("end", endInput.value);
  const suffix = query.toString() ? `?${query}` : "";
  try {
    const [quizSessions, studySessions] = await Promise.all([
      api(`api/history/quiz${suffix}`),
      api(`api/history/study${suffix}`),
    ]);
    drawQuizHistory(panes.quiz, quizSessions);
    drawStudyHistory(panes.study, studySessions);
  } catch (error) {
    showError(error);
  }
}

function drawQuizHistory(pane, sessions) {
  const rows = sessions.map((session) => {
    const rate = session.answers ? `${Math.round((session.correct / session.answers) * 100)}%` : "-";
    return el("tr", { class: "clickable", onclick: () => showQuizAnswers(pane, session) }, [
      el("td", { text: session.startedAt.slice(0, 16).replace("T", " ") }),
      el("td", { text: DIRECTION_NAME[session.direction] || session.direction }),
      el("td", { text: QUESTION_TYPE_NAME[session.questionType] || session.questionType }),
      el("td", { text: session.total }),
      el("td", { text: session.correct }),
      el("td", { text: rate }),
    ]);
  });
  const detail = el("div", { class: "answer-detail" }, [el("p", { class: "hint", text: "시험을 고르면 문항별 응답이 보입니다." })]);
  pane.replaceChildren(
    sessions.length ? table(["시작 시각", "방향", "유형", "문제 수", "정답", "정답률"], rows) : el("p", { text: "시험 기록이 없습니다." }),
    detail
  );
}

async function showQuizAnswers(pane, session) {
  const detail = pane.querySelector(".answer-detail");
  try {
    const answers = await api(`api/history/quiz/${session.sessionId}/answers`);
    const correct = answers.filter((answer) => answer.isCorrect).length;
    const rows = answers.map((answer) =>
      el("tr", {}, [
        el("td", { text: answer.answeredAt.slice(11, 16) }),
        el("td", { text: answer.word }),
        el("td", { text: answer.prompt }),
        el("td", { text: answer.expected }),
        el("td", { text: answer.userAnswer || "(빈 답)" }),
        el("td", { text: answer.isCorrect ? "정답" : "오답" }),
      ])
    );
    detail.replaceChildren(
      el("p", { class: "hint", text: `선택한 시험: ${correct} / ${answers.length} 정답` }),
      table(["시각", "단어", "문제", "정답", "내 답", "결과"], rows)
    );
  } catch (error) {
    showError(error);
  }
}

function drawStudyHistory(pane, sessions) {
  const rows = sessions.map((session) =>
    el("tr", {}, [
      el("td", { text: `${session.dayNo}일차` }),
      el("td", { text: session.startedAt.slice(0, 16).replace("T", " ") }),
      el("td", { text: session.finished ? "완료" : "진행 중" }),
      el("td", { text: session.total }),
      el("td", { text: session.know }),
      el("td", { text: session.again }),
    ])
  );
  pane.replaceChildren(
    sessions.length ? table(["일차", "시작 시각", "상태", "카드 수", "알았음", "다시 보기"], rows) : el("p", { text: "암기 기록이 없습니다." })
  );
}

// 보고서는 기간을 골라 서버에서 HTML 파일로 받는다. 기간 입력은 이력 탭의 값을 함께 쓴다
function drawReportPane(pane, startInput, endInput) {
  const reportStart = el("input", { type: "date", id: "report-start" });
  const reportEnd = el("input", { type: "date", id: "report-end" });
  pane.replaceChildren(
    el("p", { class: "hint", text: "기간의 학습 일수, 암기 단어 수, 시험 횟수, 정답률, 자주 틀린 단어 TOP 10을 HTML 파일로 저장합니다." }),
    el("div", { class: "button-row" }, [
      el("label", { class: "form-row inline" }, [el("span", { text: "시작일" }), reportStart]),
      el("label", { class: "form-row inline" }, [el("span", { text: "종료일" }), reportEnd]),
      el("button", {
        class: "primary",
        text: "보고서 만들기",
        onclick: () => downloadReport(reportStart, reportEnd),
      }),
    ])
  );
  // 이력 기간을 골랐으면 보고서 기간에도 미리 채운다
  reportStart.value = startInput.value;
  reportEnd.value = endInput.value;
}

function downloadReport(startInput, endInput) {
  if (!startInput.value || !endInput.value) {
    showToast("시작일과 종료일을 입력해 주세요.", true);
    return;
  }
  const query = new URLSearchParams({ start: startInput.value, end: endInput.value });
  // 서버가 Content-Disposition: attachment로 보내므로 링크를 누르면 바로 저장된다
  const link = el("a", { href: `api/report?${query}` });
  document.body.append(link);
  link.click();
  link.remove();
  showToast("보고서를 만들었습니다. 다운로드가 시작됩니다.");
}

function table(headers, rows) {
  return el("table", {}, [
    el("thead", {}, el("tr", {}, headers.map((text) => el("th", { text })))),
    el("tbody", {}, rows),
  ]);
}
