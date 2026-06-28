const API = "/api";

const state = {
  experiences: [],
  resumes: [],
  jobs: [],
  settings: null,
  statusLabels: {},
};

const panels = ["dashboard", "experiences", "resumes", "jobs", "ai", "settings"];

function $(id) {
  return document.getElementById(id);
}

function showToast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2000);
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

function switchPanel(name) {
  panels.forEach((p) => {
    $(`panel-${p}`)?.classList.toggle("active", p === name);
    document.querySelector(`[data-panel="${p}"]`)?.classList.toggle("active", p === name);
  });
}

async function loadAll() {
  const [experiences, resumes, jobs, settings, statesConfig] = await Promise.all([
    api("/experiences"),
    api("/resumes"),
    api("/jobs"),
    api("/settings"),
    api("/states"),
  ]);
  state.experiences = experiences;
  state.resumes = resumes;
  state.jobs = jobs;
  state.settings = settings;
  state.statusLabels = Object.fromEntries(
    (statesConfig.states || []).map((s) => [s.id, s.label])
  );
  renderDashboard();
  renderExperiences();
  renderResumes();
  renderJobs();
  renderAiSelectors();
  renderSettings();
}

function renderDashboard() {
  const pending = state.jobs.filter((j) => j.status === "pending").length;
  $("stat-pending").textContent = pending;
  $("stat-experiences").textContent = state.experiences.length;
  $("stat-resumes").textContent = state.resumes.length;
}

function renderExperiences() {
  const list = $("experience-list");
  if (!state.experiences.length) {
    list.innerHTML = '<p class="empty">暂无经历，点击下方添加</p>';
    return;
  }
  list.innerHTML = state.experiences
    .map(
      (e) => `
    <div class="list-item">
      <div>
        <h3>${escapeHtml(e.title)}</h3>
        <div class="meta">${e.category} · ${(e.tags || []).map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>
        <p>${escapeHtml((e.content || "").slice(0, 120))}${e.content?.length > 120 ? "…" : ""}</p>
      </div>
      <button class="btn btn-secondary" data-del-exp="${e.id}">删除</button>
    </div>`
    )
    .join("");
  list.querySelectorAll("[data-del-exp]").forEach((btn) => {
    btn.onclick = async () => {
      await api(`/experiences/${btn.dataset.delExp}`, { method: "DELETE" });
      showToast("已删除");
      loadAll();
    };
  });
}

function renderResumes() {
  const list = $("resume-list");
  if (!state.resumes.length) {
    list.innerHTML = '<p class="empty">暂无简历版本</p>';
    return;
  }
  list.innerHTML = state.resumes
    .map(
      (r) => `
    <div class="list-item">
      <div>
        <h3>${escapeHtml(r.name)} ${r.is_default ? '<span class="tag">默认</span>' : ""}</h3>
        <div class="meta">${escapeHtml(r.description || "")}</div>
      </div>
    </div>`
    )
    .join("");
}

function renderJobs() {
  const list = $("job-list");
  if (!state.jobs.length) {
    list.innerHTML = '<p class="empty">暂无岗位，录入 JD 开始投递</p>';
    return;
  }
  list.innerHTML = state.jobs
    .map(
      (j) => `
    <div class="list-item">
      <div>
        <h3>${escapeHtml(j.company)} — ${escapeHtml(j.position)}</h3>
        <div class="meta">
          <span class="status-badge">${state.statusLabels[j.status] || j.status}</span>
          · ${j.source}
        </div>
      </div>
      <button class="btn btn-secondary" data-del-job="${j.id}">删除</button>
    </div>`
    )
    .join("");
  list.querySelectorAll("[data-del-job]").forEach((btn) => {
    btn.onclick = async () => {
      await api(`/jobs/${btn.dataset.delJob}`, { method: "DELETE" });
      showToast("已删除");
      loadAll();
    };
  });
}

function renderAiSelectors() {
  const resumeSelect = $("ai-resume");
  resumeSelect.innerHTML = state.resumes
    .map((r) => `<option value="${r.id}">${escapeHtml(r.name)}</option>`)
    .join("");
  const defaultId = state.settings?.default_resume_id;
  if (defaultId) resumeSelect.value = defaultId;

  const jobSelect = $("ai-job");
  jobSelect.innerHTML =
    '<option value="">手动粘贴 JD</option>' +
    state.jobs
      .map(
        (j) =>
          `<option value="${j.id}">${escapeHtml(j.company)} - ${escapeHtml(j.position)}</option>`
      )
      .join("");
}

