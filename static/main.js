const form = document.getElementById("uform");
const msgEl = document.getElementById("msg");
const summaryEl = document.getElementById("summary");
const previewEl = document.getElementById("preview");
let chart;

function setMsg(text) { msgEl.textContent = text || ""; }

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  setMsg("Uploading and parsing CSV…");

  try {
    const fd = new FormData(form);
    const res = await fetch("/upload", { method: "POST", body: fd });
    const json = await res.json();

    if (!res.ok || json.error) throw new Error(json.error || `HTTP ${res.status}`);

    const { summary, preview } = json;
    summaryEl.textContent = JSON.stringify(summary, null, 2);
    previewEl.textContent = JSON.stringify(preview, null, 2);

    const ns = summary.numericSummary;
    if (ns && preview.length) {
      const col = ns.column;
      const labels = preview.map((_, i) => i + 1);
      const data = preview.map(row => {
        const raw = row[col];
        if (raw == null) return 0;
        if (typeof raw === "number") return raw;
        const cleaned = String(raw).replace(/[^\d.\-]/g, "");
        const num = parseFloat(cleaned);
        return Number.isFinite(num) ? num : 0;
      });

      const ctx = document.getElementById("chart").getContext("2d");
      if (chart) chart.destroy();
      chart = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets: [{ label: col, data }] },
        options: { responsive: true, plugins: { legend: { display: true } } }
      });
      setMsg("");
    } else {
      if (chart) chart.destroy();
      setMsg("No numeric columns detected — chart not shown. Try a CSV with numbers.");
    }
  } catch (err) {
    console.error(err);
    if (chart) chart.destroy();
    setMsg(`Error: ${err.message}`);
  }
});
