// 2026-11-04 - SmartVoca - 시험 화면: 출제 설정, 문항별 채점, 결과 요약, 틀린 단어 재시험 (FR-05~FR-07, FR-12)
// 파일 위치: src/web/static/js/quiz.js

const DIRECTION_OPTIONS = [["ko_en", "한 → 영"], ["en_ko", "영 → 한"], ["mixed", "혼합"]];
const TYPE_OPTIONS = [["short", "단답형"], ["choice", "4지선다형"], ["ox", "OX형"], ["mixed", "혼합"]];
const DIRECTION_LABEL = Object.fromEntries(DIRECTION_OPTIONS.map(([value, label]) => [value, label]));
const TYPE_LABEL = Object.fromEntries(TYPE_OPTIONS.map(([value, label]) => [value, label]));

// phase: "setup"(설정) | "question"(문항) | "summary"(결과)
const quizState = {
  root: null,
  phase: "setup",
  options: { count: 20, direction: "ko_en", questionType: "short" },
  run: null,        // { runId, total, questions }
  index: 0,
  feedback: null,   // 답한 뒤 서버 응답
  summary: null,
  busy: false,
};

window.Views.quiz = function renderQuiz(root) {
  quizState.root = root;
  if (quizState.phase === "question" && quizState.run) {
    drawQuestion();
  } else if (quizState.phase === "summary" && quizState.summary) {
    drawSummary();
  } else {
    quizState.phase = "setup";
    drawSetup();
  }
};

function drawSetup() {
  const options = quizState.options;
  const countInput = el("input", { type: "number", id: "quiz-count", min: 5, max: 100, value: options.count });
  const directionSelect = selectWith(DIRECTION_OPTIONS, options.direction, "quiz-direction");
  const typeSelect = selectWith(TYPE_OPTIONS, options.questionType, "quiz-type");

  quizState.root.replaceChildren(
    el("section", { class: "card" }, [
      el("h2", { text: "시험 설정" }),
      el("p", { class: "hint", text: "안 본 단어, 오래된 단어, 많이 틀린 단어가 더 자주 나옵니다." }),
      formRow("문제 수 (5~100)", countInput),
      formRow("방향", directionSelect),
      formRow("유형", typeSelect),
      el("div", { class: "button-row" }, [
        el("button", {
          class: "primary",
          text: "시험 시작",
          onclick: () => startQuiz({
            count: Number(countInput.value),
            direction: directionSelect.value,
            questionType: typeSelect.value,
          }),
        }),
      ]),
    ])
  );
}



async function startQuiz(options) {
  quizState.options = options;
  try {
    const run = await api("/api/quiz/runs", { method: "POST", body: options });
    beginRun(run);
  } catch (error) {
    showError(error);
  }
}

async function retryWrong() {
  try {
    const run = await api(`/api/quiz/runs/${quizState.run.runId}/retry`, {
      method: "POST",
      body: { direction: quizState.options.direction, questionType: quizState.options.questionType },
    });
    beginRun(run);
  } catch (error) {
    showError(error);
  }
}

function beginRun(run) {
  quizState.run = run;
  quizState.index = 0;
  quizState.feedback = null;
  quizState.summary = null;
  quizState.phase = "question";
  drawQuestion();
}

function drawQuestion() {
  const question = quizState.run.questions[quizState.index];
  const total = quizState.run.total;
  const children = [
    el("p", { class: "hint", text: `문제 ${quizState.index + 1} / ${total} · ${DIRECTION_LABEL[question.direction]} · ${TYPE_LABEL[question.type]}` }),
    el("h2", { class: "word", text: question.prompt }),
  ];
  if (question.type === "ox") {
    children.push(el("p", { class: "lead", text: `이 짝이 맞습니까?  ${question.candidate}` }));
  }
  children.push(answerControls(question));
  children.push(quizState.feedback ? feedbackBlock(quizState.feedback) : null);
  children.push(quizState.feedback ? nextButton() : null);
  quizState.root.replaceChildren(el("section", { class: "card quiz-card" }, children));
  const input = quizState.root.querySelector("input[type=text]");
  if (input && !quizState.feedback) input.focus();
}

