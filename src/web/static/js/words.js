// 2026-11-04 - SmartVoca - 단어 목록 화면: 검색, CSV 불러오기·내보내기 (FR-01, FR-02)
// 파일 위치: src/web/static/js/words.js

window.Views.words = function renderWords(root) {
  const searchInput = el("input", { type: "search", id: "word-search", placeholder: "단어, 품사, 뜻, 예문에서 검색", autocomplete: "off" });
  const countLabel = el("p", { class: "hint", id: "word-count" });
  const listBox = el("div", { id: "word-list" });
  const fileInput = el("input", { type: "file", accept: ".csv,text/csv", id: "word-file" });
  const resultBox = el("div", { class: "import-result", id: "import-result" });

  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadWords(searchInput.value, countLabel, listBox);
  });

  root.replaceChildren(
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
      el("p", { class: "hint", text: "CSV는 id, word, pos, meaning, example, level 열을 가져야 합니다. 같은 id는 덮어씁니다." }),
      el("div", { class: "button-row" }, [
        fileInput,
        el("button", { class: "primary", text: "CSV 불러오기", onclick: () => importCsv(fileInput, resultBox, countLabel, listBox) }),
        el("a", { class: "button-link", href: "/api/words/export", text: "CSV로 내보내기" }),
      ]),
      resultBox,
    ])
  );
  loadWords("", countLabel, listBox);
};

async function loadWords(keyword, countLabel, listBox) {
  const query = keyword.trim() ? `?q=${encodeURIComponent(keyword.trim())}` : "";
  try {
    const data = await api(`/api/words${query}`);
    countLabel.textContent = `${data.items.length} / ${data.total}개`;
    listBox.replaceChildren(wordTable(data.items));
  } catch (error) {
    showError(error);
  }
}

function wordTable(items) {
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
    ])
  );
  return el("div", { class: "table-scroll" }, el("table", {}, [
    el("thead", {}, el("tr", {}, ["번호", "단어", "품사", "뜻", "단계"].map((text) => el("th", { text })))),
    el("tbody", {}, rows),
  ]));
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
    const data = await api("/api/words/import", { method: "POST", form });
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
