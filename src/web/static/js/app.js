// 2026-11-04 - SmartVoca - 웹 앱 진입 스크립트: 상단 탭 구성, 화면 전환, 테마·글자 크기 적용
// 파일 위치: src/web/static/js/app.js

const TAB_LIST = [
  ["home", "홈"],
  ["study", "암기"],
  ["quiz", "시험"],
  ["history", "이력"],
  ["stats", "통계"],
  ["words", "단어 목록"],
  ["settings", "설정"],
];

window.currentView = null;

// 화면 전환. 각 화면 함수는 자기 root에 내용을 그린다
window.navigate = async function navigate(name) {
  window.currentView = name;
  for (const button of document.querySelectorAll("#tabs button")) {
    button.classList.toggle("active", button.dataset.tab === name);
  }
  const root = document.getElementById("view");
  try {
    await window.Views[name](root);
  } catch (error) {
    showError(error);
  }
};

// 설정 저장 후(또는 처음 불러올 때) 테마와 글자 크기를 화면 전체에 적용한다
window.applySettings = function applySettings(settings) {
  document.body.dataset.theme = settings.theme;
  document.documentElement.dataset.font = settings.font_scale;
};

function buildTabs() {
  const nav = document.getElementById("tabs");
  for (const [name, label] of TAB_LIST) {
    nav.append(el("button", { "data-tab": name, text: label, onclick: () => window.navigate(name) }));
  }
}

async function start() {
  buildTabs();
  try {
    window.applySettings(await api("api/settings"));
  } catch (error) {
    showError(error);
  }
  window.navigate("home");
}

start();
