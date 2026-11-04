// 2026-11-04 - SmartVoca - 웹 화면 공통: API 호출, DOM 만들기, 알림 메시지
// 파일 위치: src/web/static/js/api.js

// 각 화면 파일이 window.Views.<이름> = 함수(root) 형태로 자기 화면을 등록한다
window.Views = {};

// API를 호출한다. JSON 응답이면 객체를, 오류면 서버가 준 메시지로 Error를 던진다
async function api(path, options = {}) {
  const init = { method: options.method || "GET", headers: {} };
  if (options.body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  if (options.form !== undefined) {
    init.body = options.form;  // 파일 업로드는 FormData를 그대로 보낸다
  }
  const response = await fetch(path, init);
  const isJson = (response.headers.get("Content-Type") || "").includes("application/json");
  if (!isJson) {
    if (!response.ok) throw new Error(`요청 실패 (${response.status})`);
    return response;
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `요청 실패 (${response.status})`);
  return data;
}

// DOM 요소를 만든다. text는 textContent로 넣어 HTML이 해석되지 않게 한다 (입력값 보호)
function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "text") {
      node.textContent = value;
    } else if (key === "class") {
      node.className = value;
    } else if (key.startsWith("on")) {
      node.addEventListener(key.slice(2), value);
    } else if (typeof value === "boolean") {
      // 불리언 속성은 값이 true일 때만 붙인다 (예: disabled)
      if (value) node.setAttribute(key, "");
    } else if (value !== undefined && value !== null) {
      node.setAttribute(key, value);
    }
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

// 화면 아래 알림 말풍선. 오류면 빨간색으로 3.5초 보여 준다
let toastTimer = null;
function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = isError ? "toast error" : "toast";
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 3500);
}

function showError(error) {
  showToast(error.message || String(error), true);
}

// 'label + 입력 칸' 한 줄 (설정·시험 화면 공통)
function formRow(label, control) {
  return el("label", { class: "form-row" }, [el("span", { text: label }), control]);
}

// 선택 목록을 만든다. options는 [[값, 이름], ...]
function selectWith(options, selected, id) {
  const select = el("select", id ? { id } : {});
  for (const [value, label] of options) {
    select.append(el("option", { value, text: label, selected: value === selected }));
  }
  return select;
}
