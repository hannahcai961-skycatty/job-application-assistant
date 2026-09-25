const API = "/api";

const CHANNELS = [
  ["fair", "招聘会"],
  ["official", "官网"],
  ["platform", "求职平台"],
];
const CHANNEL_LABELS = Object.fromEntries(CHANNELS);

const state = {
  jobs: [],
  settings: null,
  statusLabels: {},
  lastMatch: null,
};

const panels = ["dashboard", "evaluate", "tracker", "ai", "settings"];

function $(id) {
  return document.getElementById(id);
}

function showToast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2200);
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    throw new Error(typeof detail === "string" ? detail : res.statusText);
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

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function loadAll() {
  const [jobs, settings, statesConfig] = await Promise.all([
    api("/jobs"),
    api("/settings"),
    api("/states"),
  ]);
  state.jobs = jobs;
  state.settings = settings;
  state.statusLabels = Object.fromEntries(
    (statesConfig.states || []).map((s) => [s.id, s.label])
  );
  renderDashboard();
  renderTracker();
  renderAiJobSelect();
  renderSettings();
}

function renderDashboard() {
  const counts = {};
  for (const j of state.jobs) counts[j.status] = (counts[j.status] || 0) + 1;
  const cards = [
    ["全部", state.jobs.length],
    ...Object.entries(state.statusLabels).map(([id, label]) => [label, counts[id] || 0]),
  ];
  const scored = state.jobs.filter((j) => j.match_score != null);
  $("stat-cards").innerHTML = cards
    .map(
      ([label, num]) =>
        `<div class="stat"><p class="num">${num}</p><p class="label">${escapeHtml(label)}</p></div>`
    )
    .join("");

  const host = $("dash-jobs");
  if (!state.jobs.length) {
    host.innerHTML = '<p class="empty">还没有投递记录。去「岗位评估」OCR 后写入，或在「投递表」新增一行。</p>';
    return;
  }
  const rows = [...state.jobs].reverse();
  host.innerHTML = `
    <div class="table-wrap"><table class="sheet">
      <thead><tr>
        <th>公司</th><th class="col-position">岗位</th><th class="col-status">状态</th><th>渠道</th><th>投递日</th><th>面试</th><th>分数</th><th>备注</th>
      </tr></thead>
      <tbody>${rows
        .map(
          (j) => `<tr>
            <td>${escapeHtml(j.company)}</td>
            <td class="col-position">${escapeHtml(j.position)}</td>
            <td class="col-status">${escapeHtml(state.statusLabels[j.status] || j.status)}</td>
            <td>${escapeHtml(CHANNEL_LABELS[j.source] || j.source)}</td>
            <td>${escapeHtml(j.applied_at)}</td>
            <td>${escapeHtml(j.interview_round)}</td>
            <td>${j.match_score ?? "—"}</td>
            <td>${escapeHtml(j.notes)}</td>
          </tr>`
        )
        .join("")}</tbody>
    </table></div>
    <p class="preview" style="margin-top:0.75rem">已评估 ${scored.length} / ${state.jobs.length}</p>`;
}

function statusOptions(current) {
  return Object.entries(state.statusLabels)
    .map(
      ([id, label]) =>
        `<option value="${id}" ${id === current ? "selected" : ""}>${escapeHtml(label)}</option>`
    )
    .join("");
}

function channelOptions(current) {
  const known = new Set(CHANNELS.map(([id]) => id));
  const value = known.has(current) ? current : "platform";
  return CHANNELS.map(
    ([id, label]) =>
      `<option value="${id}" ${id === value ? "selected" : ""}>${label}</option>`
  ).join("");
}

function renderTracker() {
  const body = $("tracker-body");
  if (!state.jobs.length) {
    body.innerHTML = `<tr><td colspan="9" class="empty">暂无记录</td></tr>`;
    return;
  }
  body.innerHTML = state.jobs
    .map(
      (j) => `<tr data-id="${j.id}">
        <td><input data-f="company" value="${escapeHtml(j.company)}" /></td>
        <td class="col-position"><textarea data-f="position" rows="2">${escapeHtml(j.position)}</textarea></td>
        <td><select data-f="source">${channelOptions(j.source)}</select></td>
        <td class="col-status"><select data-f="status">${statusOptions(j.status)}</select></td>
        <td><input data-f="applied_at" type="date" value="${escapeHtml(j.applied_at)}" /></td>
        <td><input data-f="interview_round" value="${escapeHtml(j.interview_round)}" /></td>
        <td><textarea data-f="notes">${escapeHtml(j.notes)}</textarea></td>
        <td>${j.match_score ?? "—"}</td>
        <td>
          <button class="btn btn-secondary" data-save="${j.id}" type="button">保存</button>
          <button class="btn btn-secondary" data-del="${j.id}" type="button">删除</button>
        </td>
      </tr>`
    )
    .join("");

  body.querySelectorAll("[data-save]").forEach((btn) => {
    btn.onclick = () => saveRow(btn.dataset.save);
  });
  body.querySelectorAll("[data-del]").forEach((btn) => {
    btn.onclick = async () => {
      await api(`/jobs/${btn.dataset.del}`, { method: "DELETE" });
      showToast("已删除");
      loadAll();
    };
  });
}

