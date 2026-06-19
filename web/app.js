/* SiteLedger — frontend logic */
(() => {
  "use strict";

  const state = {
    projects: [],
    projectId: null,
    currency: "$",
    tab: "overview",
    history: [],          // chat history for the active project
    aiEnabled: true,
  };

  // ----- tiny helpers -----------------------------------------------------
  const $ = (sel) => document.querySelector(sel);
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };
  const esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const money = (n) => {
    const v = Number(n || 0);
    return state.currency + v.toLocaleString(undefined, { maximumFractionDigits: 0 });
  };
  const dateStr = (s) => (s ? String(s).slice(0, 10) : "");

  async function api(path, opts) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try { detail = (await res.json()).detail || detail; } catch (_) {}
      throw new Error(detail);
    }
    return res.status === 204 ? null : res.json();
  }

  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.remove("hidden");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.add("hidden"), 2600);
  }

  // ----- pills ------------------------------------------------------------
  const STATUS_PILL = {
    not_started: "gray", in_progress: "blue", blocked: "red", done: "green",
    paid: "green", pending: "amber", partial: "amber",
    open: "red", resolved: "green",
    low: "gray", medium: "blue", high: "amber", critical: "red",
  };
  const pill = (val) =>
    `<span class="pill ${STATUS_PILL[val] || "gray"}">${esc(String(val).replace(/_/g, " "))}</span>`;

  // ----- boot -------------------------------------------------------------
  async function boot() {
    try {
      const health = await api("/api/health");
      state.aiEnabled = health.ai_enabled;
    } catch (_) {}
    await loadProjects();
    wireEvents();
  }

  async function loadProjects() {
    state.projects = await api("/api/projects");
    const sel = $("#project-select");
    sel.innerHTML = "";
    state.projects.forEach((p) => {
      const o = el("option");
      o.value = p.id;
      o.textContent = p.name;
      sel.appendChild(o);
    });

    if (!state.projects.length) {
      $("#empty-state").classList.remove("hidden");
      $("#app").classList.add("hidden");
      $("#assistant-fab").classList.add("hidden");
      return;
    }
    $("#empty-state").classList.add("hidden");
    $("#app").classList.remove("hidden");
    if (window.innerWidth <= 900) $("#assistant-fab").classList.remove("hidden");

    if (!state.projectId || !state.projects.find((p) => p.id == state.projectId)) {
      state.projectId = state.projects[0].id;
    }
    sel.value = state.projectId;
    await selectProject(state.projectId);
  }

  async function selectProject(id) {
    state.projectId = Number(id);
    const proj = state.projects.find((p) => p.id == id);
    state.currency = (proj && proj.currency) || "$";
    state.history = [];
    resetChat();
    await refreshDashboard();
  }

  async function refreshDashboard() {
    await renderSummary();
    await renderTab(state.tab);
  }

  // ----- summary ----------------------------------------------------------
  async function renderSummary() {
    const s = await api(`/api/projects/${state.projectId}/summary`);
    const wrap = $("#summary");
    const remainCls = s.over_budget ? "bad" : "good";
    const fillCls = s.over_budget ? "over" : (s.percent_spent >= 100 ? "done" : "");
    wrap.innerHTML = "";

    wrap.appendChild(metric("Budget", money(s.budget), s.budget ? "" : "no budget set"));

    const spent = metric("Spent", money(s.spent),
      `${money(s.spent_materials)} materials · ${money(s.spent_labour)} labour`);
    spent.appendChild(progress(Math.min(s.percent_spent, 100), fillCls,
      s.budget ? `${s.percent_spent}% of budget` : ""));
    wrap.appendChild(spent);

    wrap.appendChild(metric("Remaining", money(s.remaining),
      s.outstanding ? `${money(s.outstanding)} still owed` : "", remainCls));

    const prog = metric("Milestones", `${s.milestones_done}/${s.milestones_total}`,
      s.issues_open ? `${s.issues_open} open issue${s.issues_open === 1 ? "" : "s"}` : "no open issues");
    prog.appendChild(progress(s.milestone_progress, s.milestone_progress >= 100 ? "done" : "", ""));
    wrap.appendChild(prog);
  }

  function metric(label, value, sub, cls) {
    const m = el("div", "metric" + (cls ? " " + cls : ""));
    m.appendChild(el("div", "label", esc(label)));
    m.appendChild(el("div", "value", esc(value)));
    if (sub) m.appendChild(el("div", "sub", esc(sub)));
    return m;
  }
  function progress(pct, cls, caption) {
    const wrap = el("div");
    const track = el("div", "progress-track");
    const fill = el("div", "progress-fill" + (cls ? " " + cls : ""));
    fill.style.width = Math.max(0, Math.min(100, pct)) + "%";
    track.appendChild(fill);
    wrap.appendChild(track);
    if (caption) wrap.appendChild(el("div", "sub", esc(caption)));
    return wrap;
  }

  // ----- tabs -------------------------------------------------------------
  async function renderTab(tab) {
    state.tab = tab;
    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.toggle("active", t.dataset.tab === tab));
    const c = $("#tab-content");
    c.innerHTML = '<div class="panel"><div class="empty-list">Loading…</div></div>';

    const pid = state.projectId;
    if (tab === "overview") return renderOverview(c, pid);
    if (tab === "expenses") return renderList(c, pid, "expenses", "Expenses", expenseRow);
    if (tab === "payments") return renderList(c, pid, "payments", "Artisan payments", paymentRow);
    if (tab === "milestones") return renderList(c, pid, "milestones", "Milestones", milestoneRow);
    if (tab === "artisans") return renderList(c, pid, "artisans", "Artisans & workers", artisanRow);
    if (tab === "issues") return renderList(c, pid, "issues", "Issues", issueRow);
    if (tab === "notes") return renderList(c, pid, "notes", "Design & construction notes", noteRow);
  }

  // ----- add forms (manual entry, no AI) ----------------------------------
  const TODAY = () => new Date().toISOString().slice(0, 10);
  const ADD_SPECS = {
    expenses: {
      label: "Add expense", required: ["amount"],
      fields: [
        { name: "description", type: "text", ph: "What was bought / paid for", grow: true },
        { name: "amount", type: "number", ph: "Amount" },
        { name: "category", type: "text", ph: "Category", value: "materials" },
        { name: "vendor", type: "text", ph: "Vendor (optional)" },
        { name: "spent_on", type: "date", value: TODAY },
        { name: "payment_status", type: "select",
          options: [["paid", "Paid"], ["pending", "Owed / on credit"]] },
      ],
    },
    payments: {
      label: "Add payment", required: ["artisan_name", "amount"],
      fields: [
        { name: "artisan_name", type: "text", ph: "Who was paid", grow: true },
        { name: "amount", type: "number", ph: "Amount" },
        { name: "description", type: "text", ph: "What for, e.g. casting walls" },
        { name: "paid_on", type: "date", value: TODAY },
        { name: "status", type: "select",
          options: [["paid", "Paid"], ["partial", "Part-paid"], ["pending", "Owed"]] },
      ],
    },
    milestones: {
      label: "Add stage", required: ["name"],
      fields: [
        { name: "name", type: "text", ph: "Stage / phase name", grow: true },
        { name: "description", type: "text", ph: "Detail (optional)", grow: true },
        { name: "status", type: "select",
          options: [["not_started", "To-do"], ["in_progress", "Active"],
                    ["blocked", "Blocked"], ["done", "Done"]] },
        { name: "target_date", type: "date" },
      ],
    },
    artisans: {
      label: "Add worker", required: ["name"],
      fields: [
        { name: "name", type: "text", ph: "Name", grow: true },
        { name: "trade", type: "text", ph: "Trade, e.g. mason" },
        { name: "phone", type: "text", ph: "Phone (optional)" },
        { name: "agreed_rate", type: "number", ph: "Agreed rate (optional)" },
        { name: "notes", type: "text", ph: "Notes (optional)", grow: true },
      ],
    },
    issues: {
      label: "Log issue", required: ["title"],
      fields: [
        { name: "title", type: "text", ph: "What's the problem?", grow: true },
        { name: "description", type: "text", ph: "Detail (optional)", grow: true },
        { name: "severity", type: "select",
          options: [["low", "Low"], ["medium", "Medium"], ["high", "High"], ["critical", "Critical"]],
          value: "medium" },
      ],
    },
    notes: {
      label: "Add note", required: ["title"],
      fields: [
        { name: "title", type: "text", ph: "Title", grow: true },
        { name: "category", type: "select",
          options: [["construction", "Construction"], ["design", "Design"],
                    ["material", "Material"], ["general", "General"]] },
        { name: "content", type: "textarea", ph: "Details, specs, decisions…" },
      ],
    },
  };

  function buildAddForm(type) {
    const spec = ADD_SPECS[type];
    const form = el("form", "add-form");
    spec.fields.forEach((f) => {
      let input;
      if (f.type === "select") {
        input = el("select");
        f.options.forEach(([v, l]) => {
          const o = el("option"); o.value = v; o.textContent = l; input.appendChild(o);
        });
        if (f.value) input.value = f.value;
      } else if (f.type === "textarea") {
        input = el("textarea"); input.rows = 2;
        if (f.ph) input.placeholder = f.ph;
      } else {
        input = el("input");
        input.type = f.type || "text";
        if (f.type === "number") { input.step = "any"; input.min = "0"; }
        if (f.ph) input.placeholder = f.ph;
        const v = typeof f.value === "function" ? f.value() : f.value;
        if (v != null) input.value = v;
      }
      input.name = f.name;
      if (f.grow) input.classList.add("grow");
      form.appendChild(input);
    });
    const save = el("button", "btn btn-primary", "Save");
    save.type = "submit";
    form.appendChild(save);
    form.addEventListener("submit", (e) => { e.preventDefault(); submitAdd(type, form); });
    return form;
  }

  async function submitAdd(type, form) {
    const spec = ADD_SPECS[type];
    const body = {};
    spec.fields.forEach((f) => {
      const node = form.elements[f.name];
      let val = node.value;
      if (f.type === "number") val = val === "" ? null : parseFloat(val);
      else if (f.type === "date") val = val || null;
      else val = (val || "").trim();
      body[f.name] = val;
    });
    for (const r of (spec.required || [])) {
      if (body[r] == null || body[r] === "") { toast("Please fill in " + r.replace(/_/g, " ")); return; }
    }
    try {
      await api(`/api/projects/${state.projectId}/${type}`,
        { method: "POST", body: JSON.stringify(body) });
      toast("Saved");
      await refreshDashboard();
    } catch (e) { toast(e.message); }
  }

  async function renderList(container, pid, type, title, rowFn) {
    const rows = await api(`/api/projects/${pid}/${type}`);
    const panel = el("div", "panel");

    const head = el("div", "panel-head");
    head.appendChild(el("h3", null, esc(title)));
    const form = buildAddForm(type);
    const addBtn = el("button", "btn-add", "＋ " + ADD_SPECS[type].label);
    addBtn.onclick = () => {
      const open = form.classList.toggle("open");
      if (open) { const first = form.querySelector("input,select,textarea"); if (first) first.focus(); }
    };
    head.appendChild(addBtn);
    panel.appendChild(head);
    panel.appendChild(form);

    if (!rows.length) {
      panel.appendChild(el("div", "empty-list", "Nothing yet — tap “＋ " + ADD_SPECS[type].label + "”."));
    } else {
      const list = el("div", "record-list");
      rows.forEach((r) => list.appendChild(rowFn(r, type)));
      panel.appendChild(list);
    }
    container.innerHTML = "";
    container.appendChild(panel);
  }

  // row renderers
  function recordRow(opts) {
    const row = el("div", "record");
    const main = el("div", "main");
    main.appendChild(el("div", "title", opts.title));
    if (opts.meta) main.appendChild(el("div", "meta", opts.meta));
    if (opts.controls) main.appendChild(opts.controls);
    row.appendChild(main);
    if (opts.amount != null) {
      row.appendChild(el("div", "amount" + (opts.out ? " out" : ""), opts.amount));
    }
    if (opts.del) {
      const b = el("button", "del", "🗑");
      b.title = "Delete";
      b.onclick = () => removeRecord(opts.del.type, opts.del.id);
      row.appendChild(b);
    }
    return row;
  }

  // tap-to-update controls -------------------------------------------------
  const MS_STATES = [
    ["not_started", "To-do", "gray"],
    ["in_progress", "Active", "blue"],
    ["blocked", "Blocked", "red"],
    ["done", "Done", "green"],
  ];
  function milestoneControls(r) {
    const wrap = el("div", "stat-ctrl");
    MS_STATES.forEach(([val, label, color]) => {
      const on = r.status === val;
      const b = el("button", "sbtn" + (on ? " on " + color : ""), esc(label));
      if (!on) b.onclick = () => setMilestoneStatus(r.id, val);
      wrap.appendChild(b);
    });
    return wrap;
  }
  async function setMilestoneStatus(id, status) {
    try {
      await api(`/api/projects/${state.projectId}/milestones/${id}`,
        { method: "PATCH", body: JSON.stringify({ status }) });
      toast("Stage updated");
      await refreshDashboard();
    } catch (e) { toast(e.message); }
  }

  function issueControls(r) {
    const wrap = el("div", "stat-ctrl");
    if (r.status === "open") {
      const b = el("button", "sbtn on green", "✓ Mark resolved");
      b.onclick = () => setIssueResolved(r.id, true);
      wrap.appendChild(b);
    } else {
      const b = el("button", "sbtn", "↺ Reopen");
      b.onclick = () => setIssueResolved(r.id, false);
      wrap.appendChild(b);
    }
    return wrap;
  }
  async function setIssueResolved(id, resolve) {
    try {
      const resolution = resolve ? (prompt("How was it resolved? (optional)") || "") : "";
      await api(`/api/projects/${state.projectId}/issues/${id}`,
        { method: "PATCH", body: JSON.stringify({ status: resolve ? "resolved" : "open", resolution }) });
      toast(resolve ? "Issue resolved" : "Issue reopened");
      await refreshDashboard();
    } catch (e) { toast(e.message); }
  }

  const expenseRow = (r) => recordRow({
    title: `${esc(r.description || r.category || "Expense")} ${pill(r.payment_status)}`,
    meta: `${esc(r.category || "general")}${r.vendor ? " · " + esc(r.vendor) : ""} · ${dateStr(r.spent_on)}`,
    amount: money(r.amount), out: r.payment_status === "pending",
    del: { type: "expenses", id: r.id },
  });

  const paymentRow = (r) => recordRow({
    title: `${esc(r.artisan_name || "Payment")} ${pill(r.status)}`,
    meta: `${esc(r.description || "labour")} · ${dateStr(r.paid_on)}`,
    amount: money(r.amount), out: r.status === "pending",
    del: { type: "payments", id: r.id },
  });

  const milestoneRow = (r) => recordRow({
    title: `${esc(r.name)} ${pill(r.status)}`,
    meta: [
      r.description ? esc(r.description) : "",
      r.target_date ? "target " + dateStr(r.target_date) : "",
      r.completed_date ? "done " + dateStr(r.completed_date) : "",
    ].filter(Boolean).join(" · "),
    controls: milestoneControls(r),
    del: { type: "milestones", id: r.id },
  });

  const artisanRow = (r) => recordRow({
    title: `${esc(r.name)}${r.trade ? ' <span class="pill blue">' + esc(r.trade) + "</span>" : ""}`,
    meta: [
      r.phone ? esc(r.phone) : "",
      r.agreed_rate != null ? "rate " + money(r.agreed_rate) : "",
      "paid " + money(r.total_paid || 0),
      r.notes ? esc(r.notes) : "",
    ].filter(Boolean).join(" · "),
    del: { type: "artisans", id: r.id },
  });

  const issueRow = (r) => recordRow({
    title: `${esc(r.title)} ${pill(r.severity)} ${pill(r.status)}`,
    meta: [
      r.description ? esc(r.description) : "",
      "raised " + dateStr(r.raised_on),
      r.resolved_on ? "resolved " + dateStr(r.resolved_on) : "",
      r.resolution ? "→ " + esc(r.resolution) : "",
    ].filter(Boolean).join(" · "),
    controls: issueControls(r),
    del: { type: "issues", id: r.id },
  });

  const noteRow = (r) => recordRow({
    title: `${esc(r.title)} ${pill(r.category)}`,
    meta: r.content ? esc(r.content) : dateStr(r.created_at),
    del: { type: "notes", id: r.id },
  });

  // ----- overview ---------------------------------------------------------
  async function renderOverview(container, pid) {
    const [expenses, payments, milestones, issues] = await Promise.all([
      api(`/api/projects/${pid}/expenses`),
      api(`/api/projects/${pid}/payments`),
      api(`/api/projects/${pid}/milestones`),
      api(`/api/projects/${pid}/issues`),
    ]);
    container.innerHTML = "";

    const openIssues = issues.filter((i) => i.status === "open");
    const activeMs = milestones.filter((m) => m.status !== "done");

    container.appendChild(miniPanel("Active milestones",
      activeMs.slice(0, 5).map(milestoneRow),
      "No active milestones."));

    container.appendChild(miniPanel("Open issues",
      openIssues.slice(0, 5).map(issueRow),
      "No open issues. 🎉"));

    const activity = [
      ...expenses.map((e) => ({ ...e, _t: "expense", _d: e.spent_on })),
      ...payments.map((p) => ({ ...p, _t: "payment", _d: p.paid_on })),
    ].sort((a, b) => String(b._d).localeCompare(String(a._d))).slice(0, 6);

    container.appendChild(miniPanel("Recent spending",
      activity.map((a) => (a._t === "expense" ? expenseRow(a) : paymentRow(a))),
      "No expenses or payments logged yet."));
  }

  function miniPanel(title, rows, emptyMsg) {
    const panel = el("div", "panel");
    panel.appendChild(el("h3", null, esc(title)));
    if (!rows.length) {
      panel.appendChild(el("div", "empty-list", esc(emptyMsg)));
    } else {
      const list = el("div", "record-list");
      rows.forEach((r) => list.appendChild(r));
      panel.appendChild(list);
    }
    return panel;
  }

  async function removeRecord(type, id) {
    if (!confirm("Delete this record?")) return;
    try {
      await api(`/api/projects/${state.projectId}/${type}/${id}`, { method: "DELETE" });
      toast("Deleted");
      await refreshDashboard();
    } catch (e) {
      toast(e.message);
    }
  }

  // ----- chat -------------------------------------------------------------
  function resetChat() {
    const log = $("#chat-log");
    log.innerHTML = "";
    const greeting = state.aiEnabled
      ? "Hi! Tell me what's happening on site and I'll log it. Try:\n“Bought 50 bags of cement for 600, paid cash” or ask “How much have I spent so far?”"
      : "The assistant is offline — set ANTHROPIC_API_KEY on the server to enable it. You can still add, update and delete everything by hand using the ＋ Add buttons and the stage controls.";
    log.appendChild(msgNode(state.aiEnabled ? "bot" : "note", greeting));
    $("#chat-input").disabled = !state.aiEnabled;
    $("#chat-send").disabled = !state.aiEnabled;
  }

  function msgNode(kind, text, actions) {
    const m = el("div", "msg " + kind);
    m.appendChild(document.createTextNode(text));
    if (actions && actions.length) {
      const saved = actions.map((a) => a.saved).filter(Boolean);
      if (saved.length) {
        const counts = saved.reduce((acc, s) => ((acc[s] = (acc[s] || 0) + 1), acc), {});
        const label = Object.entries(counts)
          .map(([k, v]) => `${v} ${k}${v > 1 ? "s" : ""}`).join(", ");
        m.appendChild(el("div", "actions", "✓ saved " + label));
      }
    }
    return m;
  }

  async function sendChat(text) {
    const log = $("#chat-log");
    log.appendChild(msgNode("user", text));
    state.history.push({ role: "user", content: text });

    const typing = el("div", "typing", "Assistant is thinking…");
    log.appendChild(typing);
    log.scrollTop = log.scrollHeight;

    $("#chat-send").disabled = true;
    try {
      const res = await api(`/api/projects/${state.projectId}/chat`, {
        method: "POST",
        body: JSON.stringify({ message: text, history: state.history.slice(0, -1) }),
      });
      typing.remove();
      log.appendChild(msgNode("bot", res.reply, res.actions));
      state.history.push({ role: "assistant", content: res.reply });
      if (res.actions && res.actions.length) {
        await refreshDashboard();
      }
    } catch (e) {
      typing.remove();
      log.appendChild(msgNode("note", "⚠ " + e.message));
    } finally {
      $("#chat-send").disabled = false;
      log.scrollTop = log.scrollHeight;
    }
  }

  // ----- modal ------------------------------------------------------------
  function openModal() {
    $("#project-form").reset();
    $("#project-modal").classList.remove("hidden");
    $('#project-form [name="name"]').focus();
  }
  function closeModal() { $("#project-modal").classList.add("hidden"); }

  async function submitProject(e) {
    e.preventDefault();
    const f = e.target;
    const body = {
      name: f.name.value.trim(),
      budget: parseFloat(f.budget.value) || 0,
      currency: f.currency.value.trim() || "$",
      location: f.location.value.trim(),
      description: f.description.value.trim(),
      start_date: f.start_date.value || null,
      target_end_date: f.target_end_date.value || null,
    };
    if (!body.name) return;
    try {
      const proj = await api("/api/projects", { method: "POST", body: JSON.stringify(body) });
      closeModal();
      state.projectId = proj.id;
      await loadProjects();
      $("#project-select").value = proj.id;
      toast("Project created");
    } catch (err) {
      toast(err.message);
    }
  }

  // ----- events -----------------------------------------------------------
  function wireEvents() {
    $("#project-select").addEventListener("change", (e) => selectProject(e.target.value));
    $("#new-project-btn").addEventListener("click", openModal);
    $("#empty-create-btn").addEventListener("click", openModal);
    $("#modal-cancel").addEventListener("click", closeModal);
    $("#project-form").addEventListener("submit", submitProject);
    $("#project-modal").addEventListener("click", (e) => {
      if (e.target.id === "project-modal") closeModal();
    });

    document.querySelectorAll(".tab").forEach((t) =>
      t.addEventListener("click", () => renderTab(t.dataset.tab)));

    const form = $("#chat-form");
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const inp = $("#chat-input");
      const text = inp.value.trim();
      if (!text) return;
      inp.value = "";
      sendChat(text);
    });
    $("#chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        form.requestSubmit();
      }
    });

    // mobile assistant toggle
    $("#assistant-fab").addEventListener("click", () => $("#assistant").classList.add("open"));
    $("#assistant-close").addEventListener("click", () => $("#assistant").classList.remove("open"));
    window.addEventListener("resize", () => {
      const fab = $("#assistant-fab");
      if (window.innerWidth <= 900 && state.projects.length) fab.classList.remove("hidden");
      else { fab.classList.add("hidden"); $("#assistant").classList.remove("open"); }
    });
  }

  boot();
})();