// 유형에 맞는 입력 방식. 답한 뒤에는 모두 비활성화한다
function answerControls(question) {
  const locked = quizState.feedback !== null || quizState.busy;
  if (question.type === "choice") {
    return el("div", { class: "choice-grid" }, question.choices.map((choice, position) =>
      el("button", { text: `${position + 1}. ${choice}`, disabled: locked, onclick: () => submitAnswer(choice) })
    ));
  }
  if (question.type === "ox") {
    return el("div", { class: "button-row" }, ["O", "X"].map((mark) =>
      el("button", { class: "ox", text: mark, disabled: locked, onclick: () => submitAnswer(mark) })
    ));
  }
  const input = el("input", { type: "text", placeholder: "답을 입력하고 Enter", disabled: locked, autocomplete: "off" });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !locked) {
      event.preventDefault();
      submitAnswer(input.value);
    }
  });
  return el("div", { class: "button-row" }, [input, el("button", { class: "primary", text: "제출", disabled: locked, onclick: () => submitAnswer(input.value) })]);
}

async function submitAnswer(answer) {
  if (quizState.busy || quizState.feedback) return;
  quizState.busy = true;
  try {
    const feedback = await api(`/api/quiz/runs/${quizState.run.runId}/answers`, {
      method: "POST",
      body: { index: quizState.index, answer },
    });
    quizState.feedback = feedback;
    if (feedback.summary) quizState.summary = feedback.summary;
    drawQuestion();
  } catch (error) {
    showError(error);
  } finally {
    quizState.busy = false;
  }
}

function feedbackBlock(feedback) {
  const verdict = feedback.correct ? "정답입니다!" : "틀렸습니다.";
  const word = feedback.word;
  return el("div", { class: feedback.correct ? "feedback correct" : "feedback wrong" }, [
    el("p", { class: "lead", text: `${verdict}  정답: ${feedback.expected}` }),
    el("p", { text: `${word.word}  ${word.meaning}` }),
    el("p", { class: "example", text: word.example }),
  ]);
}

function nextButton() {
  return el("div", { class: "button-row" }, [
    el("button", { class: "primary", text: quizState.feedback.isFinished ? "결과 보기 (Enter)" : "다음 문제 (Enter)", onclick: goNext }),
  ]);
}

function goNext() {
  if (!quizState.feedback) return;
  if (quizState.feedback.isFinished) {
    quizState.phase = "summary";
    drawSummary();
    return;
  }
  quizState.index += 1;
  quizState.feedback = null;
  drawQuestion();
}

// Enter로 다음 문제 또는 결과 보기로 간다 (답한 뒤에만)
document.addEventListener("keydown", (event) => {
  if (window.currentView !== "quiz" || quizState.phase !== "question" || !quizState.feedback) return;
  if (event.key === "Enter" && event.target.tagName !== "BUTTON") {
    event.preventDefault();
    goNext();
  }
});

function drawSummary() {
  const summary = quizState.summary;
  const wrongRows = summary.wrong.map((item) =>
    el("tr", {}, [
      el("td", { text: item.word.word }),
      el("td", { text: item.prompt }),
      el("td", { text: item.expected }),
      el("td", { text: item.userAnswer || "(빈 답)" }),
    ])
  );
  const wrongTable = wrongRows.length
    ? el("table", {}, [
        el("thead", {}, el("tr", {}, ["단어", "문제", "정답", "내 답"].map((text) => el("th", { text })))),
        el("tbody", {}, wrongRows),
      ])
    : el("p", { text: "틀린 문항이 없습니다. 잘 하셨습니다!" });

  quizState.root.replaceChildren(
    el("section", { class: "card" }, [
      el("h2", { text: `${summary.correct} / ${summary.total} 정답 (${summary.accuracy}%)` }),
      el("h3", { text: "틀린 문항" }),
      wrongTable,
      el("div", { class: "button-row" }, [
        el("button", { text: "틀린 단어만 다시 시험", disabled: summary.wrong.length === 0, onclick: retryWrong }),
        el("button", { class: "primary", text: "새 시험", onclick: newQuiz }),
      ]),
    ])
  );
}

function newQuiz() {
  quizState.phase = "setup";
  quizState.run = null;
  quizState.summary = null;
  drawSetup();
}
