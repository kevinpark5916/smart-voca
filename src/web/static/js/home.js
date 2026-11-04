// 2026-11-04 - SmartVoca - 홈 화면: 오늘 할 일, 전체 진도, 연속 학습일, 최근 정답률 (FR-03, FR-17)
// 파일 위치: src/web/static/js/home.js

window.Views.home = async function renderHome(root) {
  const data = await api("/api/home");

  let plan;
  if (data.total === 0) {
    plan = "단어가 없습니다. '단어 목록'에서 CSV를 불러오세요.";
  } else if (data.allDone) {
    plan = "모든 단어를 외웠습니다!";
  } else {
    const state = data.inProgress ? " (진행 중)" : "";
    plan = `${data.dayNo}일차${state} · 신규 최대 ${data.dailyNewCount}개 · 복습 최대 ${data.dailyReviewCount}개`;
  }
  const percent = data.total ? Math.round((data.studied / data.total) * 100) : 0;
  const streakText = data.streak ? `연속 학습 ${data.streak}일` : "오늘 학습을 시작해 보세요.";
  const accuracyText = data.recentAnswers
    ? `최근 ${data.recentQuizCount}회 시험 정답률 ${Math.round((data.recentCorrect / data.recentAnswers) * 100)}% (${data.recentAnswers}문항)`
    : "아직 시험 기록이 없습니다.";

  root.replaceChildren(
    el("section", { class: "card" }, [
      el("h2", { text: "오늘의 학습" }),
      el("p", { class: "lead", text: plan }),
      el("div", { class: "progress" }, el("div", { class: "bar", style: `width: ${percent}%` })),
      el("p", { text: `암기한 단어 ${data.studied} / ${data.total}개 (${percent}%)` }),
      el("p", { text: streakText }),
      el("p", { text: accuracyText }),
      el("div", { class: "button-row" }, [
        navButton("오늘 암기하기", "study"),
        navButton("시험 보기", "quiz"),
        navButton("이력 보기", "history"),
        navButton("단어 목록", "words"),
      ]),
    ])
  );
};

// 홈의 바로가기 버튼. 누르면 해당 탭으로 이동한다 (app.js의 navigate)
function navButton(text, tabName) {
  return el("button", { class: "primary", text, onclick: () => window.navigate(tabName) });
}
