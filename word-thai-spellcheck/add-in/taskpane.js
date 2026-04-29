/* taskpane.js — Thai Spell Checker Logic */

const API_BASE = "http://localhost:8000";

let currentErrors = [];

// --- Office.js Ready ---
Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    document.getElementById("btn-check").onclick = checkDocument;
    document.getElementById("btn-clear").onclick = clearHighlights;
    checkServerHealth();
  }
});

// --- Health Check ---
async function checkServerHealth() {
  const statusBar = document.getElementById("status-bar");
  const statusText = document.getElementById("status-text");
  const btnCheck = document.getElementById("btn-check");
  const btnClear = document.getElementById("btn-clear");

  try {
    const resp = await fetch(`${API_BASE}/health`);
    const data = await resp.json();

    if (data.ollama) {
      statusBar.className = "status-bar status-ok";
      statusText.textContent = `Ollama · ${data.model}`;
      btnCheck.disabled = false;
      btnClear.disabled = false;
    } else {
      statusBar.className = "status-bar status-error";
      statusText.textContent = "Ollama ไม่ได้รัน";
    }
  } catch (err) {
    statusBar.className = "status-bar status-error";
    statusText.textContent = "ไม่สามารถเชื่อมต่อ server";
  }
}

// --- Check Document ---
async function checkDocument() {
  const btnCheck = document.getElementById("btn-check");
  const progressContainer = document.getElementById("progress-container");
  const progressText = document.getElementById("progress-text");
  const resultDiv = document.getElementById("result");
  const errorList = document.getElementById("error-list");

  btnCheck.disabled = true;
  progressContainer.classList.remove("hidden");
  progressText.textContent = "กำลังดึงข้อความจากเอกสาร...";
  resultDiv.classList.add("hidden");
  errorList.innerHTML = "";

  try {
    await Word.run(async (context) => {
      // ดึง text จาก document
      const body = context.document.body;
      body.load("text");
      await context.sync();

      const text = body.text;

      if (!text.trim()) {
        showResult("เอกสารว่างเปล่า", "clean");
        return;
      }

      progressText.textContent = "กำลังส่งข้อความไปตรวจสอบ...";

      // ส่งไป server
      const resp = await fetch(`${API_BASE}/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      if (!resp.ok) {
        throw new Error(`Server error: ${resp.status}`);
      }

      const data = await resp.json();
      currentErrors = data.errors;

      progressText.textContent = "กำลัง highlight คำผิด...";

      // Highlight คำผิดใน Word
      if (currentErrors.length > 0) {
        await highlightErrors(context, currentErrors);
      }

      // แสดงผลลัพธ์
      const timeText = `(ใช้เวลา ${data.time_seconds} วินาที)`;
      if (currentErrors.length === 0) {
        showResult(`✅ ไม่พบคำผิด ${timeText}`, "clean");
      } else {
        showResult(`⚠️ พบ ${currentErrors.length} คำที่ควรตรวจสอบ ${timeText}`, "found");
        displayErrorList(currentErrors);
      }
    });
  } catch (err) {
    showResult(`❌ เกิดข้อผิดพลาด: ${err.message}`, "found");
  } finally {
    progressContainer.classList.add("hidden");
    btnCheck.disabled = false;
  }
}

// --- Highlight Errors in Word ---
async function highlightErrors(context, errors) {
  for (const error of errors) {
    const searchResults = context.document.body.search(error.word, {
      matchCase: true,
      matchWholeWord: false
    });
    searchResults.load("items");
    await context.sync();

    // Highlight ทุก occurrence (ระวัง: อาจ highlight คำซ้ำที่ไม่ผิด)
    for (const item of searchResults.items) {
      item.font.highlightColor = "#FF6B6B";
    }
    await context.sync();
  }
}

// --- Clear Highlights ---
async function clearHighlights() {
  try {
    await Word.run(async (context) => {
      const body = context.document.body;
      body.font.highlightColor = null;
      await context.sync();
    });

    currentErrors = [];
    document.getElementById("result").classList.add("hidden");
    document.getElementById("error-list").innerHTML = "";
  } catch (err) {
    alert(`เกิดข้อผิดพลาด: ${err.message}`);
  }
}

// --- Display Result ---
function showResult(message, type) {
  const resultDiv = document.getElementById("result");
  resultDiv.textContent = message;
  resultDiv.className = `result result-${type}`;
  resultDiv.classList.remove("hidden");
}

// --- Display Error List ---
function displayErrorList(errors) {
  const errorList = document.getElementById("error-list");
  errorList.innerHTML = "";

  errors.forEach((err) => {
    const item = document.createElement("div");
    item.className = "error-item";

    const typeLabel = {
      thai: "ไทย",
      english: "อังกฤษ",
      transliteration: "ทับศัพท์"
    }[err.type] || "อื่นๆ";

    item.innerHTML = `
      <div>
        <span class="error-word">${escapeHtml(err.word)}</span>
        <span class="error-arrow">→</span>
        <span class="error-suggestion">${escapeHtml(err.suggestion)}</span>
        <span class="error-type type-${err.type}">${typeLabel}</span>
      </div>
      <div class="error-sentence">${escapeHtml(err.sentence)}</div>
    `;

    errorList.appendChild(item);
  });
}

// --- Utility ---
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