function renderSettings() {
  $("settings-key-status").textContent = state.settings?.deepseek_api_key_set
    ? "已配置"
    : "未配置";
  $("settings-model").value = state.settings?.deepseek_model || "deepseek-chat";
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatMatchResult(result) {
  const rec = result.recommendation || "";
  const lines = [
    `分数: ${result.score ?? "—"}`,
    `建议: ${rec} — ${result.recommendation_message || ""}`,
    "",
    result.summary || "",
    "",
  ];
  const blocks = result.blocks || {};
  const titles = {
    a_role_summary: "A. 岗位要求",
    b_cv_match: "B. 简历匹配",
    c_level_fit: "C. 职级匹配",
    d_key_gaps: "D. 主要差距",
    e_personalization: "E. 定制方向",
    f_interview_angles: "F. 面试角度",
  };
  for (const [key, title] of Object.entries(titles)) {
    if (blocks[key]) lines.push(`${title}\n${blocks[key]}\n`);
  }
  if (result.gaps?.length) lines.push("差距:\n- " + result.gaps.join("\n- "));
  if (result.suggestions?.length) lines.push("\n建议:\n- " + result.suggestions.join("\n- "));
  $("output-match").textContent = lines.join("\n");
  return rec;
}

function getAiPayload(extra = {}) {
  const resumeId = $("ai-resume").value;
  if (!resumeId) throw new Error("请先创建简历");
  return {
    resume_id: resumeId,
    job_id: $("ai-job").value || null,
    jd_text: $("ai-jd").value,
    ...extra,
  };
}

document.querySelectorAll("[data-panel]").forEach((btn) => {
  btn.onclick = () => switchPanel(btn.dataset.panel);
});

$("form-experience").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await api("/experiences", {
    method: "POST",
    body: JSON.stringify({
      title: fd.get("title"),
      category: fd.get("category"),
      content: fd.get("content"),
      tags: String(fd.get("tags") || "")
        .split(/[,，]/)
        .map((s) => s.trim())
        .filter(Boolean),
      bullets: [],
    }),
  });
  e.target.reset();
  showToast("经历已保存");
  loadAll();
};

$("form-resume").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await api("/resumes", {
    method: "POST",
    body: JSON.stringify({
      name: fd.get("name"),
      description: fd.get("description"),
      content: fd.get("content"),
      is_default: fd.get("is_default") === "on",
      experience_ids: [],
    }),
  });
  e.target.reset();
  showToast("简历已保存");
  loadAll();
};

$("form-job").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await api("/jobs", {
    method: "POST",
    body: JSON.stringify({
      company: fd.get("company"),
      position: fd.get("position"),
      jd_text: fd.get("jd_text"),
      source: fd.get("source"),
      status: "pending",
      notes: fd.get("notes") || "",
    }),
  });
  e.target.reset();
  showToast("岗位已保存");
  loadAll();
};

$("form-settings").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const key = fd.get("api_key");
  const body = { deepseek_model: fd.get("model") };
  if (key) body.deepseek_api_key = key;
  await api("/settings", { method: "PUT", body: JSON.stringify(body) });
  showToast("设置已保存");
  loadAll();
};

async function runAi(endpoint, outputId, extra = {}) {
  let body;
  try {
    body = getAiPayload(extra);
  } catch (err) {
    showToast(err.message);
    return;
  }
  const out = $(outputId);
  out.textContent = "生成中…";
  try {
    const result = await api(endpoint, { method: "POST", body: JSON.stringify(body) });
    if (endpoint === "/ai/match") {
      const rec = formatMatchResult(result);
      if (rec === "skip") showToast("匹配度较低，不建议深度定制");
    } else if (result.greeting) {
      out.textContent = result.greeting;
    } else {
      out.textContent = JSON.stringify(result, null, 2);
    }
  } catch (err) {
    out.textContent = `错误: ${err.message}`;
  }
}

$("btn-match").onclick = () => runAi("/ai/match", "output-match");
$("btn-tune").onclick = () => runAi("/ai/tune-resume", "output-tune");
$("btn-boss").onclick = () => runAi("/ai/boss-greeting", "output-boss");
$("btn-email").onclick = () =>
  runAi("/ai/email-draft", "output-email", {
    recipient_name: $("ai-recipient").value || null,
  });

$("btn-pipeline").onclick = async () => {
  let body;
  try {
    body = getAiPayload({
      channel: $("ai-channel").value,
      include_tune: $("ai-include-tune").checked,
      recipient_name: $("ai-recipient").value || null,
    });
  } catch (err) {
    showToast(err.message);
    return;
  }
  $("output-match").textContent = "流水线运行中…";
  $("output-tune").textContent = "—";
  $("output-boss").textContent = "—";
  $("output-email").textContent = "—";
  try {
    const result = await api("/ai/auto-pipeline", {
      method: "POST",
      body: JSON.stringify(body),
    });
    formatMatchResult(result.match);
    $("output-tune").textContent = result.tune
      ? JSON.stringify(result.tune, null, 2)
      : "（匹配分不足或未启用微调）";
    if (result.channel === "boss" && result.output?.greeting) {
      $("output-boss").textContent = result.output.greeting;
    } else if (result.channel === "email") {
      $("output-email").textContent = JSON.stringify(result.output, null, 2);
    }
    if (result.report_path) showToast(`报告已保存: ${result.report_path}`);
    if (result.match?.recommendation === "skip") {
      showToast("匹配度较低，已生成报告但不建议深度定制");
    }
  } catch (err) {
    $("output-match").textContent = `错误: ${err.message}`;
  }
};

document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.onclick = () => {
    const text = $(btn.dataset.copy).textContent;
    navigator.clipboard.writeText(text).then(() => showToast("已复制"));
  };
});

$("ai-job").onchange = () => {
  const job = state.jobs.find((j) => j.id === $("ai-job").value);
  if (job) {
    $("ai-jd").value = job.jd_text;
    if (job.source === "email") $("ai-channel").value = "email";
    if (job.source === "boss") $("ai-channel").value = "boss";
  }
};

loadAll().catch((err) => showToast(`加载失败: ${err.message}`));
