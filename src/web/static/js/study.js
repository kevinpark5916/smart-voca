// 2026-11-04 - SmartVoca - 암기 화면: 플래시카드 뒤집기, 알았음/다시 기록, 되돌리기 (FR-03, FR-04)
// 파일 위치: src/web/static/js/study.js

// 화면 상태. session은 서버가 준 세션 요약을 그대로 쓴다
const studyState = { root: null, session: null, status: "", revealed: false, showExample: false, busy: false };

window.Views.study = async function renderStudy(root) {
  studyState.root = root;
  root.replaceChildren(el("p", { text: "불러오는 중..." }));
  const data = await api("api/study/session");
  setStudyData(data);
};

function setStudyData(data) {
  studyState.session = data.session;
  studyState.status = data.state;
  studyState.revealed = false;
  studyState.showExample = false;
  drawStudy();
}

// 서버 응답으로 세션을 갱신한다 (답하기·되돌리기 후 공통)
async function studyRequest(path, body) {
  if (studyState.busy || !studyState.session) return;
  studyState.busy = true;
  try {
    const data = await api(path, { method: "POST", body: { sessionId: studyState.session.sessionId, dayNo: studyState.session.dayNo, ...body } });
    studyState.session = data.session;
    studyState.revealed = false;
    studyState.showExample = false;
    drawStudy();
  } catch (error) {
    showError(error);
  } finally {
    studyState.busy = false;
  }
}

async function startNextDay() {
  try {
    setStudyData(await api("api/study/start", { method: "POST" }));
  } catch (error) {
    showError(error);
  }
}

function drawStudy() {
  const root = studyState.root;
  if (!root || window.currentView !== "study") return;
  const session = studyState.session;

  if (!session) {
    const messages = {
      no_words: "단어가 없습니다. '단어 목록' 탭에서 CSV를 불러오세요.",
      all_done: "모든 단어를 외웠습니다!",
      ready: "오늘 암기를 시작할 준비가 되었습니다.",
    };
    const action = studyState.status === "ready" ? el("button", { class: "primary", text: "다음 일차 시작", onclick: startNextDay }) : null;
    root.replaceChildren(el("section", { class: "card center" }, [el("p", { class: "lead", text: messages[studyState.status] || "" }), action]));
    return;
  }

  if (session.isFinished) {
    root.replaceChildren(
      el("section", { class: "card center" }, [
        el("h2", { text: `${session.dayNo}일차 암기 완료` }),
        el("p", { text: "수고하셨습니다!" }),
        el("p", { class: "hint", text: "마지막 답을 되돌리려면 Ctrl+Z를 누르세요." }),
        el("div", { class: "button-row" }, [
          el("button", { class: "primary", text: "다음 일차 시작", onclick: startNextDay }),
          el("button", { text: "마지막 답 되돌리기 (Ctrl+Z)", onclick: undoStudy }),
        ]),
      ])
    );
    return;
  }

  const index = session.cards.findIndex((card) => card.result === null);
  const card = session.cards[index];
  const kindLabel = card.kind === "review" ? "복습" : "신규";
  const counts = countResults(session);
  const word = card.word;

  root.replaceChildren(
    el("section", { class: "card study-card" }, [
      el("p", { class: "hint", text: `${session.dayNo}일차 · ${kindLabel} · ${index + 1} / ${session.total}` }),
      el("h2", { class: "word", text: word.word }),
      studyState.revealed ? el("p", { class: "lead", text: `${word.pos}  ${word.meaning}` }) : null,
      studyState.revealed && studyState.showExample ? el("p", { class: "example", text: word.example }) : null,
      el("div", { class: "button-row" }, studyButtons()),
      el("p", { class: "hint", text: `알았음 ${counts.know} · 다시 ${counts.again} · 남은 카드 ${counts.left}` }),
      el("p", { class: "hint", text: "단축키: Space 뒤집기 · E 예문 · Enter 알았음 · Backspace 다시 · Ctrl+Z 되돌리기" }),
    ])
  );
}

// 뜻을 보기 전에는 '뒤집기'만 보인다. 뒤집은 뒤에야 알았음/다시를 누를 수 있다
function studyButtons() {
  if (!studyState.revealed) {
    return [el("button", { class: "primary", text: "뒤집기 (Space)", onclick: revealCard })];
  }
  return [
    el("button", { text: studyState.showExample ? "예문 숨기기 (E)" : "예문 보기 (E)", onclick: toggleExample }),
    el("button", { class: "again", text: "다시 (Backspace)", onclick: () => studyRequest("api/study/answer", { result: "again" }) }),
    el("button", { class: "know primary", text: "알았음 (Enter)", onclick: () => studyRequest("api/study/answer", { result: "know" }) }),
  ];
}

function countResults(session) {
  const counts = { know: 0, again: 0, left: 0 };
  for (const card of session.cards) {
    if (card.result === null) counts.left += 1;
    else counts[card.result] += 1;
  }
  return counts;
}

function revealCard() {
  studyState.revealed = true;
  drawStudy();
}

function toggleExample() {
  studyState.showExample = !studyState.showExample;
  drawStudy();
}

function undoStudy() {
  studyRequest("api/study/undo", {});
}

// 암기 화면 단축키. 다른 화면이거나 입력 중이면 무시한다
document.addEventListener("keydown", (event) => {
  if (window.currentView !== "study" || !studyState.session || studyState.busy) return;
  if (event.target.matches("input, textarea, select")) return;
  const session = studyState.session;
  const finished = session.isFinished;

  if (event.ctrlKey && event.key.toLowerCase() === "z") {
    event.preventDefault();
    if (session.answeredCount > 0) undoStudy();
    return;
  }
  if (finished) return;
  if (event.key === " " && !studyState.revealed) {
    event.preventDefault();
    revealCard();
  } else if (studyState.revealed && (event.key === "e" || event.key === "E")) {
    toggleExample();
  } else if (studyState.revealed && event.key === "Enter") {
    studyRequest("api/study/answer", { result: "know" });
  } else if (studyState.revealed && event.key === "Backspace") {
    event.preventDefault();
    studyRequest("api/study/answer", { result: "again" });
  }
});
