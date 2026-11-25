// 2026-11-25 - SmartVoca - 단어 화면: 검색, 추가·수정·삭제, CSV 불러오기·내보내기 (VOCA-FR-001~004, FR-01, FR-02)
// 파일 위치: src/web/static/js/words.js

window.Views.words = function renderWords(root) {
  const searchInput = el("input", { type: "search", id: "word-search", placeholder: "단어, 품사, 뜻, 예문에서 검색", autocomplete: "off" });
  const countLabel = el("p", { class: "hint", id: "word-count" });
  const listBox = el("div", { id: "word-list" });
  const fileInput = el("input", { type: "file", accept: ".csv,text/csv", id: "word-file" });
  const resultBox = el("div", { class: "import-result", id: "import-result" });
  const form = buildWordForm(() => loadWords(searchInput.value, countLabel, listBox));

  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadWords(searchInput.value, countLabel, listBox);
  });

  root.replaceChildren(
    el("section", { class: "card" }, [
      el("h2", { text: "단어 추가·수정" }),
      form.node,
    ]),
    el("section", { class: "card" }, [
      el("h2", { text: "단어 목록" }),
      el("div", { class: "button-row" }, [
        searchInput,
        el("button", { text: "검색", onclick: () => loadWords(searchInput.value, countLabel, listBox) }),
        el("button", { text: "전체 보기", onclick: () => { searchInput.value = ""; loadWords("", countLabel, listBox); } }),
      ]),
      countLabel,
      listBox,
    ]),
    el("section", { class: "card" }, [
      el("h2", { text: "CSV 가져오기·내보내기" }),
      el("p", { class: "hint", text: "영단어와 뜻 두 열(영단어,뜻)만 있어도 됩니다. 번호는 자동으로 붙고, 이미 있는 영단어는 건너뜁니다. 전체 형식(id, word, pos, meaning, example, level)이면 같은 id는 덮어씁니다." }),
      el("div", { class: "button-row" }, [
        fileInput,
        el("button", { class: "primary", text: "CSV 불러오기", onclick: () => importCsv(fileInput, resultBox, countLabel, listBox) }),
        el("a", { class: "button-link", href: "api/words/export", text: "CSV로 내보내기" }),
      ]),
      resultBox,
    ])
  );
  form.reset();
  loadWords("", countLabel, listBox);
  // 목록 행의 '수정' 버튼이 이 함수를 부를 수 있도록 전역에 둔다
  window.editWordInForm = form.fill;
};

// 추가·수정 입력 폼. fill(word)로 수정 모드가 되고, reset()으로 추가 모드로 돌아간다
function buildWordForm(onSaved) {
  const inputs = {
    word: el("input", { type: "text", placeholder: "예: apple", maxlength: "60" }),
    meaning: el("input", { type: "text", placeholder: "예: 사과, 사과나무", maxlength: "120" }),
    pos: el("input", { type: "text", placeholder: "예: n.", maxlength: "20" }),
    example: el("input", { type: "text", placeholder: "예: An apple a day.", maxlength: "200" }),
    level: el("input", { type: "number", min: "1", max: "9", value: "1" }),
  };
  let editingId = null;
  const title = el("p", { class: "hint" });
  const saveButton = el("button", { class: "primary", text: "추가" });
  const cancelButton = el("button", { text: "취소", hidden: true, onclick: () => reset() });

  function reset() {
    editingId = null;
    inputs.word.value = "";
    inputs.meaning.value = "";
    inputs.pos.value = "";
    inputs.example.value = "";
    inputs.level.value = "1";
    title.textContent = "새 단어를 입력하세요.";
    saveButton.textContent = "추가";
    cancelButton.hidden = true;
  }

  function fill(word) {
    editingId = word.id;
    inputs.word.value = word.word;
    inputs.meaning.value = word.meaning;
    inputs.pos.value = word.pos;
    inputs.example.value = word.example;
    inputs.level.value = String(word.level);
    title.textContent = `번호 ${word.id} 단어를 고치는 중입니다.`;
    saveButton.textContent = "저장";
    cancelButton.hidden = false;
    inputs.word.scrollIntoView({ block: "center" });
  }

  async function save() {
    const body = {
      word: inputs.word.value,
      meaning: inputs.meaning.value,
      pos: inputs.pos.value,
      example: inputs.example.value,
      level: inputs.level.value,
    };
    try {
      if (editingId === null) {
        await api("api/words", { method: "POST", body });
        showToast("단어를 추가했습니다.");
      } else {
        await api(`api/words/${editingId}`, { method: "PUT", body });
        showToast("단어를 저장했습니다.");
      }
      reset();
      onSaved();
    } catch (error) {
      showError(error);
    }
  }

  saveButton.addEventListener("click", save);
  const node = el("div", { class: "word-form" }, [
    title,
    el("div", { class: "form-grid" }, [
      formRow("영단어", inputs.word),
      formRow("뜻", inputs.meaning),
      formRow("품사", inputs.pos),
      formRow("예문", inputs.example),
      formRow("단계", inputs.level),
    ]),
    el("div", { class: "button-row" }, [saveButton, cancelButton]),
  ]);
  reset();
  return { node, reset, fill: (word) => fill(word) };
}

async function loadWords(keyword, countLabel, listBox) {
  const query = keyword.trim() ? `?q=${encodeURIComponent(keyword.trim())}` : "";
  try {
    const data = await api(`api/words${query}`);
    countLabel.textContent = `${data.items.length} / ${data.total}개`;
    listBox.replaceChildren(wordTable(data.items, countLabel, listBox));
  } catch (error) {
    showError(error);
  }
}

function wordTable(items, countLabel, listBox) {
  if (items.length === 0) {
    return el("p", { text: "표시할 단어가 없습니다." });
  }
  const rows = items.map((word) =>
    el("tr", {}, [
      el("td", { text: word.id }),
      el("td", { text: word.word }),
      el("td", { text: word.pos }),
      el("td", { text: word.meaning }),
      el("td", { text: word.level }),
      el("td", {}, [
        el("button", { text: "수정", onclick: () => window.editWordInForm(word) }),
        el("button", { text: "삭제", onclick: () => deleteWord(word, countLabel, listBox) }),
      ]),
    ])
  );
  return el("div", { class: "table-scroll" }, el("table", {}, [
    el("thead", {}, el("tr", {}, ["번호", "단어", "품사", "뜻", "단계", ""].map((text) => el("th", { text })))),
    el("tbody", {}, rows),
  ]));
}

async function deleteWord(word, countLabel, listBox) {
  if (!window.confirm(`'${word.word}' 단어를 지울까요?`)) return;
  try {
    await api(`api/words/${word.id}`, { method: "DELETE" });
    showToast("단어를 지웠습니다.");
    loadWords("", countLabel, listBox);
  } catch (error) {
    showError(error);
  }
}

async function importCsv(fileInput, resultBox, countLabel, listBox) {
  const file = fileInput.files[0];
  if (!file) {
    showToast("CSV 파일을 먼저 선택해 주세요.", true);
    return;
  }
  const form = new FormData();
  form.append("file", file);
  try {
    const data = await api("api/words/import", { method: "POST", form });
    const errorItems = data.errors.map((message) => el("li", { text: message }));
    resultBox.replaceChildren(
      el("p", { text: `${data.count}개 단어를 저장했습니다.` }),
      errorItems.length ? el("details", {}, [el("summary", { text: `건너뛴 행 ${errorItems.length}건` }), el("ul", {}, errorItems)]) : null
    );
    loadWords("", countLabel, listBox);
  } catch (error) {
    showError(error);
  }
}
