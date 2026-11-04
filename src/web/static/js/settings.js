// 2026-11-04 - SmartVoca - 설정 화면: 하루 단어 수, 시험 문제 수, 가중치, 테마·글자 크기 저장 (FR-13, FR-22)
// 파일 위치: src/web/static/js/settings.js

// 입력 항목: [설정 키, 라벨, 입력 종류, 최소, 최대, 단계]
const NUMBER_FIELDS = [
  ["daily_new_count", "하루 신규 단어 수 (1~200)", 1, 200, 1],
  ["daily_review_count", "하루 복습 단어 최대 수 (0~100)", 0, 100, 1],
  ["quiz_question_count", "시험 문제 수 기본값 (5~100)", 5, 100, 1],
  ["old_days", "오래됨 기준 (일, 1~365)", 1, 365, 1],
  ["weight_new", "가중치: 시험 이력 없음", 0, null, 0.1],
  ["weight_old", "가중치: 오래됨", 0, null, 0.1],
  ["weight_wrong", "가중치: 오답률 배수", 0, null, 0.1],
];

window.Views.settings = async function renderSettings(root) {
  const settings = await api("/api/settings");
  const inputs = {};
  const rows = NUMBER_FIELDS.map(([key, label, min, max, step]) => {
    const input = el("input", { type: "number", id: `setting-${key}`, min, step, value: settings[key] });
    if (max !== null) input.max = max;
    inputs[key] = input;
    return formRow(label, input);
  });
  const theme = selectWith([["light", "밝게"], ["dark", "어둡게"]], settings.theme);
  const fontScale = selectWith([["small", "작게"], ["normal", "보통"], ["large", "크게"]], settings.font_scale);
  inputs.theme = theme;
  inputs.font_scale = fontScale;

  root.replaceChildren(
    el("section", { class: "card" }, [
      el("h2", { text: "설정" }),
      ...rows,
      formRow("테마", theme),
      formRow("글자 크기", fontScale),
      el("div", { class: "button-row" }, [
        el("button", { class: "primary", text: "저장", onclick: () => saveSettings(inputs) }),
      ]),
    ])
  );
};

async function saveSettings(inputs) {
  const body = {};
  for (const [key, input] of Object.entries(inputs)) {
    if (key === "theme" || key === "font_scale") {
      body[key] = input.value;
    } else {
      body[key] = Number(input.value);
    }
  }
  try {
    const saved = await api("/api/settings", { method: "PUT", body });
    window.applySettings(saved);
    showToast("설정을 저장했습니다.");
  } catch (error) {
    showError(error);
  }
}