function rowPayload(id) {
  const job = state.jobs.find((j) => j.id === id);
  const tr = document.querySelector(`#tracker-body tr[data-id="${id}"]`);
  const get = (name) => tr.querySelector(`[data-f="${name}"]`)?.value ?? "";
  return {
    company: get("company"),
    position: get("position"),
    source: get("source") || job.source,
    status: get("status") || job.status,
    applied_at: get("applied_at"),
    interview_round: get("interview_round"),
    notes: get("notes"),
    jd_text: job.jd_text || "",
    url: job.url || "",
    match_score: job.match_score,
    match_reason: job.match_reason || "",
  };
}

async function saveRow(id) {
  await api(`/jobs/${id}`, {
    method: "PUT",
    body: JSON.stringify(rowPayload(id)),
  });
  showToast("已保存");
  loadAll();
}

function renderAiJobSelect() {
  const sel = $("ai-job");
  const current = sel.value;
  sel.innerHTML =
    '<option value="">不从投递表读取</option>' +
    state.jobs
      .map(
        (j) =>
          `<option value="${j.id}">${escapeHtml(j.company || "未命名")} - ${escapeHtml(j.position || "岗位")}${j.jd_text ? "" : "（无JD）"}</option>`
      )
      .join("");
  if (current) sel.value = current;
}

function renderSettings() {
  $("settings-key-status").textContent = state.settings?.deepseek_api_key_set
    ? "已配置"
    : "未配置";
  $("settings-model").value = state.settings?.deepseek_model || "qwen-plus";
  $("settings-base-url").value =
    state.settings?.deepseek_base_url || "https://dashscope.aliyuncs.com/compatible-mode/v1";
  const profiles = state.settings?.profiles || [];

  const list = $("profile-list");
  if (!profiles.length) {
    list.innerHTML = '<p class="empty">暂无材料</p>';
    return;
  }
  list.innerHTML = profiles
    .map(
      (p) => `<div class="list-item" data-profile="${p.id}">
        <div style="flex:1">
          <label>主题</label>
          <input data-topic="${p.id}" value="${escapeHtml(p.topic)}" />
        </div>
        <div style="display:flex;flex-direction:column;gap:0.35rem">
          <button class="btn btn-secondary" data-save-topic="${p.id}" type="button">保存主题</button>
          <button class="btn btn-secondary" data-del-profile="${p.id}" type="button">删除</button>
        </div>
      </div>`
    )
    .join("");

  list.querySelectorAll("[data-save-topic]").forEach((btn) => {
    btn.onclick = async () => {
      const topic = list.querySelector(`[data-topic="${btn.dataset.saveTopic}"]`)?.value?.trim();
      if (!topic) return showToast("主题不能为空");
      state.settings = await api(`/profiles/${btn.dataset.saveTopic}`, {
        method: "PUT",
        body: JSON.stringify({ topic }),
      });
      renderSettings();
      showToast("主题已更新");
    };
  });
  list.querySelectorAll("[data-del-profile]").forEach((btn) => {
    btn.onclick = async () => {
      state.settings = await api(`/profiles/${btn.dataset.delProfile}`, { method: "DELETE" });
      renderSettings();
      showToast("已删除");
    };
  });
}

function applyOcr(data, { jdId, companyId, positionId, urlId }) {
  if (jdId && data.jd_text) $(jdId).value = data.jd_text;
  if (companyId && data.company) $(companyId).value = data.company;
  if (positionId && data.position) $(positionId).value = data.position;
  if (urlId && data.url) $(urlId).value = data.url;
  if (!data.jd_text && data.raw_text && jdId) $(jdId).value = data.raw_text;
}

