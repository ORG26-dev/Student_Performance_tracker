/* Student Performance Analysis System - browser side.
   Talks to the Flask API in app.py using fetch(). */
(() => {
  const $ = (selector) => document.querySelector(selector);
  const esc = (value) => String(value).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const num = (n) => Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 });

  const state = {
    compareId: null,
    students: [], summary: null, subjects: [], passMarks: 40, maxMarks: 100,
    sort: { key: "Rank", dir: 1 }, query: "", editingId: null, openId: null,
  };

  /* ---------- talking to Python ---------- */
  async function api(url, options = {}) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Something went wrong. Try again.");
    return data;
  }

  async function load() {
    try {
      const [list, summary] = await Promise.all([api("/api/students"), api("/api/summary")]);
      state.students = list.students;
      state.subjects = list.subjects;
      state.passMarks = list.pass_marks;
      state.maxMarks = list.max_marks;
      state.summary = summary;
      render();
    } catch (err) {
      $("#summaryLine").textContent = "Could not reach the Python server. Start it with: python app.py";
    }
  }

  /* ---------- helpers ---------- */
  function heat(mark) {
    if (mark < state.passMarks) {
      const strength = 0.12 + ((state.passMarks - mark) / state.passMarks) * 0.22;
      return `background:rgba(183,47,67,${strength.toFixed(2)});color:#7a1626`;
    }
    const t = (mark - state.passMarks) / (state.maxMarks - state.passMarks);
    return `background:rgba(14,124,134,${(0.05 + t * 0.45).toFixed(2)})`;
  }

  function visibleStudents() {
    const q = state.query.trim().toLowerCase();
    let rows = state.students.filter((s) =>
      !q || s.Name.toLowerCase().includes(q) || String(s.ID).includes(q));
    const { key, dir } = state.sort;
    rows = [...rows].sort((a, b) => {
      const x = a[key], y = b[key];
      const result = typeof x === "string" ? x.localeCompare(y) : x - y;
      return result * dir || a.Rank - b.Rank;
    });
    return rows;
  }

  function failedSubjects(student) {
    return state.subjects.filter((s) => student[s] < state.passMarks);
  }

  function toast(message, bad = false) {
    const el = $("#toast");
    el.textContent = message;
    el.className = "toast" + (bad ? " bad" : "");
    el.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => { el.hidden = true; }, 3500);
  }

  /* ---------- rendering ---------- */
  function render() {
    renderSummary();
    renderTable();
    renderInsights();
    renderCharts();
  }

  function renderSummary() {
    const s = state.summary;
    if (!s || s.count === 0) {
      $("#summaryLine").textContent = "No students yet. Add a student to see grades, ranks and charts.";
      return;
    }
    $("#summaryLine").innerHTML =
      `<strong>${s.count} students.</strong> Class average is <strong>${num(s.average)}%</strong> and ` +
      `<strong>${num(s.pass_rate)}%</strong> passed every subject. Top scorer is ` +
      `<strong>${esc(s.top.name)}</strong> with ${num(s.top.percentage)}%.`;
  }

  function renderTable() {
    const cols = [
      { key: "Rank", label: "Rank" },
      { key: "Name", label: "Student", left: true },
      ...state.subjects.map((s) => ({ key: s, label: s })),
      { key: "Total", label: "Total" },
      { key: "Percentage", label: "Percent" },
      { key: "Grade", label: "Grade", plain: true },
      { key: "Result", label: "Result", plain: true },
    ];
    $("#regHead").innerHTML = "<tr>" + cols.map((c) => {
      if (c.plain) return `<th class="plain" scope="col">${c.label}</th>`;
      const active = state.sort.key === c.key;
      const aria = active ? ` aria-sort="${state.sort.dir === 1 ? "ascending" : "descending"}"` : "";
      return `<th scope="col" class="${c.left ? "left" : ""}"${aria}>` +
        `<button type="button" data-sort="${c.key}">${c.label}</button></th>`;
    }).join("") + "</tr>";

    const rows = visibleStudents();
    const body = $("#regBody");
    if (rows.length === 0) {
      const none = state.students.length === 0;
      body.innerHTML = `<tr><td colspan="${cols.length}"><div class="empty">` +
        (none
          ? `<p>The register is empty. Add the first student to start ranking.</p><button class="btn primary" type="button" data-add>Add student</button>`
          : `<p>No students match "${esc(state.query)}". Check the spelling or clear the search.</p>`) +
        `</div></td></tr>`;
      return;
    }
    body.innerHTML = rows.map((s) => {
      const marks = state.subjects.map((sub) =>
        `<td><span class="cell" style="${heat(s[sub])}">${num(s[sub])}</span></td>`).join("");
      return `<tr class="row" data-id="${s.ID}">` +
        `<td class="plain rank">${s.Rank}</td>` +
        `<td class="left"><button type="button" class="who"><span class="nm">${esc(s.Name)}</span><span class="sid">ID ${s.ID}</span></button></td>` +
        marks +
        `<td class="plain">${num(s.Total)}</td>` +
        `<td class="plain">${num(s.Percentage)}%</td>` +
        `<td class="plain grade">${s.Grade}</td>` +
        `<td class="plain ${s.Result === "Pass" ? "pass" : "fail"}">${s.Result}</td></tr>`;
    }).join("");
  }

  function renderInsights() {
    const s = state.summary;
    const bars = $("#subjectBars");
    if (!s || s.count === 0) {
      bars.innerHTML = '<p class="note">Subject averages appear once you add students.</p>';
      $("#subjectNote").textContent = "";
      $("#gradeCols").innerHTML = "";
      $("#attention").innerHTML = '<li class="none">Nobody to review yet.</li>';
      return;
    }
    const stats = s.subject_stats;
    const best = stats.reduce((a, b) => (b.Average > a.Average ? b : a));
    const worst = stats.reduce((a, b) => (b.Average < a.Average ? b : a));
    bars.innerHTML = stats.map((st) => {
      const cls = st.Subject === best.Subject ? "strong" : st.Subject === worst.Subject ? "weak" : "";
      return `<div class="bar-row"><span>${esc(st.Subject)}</span>` +
        `<div class="track"><div class="fill ${cls}" style="width:${(st.Average / state.maxMarks) * 100}%"></div></div>` +
        `<span class="val">${num(st.Average)}</span></div>`;
    }).join("");
    $("#subjectNote").textContent = `${best.Subject} is the strongest subject and ${worst.Subject} is the weakest.`;

    const counts = s.grades;
    const max = Math.max(...counts.map((x) => x.count), 1);
    $("#gradeCols").innerHTML = counts.map(({ grade: g, count: n }) =>
      `<div class="gcol${g === "F" ? " f" : ""}"><span class="count">${n}</span>` +
      `<div class="gbar" style="height:${(n / max) * 96}px"></div><span class="gl">${g}</span></div>`).join("");

    const weak = state.students.filter((st) => failedSubjects(st).length);
    $("#attention").innerHTML = weak.length
      ? weak.map((st) => `<li><strong>${esc(st.Name)}</strong><span>Below ${state.passMarks} in ${failedSubjects(st).join(", ")}</span></li>`).join("")
      : '<li class="none">Everyone passed every subject.</li>';
  }


  function compareHtml(st) {
    const avg = Object.fromEntries(state.summary.subject_stats.map((x) => [x.Subject, x.Average]));
    return state.subjects.map((sub) =>
      `<div class="cmp"><span>${esc(sub)}</span>` +
      `<div class="track"><div class="fill ${st[sub] < state.passMarks ? "weak" : ""}" style="width:${(st[sub] / state.maxMarks) * 100}%"></div>` +
      `<i class="avg" style="left:${(avg[sub] / state.maxMarks) * 100}%"></i></div>` +
      `<span class="val">${num(st[sub])} <small>(avg ${num(avg[sub])})</small></span></div>`).join("");
  }

  function renderCharts() {
    const empty = '<p class="note">This chart appears once you add students.</p>';
    if (!state.students.length) {
      $("#topBars").innerHTML = empty;
      $("#histCols").innerHTML = "";
      $("#compareBars").innerHTML = empty;
      $("#compareSelect").innerHTML = "";
      return;
    }
    // Top 5 students (list is already sorted by rank)
    $("#topBars").innerHTML = state.students.slice(0, 5).map((s) =>
      `<div class="bar-row wide"><span title="${esc(s.Name)}">${esc(s.Name)}</span>` +
      `<div class="track"><div class="fill strong" style="width:${s.Percentage}%"></div></div>` +
      `<span class="val">${num(s.Percentage)}%</span></div>`).join("");

    // Percentage histogram, 10 bins of width 10
    const bins = Array(10).fill(0);
    state.students.forEach((s) => { bins[Math.min(Math.floor(s.Percentage / 10), 9)] += 1; });
    const top = Math.max(...bins, 1);
    $("#histCols").innerHTML = bins.map((n, i) =>
      `<div class="gcol${i * 10 < 40 ? " f" : ""}"><span class="count">${n}</span>` +
      `<div class="gbar" style="height:${(n / top) * 96}px"></div><span class="gl">${i * 10}</span></div>`).join("");

    // Student against class average
    if (!state.students.some((s) => s.ID === state.compareId)) state.compareId = state.students[0].ID;
    $("#compareSelect").innerHTML = state.students.map((s) =>
      `<option value="${s.ID}"${s.ID === state.compareId ? " selected" : ""}>${esc(s.Name)} (ID ${s.ID})</option>`).join("");
    $("#compareBars").innerHTML = compareHtml(state.students.find((s) => s.ID === state.compareId));
  }

  /* ---------- student detail sheet ---------- */
  function openDetail(id) {
    const st = state.students.find((s) => s.ID === id);
    if (!st) return;
    state.openId = id;
    const failed = failedSubjects(st);
    const outcome = failed.length ? `Below the pass mark in ${failed.join(", ")}.` : "Passed every subject.";
    const rows = compareHtml(st);
    const dlg = $("#detail");
    dlg.innerHTML =
      `<div class="sheet-head"><div><h2 id="detailName">${esc(st.Name)}</h2><p class="muted">Student ID ${st.ID}</p></div>` +
      `<button class="btn" type="button" data-close>Close</button></div>` +
      `<div class="sheet-body"><p class="verdict"><strong>Rank ${st.Rank} of ${state.students.length}.</strong> ` +
      `Grade ${st.Grade} with ${num(st.Percentage)}% (${num(st.Total)} of ${state.maxMarks * state.subjects.length}). ${outcome}</p>` +
      `<h3>Marks compared with the class average</h3>${rows}` +
      `<p class="key"><i></i> Class average</p></div>` +
      `<div class="sheet-foot"><button class="btn" type="button" data-edit>Edit marks</button>` +
      `<button class="btn danger" type="button" data-delete>Delete student</button></div>`;
    if (!dlg.open) dlg.showModal();
  }

  /* ---------- add / edit form ---------- */
  function openForm(student = null) {
    state.editingId = student ? student.ID : null;
    $("#formTitle").textContent = student ? `Edit ${student.Name}` : "Add student";
    $("#formSave").textContent = student ? "Save changes" : "Add student";
    $("#formError").textContent = "";
    const nextId = state.students.reduce((m, s) => Math.max(m, s.ID), 100) + 1;
    const field = (id, label, value, extra = "", wide = false) =>
      `<div class="field${wide ? " wide" : ""}"><label for="${id}">${label}</label>` +
      `<input id="${id}" name="${id}" value="${esc(value)}" ${extra}></div>`;
    $("#formFields").innerHTML =
      field("f-ID", "Student ID", student ? student.ID : nextId, `type="number" min="1" step="1" required ${student ? "disabled" : ""}`) +
      field("f-Name", "Full name", student ? student.Name : "", 'type="text" maxlength="60" required autocomplete="off"') +
      state.subjects.map((sub) =>
        field(`f-${sub}`, `${sub} marks (0 to ${state.maxMarks})`, student ? student[sub] : "",
          `type="number" min="0" max="${state.maxMarks}" step="0.5" required inputmode="decimal"`)).join("");
    const dlg = $("#formDialog");
    if (!dlg.open) dlg.showModal();
    $(student ? "#f-Name" : "#f-ID").focus();
  }

  async function submitForm(event) {
    event.preventDefault();
    const payload = { ID: $("#f-ID").value, Name: $("#f-Name").value };
    state.subjects.forEach((sub) => { payload[sub] = $(`#f-${sub}`).value; });
    const editing = state.editingId !== null;
    try {
      await api(editing ? `/api/students/${state.editingId}` : "/api/students", {
        method: editing ? "PUT" : "POST", body: JSON.stringify(payload),
      });
      $("#formDialog").close();
      await load();
      toast(editing ? `Saved changes to ${payload.Name}.` : `Added ${payload.Name}.`);
      if (editing && $("#detail").open) openDetail(state.editingId);
    } catch (err) {
      $("#formError").textContent = err.message;
    }
  }

  /* ---------- delete & export ---------- */
  function askDelete() {
    const st = state.students.find((s) => s.ID === state.openId);
    if (!st) return;
    $("#confirmText").textContent = `${st.Name} and their marks will be removed from the register. This cannot be undone.`;
    $("#confirmDialog").showModal();
  }

  async function confirmDelete() {
    const st = state.students.find((s) => s.ID === state.openId);
    try {
      await api(`/api/students/${state.openId}`, { method: "DELETE" });
      $("#confirmDialog").close();
      $("#detail").close();
      await load();
      toast(`Deleted ${st.Name}.`);
    } catch (err) {
      $("#confirmDialog").close();
      toast(err.message, true);
    }
  }

  async function downloadReport() {
    try {
      const response = await fetch("/api/report");
      if (!response.ok) throw new Error((await response.json()).error);
      const url = URL.createObjectURL(await response.blob());
      const link = Object.assign(document.createElement("a"), { href: url, download: "performance_report.txt" });
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast("Report downloaded.");
    } catch (err) {
      toast(err.message || "Could not create the report.", true);
    }
  }

  /* ---------- events ---------- */
  document.addEventListener("click", (e) => {
    const sortBtn = e.target.closest("[data-sort]");
    if (sortBtn) {
      const key = sortBtn.dataset.sort;
      if (state.sort.key === key) state.sort.dir *= -1;
      else state.sort = { key, dir: key === "Rank" || key === "Name" ? 1 : -1 };
      renderTable();
      return;
    }
    if (e.target.closest("[data-add]")) return openForm();
    const row = e.target.closest("tr.row");
    if (row) return openDetail(Number(row.dataset.id));
    if (e.target.closest("[data-close]")) return $("#detail").close();
    if (e.target.closest("[data-edit]")) return openForm(state.students.find((s) => s.ID === state.openId));
    if (e.target.closest("[data-delete]")) return askDelete();
  });

  $("#addBtn").addEventListener("click", () => openForm());
  $("#exportBtn").addEventListener("click", downloadReport);
  $("#compareSelect").addEventListener("change", (e) => { state.compareId = Number(e.target.value); renderCharts(); });
  $("#search").addEventListener("input", (e) => { state.query = e.target.value; renderTable(); });
  $("#studentForm").addEventListener("submit", submitForm);
  $("#formCancel").addEventListener("click", () => $("#formDialog").close());
  $("#confirmCancel").addEventListener("click", () => $("#confirmDialog").close());
  $("#confirmOk").addEventListener("click", confirmDelete);
  $("#detail").addEventListener("click", (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });

  load();
})();
