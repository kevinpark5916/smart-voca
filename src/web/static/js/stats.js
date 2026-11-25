// 2026-11-25 - SmartVoca - 학습 통계 화면: 진도 현황, 날짜별 정답률 추이, 자주 틀린 단어 TOP 10 (VOCA-FR-031~034)
// 파일 위치: src/web/static/js/stats.js

window.Views.stats = function renderStats(root) {
  const startInput = el("input", { type: "date", id: "stats-start" });
  const endInput = el("input", { type: "date", id: "stats-end" });
  const progressBox = el("div", { id: "stats-progress" });
  const bodyBox = el("div", { id: "stats-body" });

  const load = () => loadStats(startInput.value, endInput.value, progressBox, bodyBox);
  root.replaceChildren(
    el("section", { class: "card" }, [
      el("h2", { text: "진도 현황" }),
      progressBox,
    ]),
    el("section", { class: "card" }, [
      el("h2", { text: "정답률 추이와 자주 틀린 단어" }),
      el("p", { class: "hint", text: "기간을 비우면 전체 기간입니다. 값은 모두 저장된 시험 이력으로 계산합니다." }),
      el("div", { class: "button-row" }, [
        formRow("시작", startInput),
        formRow("끝", endInput),
        el("button", { class: "primary", text: "조회", onclick: load }),
        el("button", { text: "전체 기간", onclick: () => { startInput.value = ""; endInput.value = ""; load(); } }),
      ]),
      bodyBox,
    ])
  );
  load();
};

async function loadStats(start, end, progressBox, bodyBox) {
  try {
    const query = new URLSearchParams();
    if (start) query.set("start", start);
    if (end) query.set("end", end);
    const suffix = query.toString() ? `?${query.toString()}` : "";
    const [home, stats] = await Promise.all([api("/api/home"), api(`/api/stats${suffix}`)]);
    progressBox.replaceChildren(progressSummary(home));
    bodyBox.replaceChildren(
      summaryLine(stats),
      stats.daily.length ? accuracyChart(stats.daily) : el("p", { text: "이 기간에 치른 시험이 없습니다." }),
      el("h3", { text: "자주 틀린 단어 TOP 10" }),
      wrongTable(stats.topWrong)
    );
  } catch (error) {
    showError(error);
  }
}

// 진도: 현재 일차, 암기한 단어 수 / 전체, 연속 학습일 (VOCA-FR-031)
function progressSummary(home) {
  const dayText = home.allDone ? "모두 외움" : `${home.dayNo}일차${home.inProgress ? " (진행 중)" : ""}`;
  return el("div", { class: "stat-grid" }, [
    statTile("현재", dayText),
    statTile("암기한 단어", `${home.studied} / ${home.total}`),
    statTile("연속 학습", `${home.streak}일`),
    statTile("하루 신규", `${home.dailyNewCount}개`),
  ]);
}

function summaryLine(stats) {
  const percent = `${Math.round(stats.accuracy * 100)}%`;
  return el("p", { text: `전체 정답률 ${percent} (응답 ${stats.totalAnswers}개, 정답 ${stats.totalCorrect}개)` });
}

// 날짜별 정답률 막대 그래프 (VOCA-FR-032). 막대 높이가 정답률이다
function accuracyChart(daily) {
  const bars = daily.map((item) => {
    const percent = Math.round(item.accuracy * 100);
    return el("div", { class: "bar-column", title: `${item.date}: ${percent}% (${item.correct}/${item.answers})` }, [
      el("div", { class: "bar-value", text: `${percent}%` }),
      el("div", { class: "bar", style: `height: ${Math.max(percent, 2)}%` }),
      el("div", { class: "bar-label", text: item.date.slice(5) }),
    ]);
  });
  return el("div", {}, [
    el("div", { class: "bar-chart", role: "img", "aria-label": "날짜별 정답률" }, bars),
    el("details", {}, [
      el("summary", { text: "표로 보기" }),
      el("table", {}, [
        el("thead", {}, el("tr", {}, ["날짜", "응답", "정답", "정답률"].map((text) => el("th", { text })))),
        el("tbody", {}, daily.map((item) =>
          el("tr", {}, [
            el("td", { text: item.date }),
            el("td", { text: item.answers }),
            el("td", { text: item.correct }),
            el("td", { text: `${Math.round(item.accuracy * 100)}%` }),
          ])
        )),
      ]),
    ]),
  ]);
}

function wrongTable(rows) {
  if (rows.length === 0) {
    return el("p", { text: "틀린 기록이 있는 단어가 없습니다." });
  }
  return el("table", {}, [
    el("thead", {}, el("tr", {}, ["단어", "응답", "오답"].map((text) => el("th", { text })))),
    el("tbody", {}, rows.map((row) =>
      el("tr", {}, [el("td", { text: row.word }), el("td", { text: row.attempts }), el("td", { text: row.wrong })])
    )),
  ]);
}

function statTile(label, value) {
  return el("div", { class: "stat-tile" }, [el("div", { class: "stat-label", text: label }), el("div", { class: "stat-value", text: value })]);
}