async function uploadOcr(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API}/ingest/ocr`, { method: "POST", body: fd });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

document.querySelectorAll("[data-panel]").forEach((btn) => {
  btn.onclick = () => switchPanel(btn.dataset.panel);
});

async function runEvalOcr(file) {
  showToast("识别中…");
  try {
    const data = await uploadOcr(file);
    applyOcr(data, {
      jdId: "eval-jd",
      companyId: "eval-company",
      positionId: "eval-position",
      urlId: "eval-url",
    });
    showToast("识别完成，请核对后评估");
  } catch (err) {
    showToast(err.message);
  }
}

function fileFromClipboard(event) {
  const items = event.clipboardData?.items;
  if (!items) return null;
  for (const item of items) {
    if (item.type.startsWith("image/")) return item.getAsFile();
  }
  return null;
}

function bindImagePaste(zoneId, onFile) {
  $(zoneId).addEventListener("paste", (event) => {
    const file = fileFromClipboard(event);
    if (!file) {
      showToast("剪贴板里没有图片");
      return;
    }
    event.preventDefault();
    onFile(file);
  });
}

$("btn-eval-ocr").onclick = async () => {
  const file = $("eval-file").files?.[0];
  if (!file) return showToast("请先选择图片，或在下方虚线框按 Ctrl+V");
  runEvalOcr(file);
};

bindImagePaste("eval-paste", runEvalOcr);

$("btn-eval-match").onclick = async () => {
  const jd = $("eval-jd").value.trim();
  if (!jd) return showToast("请先 OCR 或填写岗位要求");
  $("eval-output").textContent = "评估中…";
  try {
    const result = await api("/ai/match", {
      method: "POST",
      body: JSON.stringify({ jd_text: jd }),
    });
    state.lastMatch = result;
    const brief = result.summary || result.reason || "";
    const detail = result.reason && result.reason !== result.summary ? `\n${result.reason}` : "";
    $("eval-output").textContent = `分数：${result.score ?? "—"}\n\n${brief}${detail}`;
  } catch (err) {
    $("eval-output").textContent = `错误：${err.message}`;
  }
};

$("btn-eval-save").onclick = async () => {
  const company = $("eval-company").value.trim();
  const position = $("eval-position").value.trim();
  if (!company && !position) return showToast("至少填写公司或岗位");
  const reason =
    state.lastMatch?.summary || state.lastMatch?.reason || "";
  await api("/jobs", {
    method: "POST",
    body: JSON.stringify({
      company,
      position,
      url: $("eval-url").value.trim(),
      jd_text: $("eval-jd").value,
      source: "platform",
      status: "pending",
      match_score: state.lastMatch?.score ?? null,
      match_reason: reason,
      notes: reason,
    }),
  });
  showToast("已写入投递表");
  await loadAll();
  switchPanel("tracker");
};

$("btn-add-job").onclick = async () => {
  await api("/jobs", {
    method: "POST",
    body: JSON.stringify({
      company: "",
      position: "",
      status: "pending",
      source: "platform",
    }),
  });
  await loadAll();
  switchPanel("tracker");
};

$("ai-job").onchange = () => {
  const job = state.jobs.find((j) => j.id === $("ai-job").value);
  if (job) $("ai-jd").value = job.jd_text || "";
};

async function runAiOcr(file) {
  showToast("识别中…");
  try {
    const data = await uploadOcr(file);
    applyOcr(data, { jdId: "ai-jd" });
    showToast("已填入 JD");
  } catch (err) {
    showToast(err.message);
  }
}

$("btn-ai-ocr").onclick = async () => {
  const file = $("ai-file").files?.[0];
  if (!file) return showToast("请先选择图片，或在下方虚线框按 Ctrl+V");
  runAiOcr(file);
};

bindImagePaste("ai-paste", runAiOcr);

$("btn-email").onclick = async () => {
  $("output-email").textContent = "生成中…";
  try {
    const result = await api("/ai/email-draft", {
      method: "POST",
      body: JSON.stringify({
        job_id: $("ai-job").value || null,
        jd_text: $("ai-jd").value,
        recipient_name: $("ai-recipient").value || null,
      }),
    });
    const attachments = (result.attachments || []).map((a) => `- ${a}`).join("\n");
    $("output-email").textContent = [
      `主题：${result.subject || ""}`,
      "",
      result.body || "",
      attachments ? `\n附件建议：\n${attachments}` : "",
    ].join("\n");
  } catch (err) {
    $("output-email").textContent = `错误：${err.message}`;
  }
};

$("form-settings").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const key = fd.get("api_key");
  const body = {
    deepseek_model: fd.get("model"),
    deepseek_base_url: fd.get("base_url"),
  };
  if (key) body.deepseek_api_key = key;
  await api("/settings", { method: "PUT", body: JSON.stringify(body) });
  e.target.querySelector('[name="api_key"]').value = "";
  showToast("设置已保存");
  loadAll();
};

$("btn-profile").onclick = async () => {
  const input = $("profile-file");
  const files = [...(input.files || [])];
  if (!files.length) return showToast("请先选择至少一个文档");
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  fd.append("topic", $("profile-topic").value.trim());
  showToast(`正在读取 ${files.length} 份文档…`);
  try {
    const res = await fetch(`${API}/profiles/upload`, { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    state.settings = await res.json();
    input.value = "";
    $("profile-topic").value = "";
    renderSettings();
    showToast(`已上传 ${files.length} 份，主题已区分`);
  } catch (err) {
    showToast(err.message);
  }
};

document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.onclick = () => {
    const text = $(btn.dataset.copy).textContent;
    navigator.clipboard.writeText(text).then(() => showToast("已复制"));
  };
});

loadAll().catch((err) => showToast(`加载失败: ${err.message}`));
