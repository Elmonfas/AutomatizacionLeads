"""Flask dashboard for browsing and filtering leads."""

import json
from pathlib import Path
from flask import Flask, jsonify, render_template_string, request

DATA_PATH = Path(__file__).parent / "leads_data.json"
CONFIG_PATH = Path(__file__).parent / "config.json"

TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prospector — Leads</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f1117; color: #e2e8f0; min-height: 100vh; }

  header { background: #1a1d2e; border-bottom: 1px solid #2d3148;
           padding: 16px 24px; display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 1.2rem; font-weight: 700; color: #7c83ff; }
  .badge { background: #2d3148; border-radius: 20px; padding: 4px 12px;
           font-size: 0.75rem; color: #94a3b8; }
  .badge span { color: #7c83ff; font-weight: 700; }

  .toolbar { padding: 16px 24px; display: flex; gap: 12px; flex-wrap: wrap;
             align-items: center; background: #13151f; border-bottom: 1px solid #1e2235; }
  .toolbar input, .toolbar select {
    background: #1a1d2e; border: 1px solid #2d3148; color: #e2e8f0;
    border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; outline: none; }
  .toolbar input { width: 260px; }
  .toolbar input:focus, .toolbar select:focus { border-color: #7c83ff; }
  .chip { background: #1a1d2e; border: 1px solid #2d3148; border-radius: 20px;
          padding: 6px 14px; font-size: 0.8rem; cursor: pointer; color: #94a3b8;
          transition: all .15s; }
  .chip:hover, .chip.active { background: #7c83ff; border-color: #7c83ff; color: #fff; }
  .run-btn { margin-left: auto; background: #7c83ff; color: #fff; border: none;
             border-radius: 8px; padding: 8px 18px; font-size: 0.85rem; font-weight: 600;
             cursor: pointer; display: flex; align-items: center; gap: 6px; transition: .15s; }
  .run-btn:hover { background: #636adf; }
  .run-btn:disabled { opacity: .5; cursor: not-allowed; }

  .stats { display: flex; gap: 12px; padding: 16px 24px; flex-wrap: wrap; }
  .stat { background: #1a1d2e; border: 1px solid #2d3148; border-radius: 10px;
          padding: 12px 20px; flex: 1; min-width: 130px; }
  .stat .num { font-size: 1.8rem; font-weight: 700; color: #7c83ff; }
  .stat .lbl { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
          gap: 14px; padding: 0 24px 24px; }

  .card { background: #1a1d2e; border: 1px solid #2d3148; border-radius: 12px;
          padding: 16px; display: flex; flex-direction: column; gap: 10px;
          transition: border-color .15s; }
  .card:hover { border-color: #7c83ff44; }

  .card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
  .card-name { font-weight: 700; font-size: 1rem; color: #f1f5f9; line-height: 1.3; }
  .score-badge { flex-shrink: 0; width: 38px; height: 38px; border-radius: 50%;
                 display: flex; align-items: center; justify-content: center;
                 font-weight: 800; font-size: 0.95rem; }

  .contact-row { display: flex; flex-direction: column; gap: 6px; margin: 2px 0; }
  .contact-item { display: flex; align-items: center; gap: 8px; }
  .contact-icon { width: 28px; height: 28px; border-radius: 7px; display: flex;
                  align-items: center; justify-content: center; font-size: 0.85rem;
                  flex-shrink: 0; }
  .icon-phone { background: #0d2e1a; }
  .icon-email { background: #1a1d40; }
  .icon-web   { background: #1a2535; }
  .contact-value { font-size: 0.82rem; font-weight: 600; color: #e2e8f0; }
  .contact-value a { color: #7c83ff; text-decoration: none; }
  .contact-value a:hover { text-decoration: underline; }
  .contact-missing { font-size: 0.78rem; color: #374151; font-style: italic; }

  .card-meta { font-size: 0.75rem; color: #64748b; display: flex; flex-direction: column; gap: 2px; margin-top: 2px; }
  .card-meta a { color: #7c83ff; text-decoration: none; }
  .card-meta a:hover { text-decoration: underline; }

  .pills { display: flex; flex-wrap: wrap; gap: 5px; }
  .pill { border-radius: 20px; padding: 3px 9px; font-size: 0.7rem; font-weight: 600; }
  .pill-red   { background: #3d1515; color: #f87171; border: 1px solid #5c1f1f; }
  .pill-amber { background: #3d2e0a; color: #fbbf24; border: 1px solid #5c4510; }
  .pill-green { background: #0d2e1a; color: #34d399; border: 1px solid #164a2a; }
  .pill-gray  { background: #1e2235; color: #94a3b8; border: 1px solid #2d3148; }

  .problem { font-size: 0.8rem; color: #94a3b8; font-style: italic; }

  .whatsapp-box { background: #0d2e1a; border: 1px solid #164a2a; border-radius: 8px;
                  padding: 10px 12px; font-size: 0.8rem; color: #a7f3d0; line-height: 1.5; }
  .copy-btn { align-self: flex-start; background: transparent; border: 1px solid #2d3148;
              border-radius: 6px; color: #64748b; font-size: 0.75rem; padding: 4px 10px;
              cursor: pointer; transition: .15s; }
  .copy-btn:hover { border-color: #7c83ff; color: #7c83ff; }

  .empty { grid-column: 1/-1; text-align: center; padding: 60px; color: #374151; }

  .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #ffffff44;
             border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  #toast { position: fixed; bottom: 20px; right: 20px; background: #22c55e; color: #fff;
           border-radius: 8px; padding: 10px 18px; font-size: 0.85rem; font-weight: 600;
           opacity: 0; transition: opacity .3s; pointer-events: none; z-index: 999; }
  #toast.show { opacity: 1; }

  #progress-overlay { display:none; position:fixed; inset:0; background:#0008;
                      align-items:center; justify-content:center; z-index: 100; flex-direction:column; gap:16px;}
  #progress-overlay.show { display:flex; }
  .progress-box { background:#1a1d2e; border:1px solid #2d3148; border-radius:14px;
                  padding:32px 40px; text-align:center; min-width:320px; }
  .progress-box h2 { color:#7c83ff; margin-bottom:12px; font-size:1rem; }
  .progress-log { font-size:0.78rem; color:#64748b; max-height:120px; overflow-y:auto;
                  margin-top:12px; text-align:left; line-height:1.8; }
</style>
</head>
<body>

<header>
  <h1>🎯 Prospector Diseño Web</h1>
  <div class="badge">Total: <span id="total-count">—</span></div>
  <div class="badge">Sin web: <span id="noweb-count">—</span></div>
  <div class="badge">Web mala: <span id="badweb-count">—</span></div>
</header>

<div class="toolbar">
  <input type="text" id="search" placeholder="Buscar negocio...">
  <select id="filter-web">
    <option value="all">Todos</option>
    <option value="noweb">Sin web</option>
    <option value="badweb">Web mala (&lt;50)</option>
    <option value="hasweb">Con web</option>
  </select>
  <select id="sort">
    <option value="score">Ordenar: Score</option>
    <option value="rating">Ordenar: Rating Google</option>
    <option value="reviews">Ordenar: Reseñas</option>
  </select>
  <span class="chip active" onclick="filterScore(this, 0)">Todos</span>
  <span class="chip" onclick="filterScore(this, 7)">Score 7+</span>
  <span class="chip" onclick="filterScore(this, 9)">Score 9-10</span>
  <button class="run-btn" onclick="runScraper()" id="run-btn">
    ▶ Nueva búsqueda
  </button>
</div>

<div class="stats">
  <div class="stat"><div class="num" id="s-total">—</div><div class="lbl">Total leads</div></div>
  <div class="stat"><div class="num" id="s-noweb">—</div><div class="lbl">Sin web</div></div>
  <div class="stat"><div class="num" id="s-bad">—</div><div class="lbl">Web mala (&lt;50)</div></div>
  <div class="stat"><div class="num" id="s-avg">—</div><div class="lbl">Score medio</div></div>
</div>

<div class="grid" id="grid"></div>
<div id="toast">✓ Copiado al portapapeles</div>

<div id="progress-overlay">
  <div class="progress-box">
    <h2>Ejecutando búsqueda...</h2>
    <div class="spinner" style="margin:0 auto 8px"></div>
    <div class="progress-log" id="progress-log"></div>
  </div>
</div>

<script>
let allLeads = [];
let minScore = 0;

async function loadLeads() {
  const r = await fetch('/api/leads');
  allLeads = await r.json();
  renderAll();
}

function renderAll() {
  const q = document.getElementById('search').value.toLowerCase();
  const fw = document.getElementById('filter-web').value;
  const sort = document.getElementById('sort').value;

  let leads = allLeads.filter(l => {
    if (q && !l.name.toLowerCase().includes(q)) return false;
    if (fw === 'noweb' && l.has_website) return false;
    if (fw === 'hasweb' && !l.has_website) return false;
    if (fw === 'badweb' && (!l.has_website || l.pagespeed_mobile === null || l.pagespeed_mobile >= 50)) return false;
    if (l.urgency_score < minScore) return false;
    return true;
  });

  if (sort === 'rating') leads.sort((a,b) => b.rating - a.rating);
  else if (sort === 'reviews') leads.sort((a,b) => b.reviews_count - a.reviews_count);
  else leads.sort((a,b) => b.urgency_score - a.urgency_score);

  // Stats
  const total = allLeads.length;
  const noWeb = allLeads.filter(l => !l.has_website).length;
  const badWeb = allLeads.filter(l => l.has_website && l.pagespeed_mobile !== null && l.pagespeed_mobile < 50).length;
  const avgScore = total ? (allLeads.reduce((s,l) => s + (l.urgency_score||0), 0) / total).toFixed(1) : 0;
  document.getElementById('total-count').textContent = total;
  document.getElementById('noweb-count').textContent = noWeb;
  document.getElementById('badweb-count').textContent = badWeb;
  document.getElementById('s-total').textContent = total;
  document.getElementById('s-noweb').textContent = noWeb;
  document.getElementById('s-bad').textContent = badWeb;
  document.getElementById('s-avg').textContent = avgScore;

  const grid = document.getElementById('grid');
  if (!leads.length) {
    grid.innerHTML = '<div class="empty">No hay leads con estos filtros.</div>';
    return;
  }
  grid.innerHTML = leads.map(l => cardHTML(l)).join('');
}

function scoreColor(s) {
  if (s >= 9) return { bg: '#3d0f0f', fg: '#f87171' };
  if (s >= 7) return { bg: '#3d2200', fg: '#fb923c' };
  if (s >= 5) return { bg: '#2d2a00', fg: '#facc15' };
  return { bg: '#0d2e1a', fg: '#34d399' };
}

function cardHTML(l) {
  const c = scoreColor(l.urgency_score);
  const stars = l.rating ? '★'.repeat(Math.round(l.rating)) + '☆'.repeat(5-Math.round(l.rating)) : '';

  // Contact block
  const phoneHTML = l.phone
    ? `<div class="contact-item">
        <div class="contact-icon icon-phone">📞</div>
        <div class="contact-value">
          <a href="tel:${l.phone}">${l.phone}</a>
        </div>
      </div>`
    : `<div class="contact-item">
        <div class="contact-icon icon-phone">📞</div>
        <span class="contact-missing">Teléfono no encontrado</span>
      </div>`;

  const emailHTML = l.email
    ? `<div class="contact-item">
        <div class="contact-icon icon-email">✉️</div>
        <div class="contact-value">
          <a href="mailto:${l.email}">${l.email}</a>
        </div>
      </div>`
    : `<div class="contact-item">
        <div class="contact-icon icon-email">✉️</div>
        <span class="contact-missing">Email no encontrado</span>
      </div>`;

  const webHTML = l.website
    ? `<div class="contact-item">
        <div class="contact-icon icon-web">🌐</div>
        <div class="contact-value">
          <a href="${l.website}" target="_blank">${l.website.replace(/^https?:\/\//,'').replace(/\/$/,'').slice(0,38)}</a>
        </div>
      </div>`
    : `<div class="contact-item">
        <div class="contact-icon icon-web">🌐</div>
        <span class="contact-missing">Sin página web</span>
      </div>`;

  // Pills
  const pills = [];
  if (!l.has_website) pills.push('<span class="pill pill-red">SIN WEB</span>');
  if (l.has_website && l.pagespeed_mobile !== null && l.pagespeed_mobile < 50)
    pills.push(`<span class="pill pill-red">Móvil ${l.pagespeed_mobile}/100</span>`);
  else if (l.has_website && l.pagespeed_mobile !== null)
    pills.push(`<span class="pill pill-green">Móvil ${l.pagespeed_mobile}/100</span>`);
  if (l.has_website && l.has_ssl === false) pills.push('<span class="pill pill-amber">Sin SSL</span>');
  if (l.has_website && l.has_ssl) pills.push('<span class="pill pill-green">HTTPS</span>');
  if (l.web_looks_old) pills.push('<span class="pill pill-amber">Web antigua</span>');
  if (l.pagespeed_desktop !== null && l.has_website)
    pills.push(`<span class="pill pill-gray">Desktop ${l.pagespeed_desktop}</span>`);

  const waEscaped = l.whatsapp_message.replace(/'/g,"&#39;").replace(/"/g,"&quot;");
  const phone = l.phone || '';
  const waLink = phone
    ? `https://wa.me/${phone.replace(/\D/g,'')}?text=${encodeURIComponent(l.whatsapp_message)}`
    : '#';

  return `<div class="card">
    <div class="card-top">
      <div class="card-name">${l.name}</div>
      <div class="score-badge" style="background:${c.bg};color:${c.fg}">${l.urgency_score}</div>
    </div>

    <div class="contact-row">
      ${phoneHTML}
      ${emailHTML}
      ${webHTML}
    </div>

    <div class="card-meta">
      ${l.address ? `<span>📍 ${l.address}</span>` : ''}
      ${l.rating ? `<span>${stars} ${l.rating} · ${l.reviews_count} reseñas</span>` : ''}
      ${l.maps_url ? `<span><a href="${l.maps_url}" target="_blank">Ver en Google Maps →</a></span>` : ''}
    </div>

    ${pills.length ? `<div class="pills">${pills.join('')}</div>` : ''}
    ${l.problem_summary ? `<div class="problem">⚠ ${l.problem_summary}</div>` : ''}
    <div class="whatsapp-box">${l.whatsapp_message}</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <button class="copy-btn" onclick="copyMsg('${waEscaped}')">📋 Copiar mensaje</button>
      ${phone ? `<a href="${waLink}" target="_blank"><button class="copy-btn" style="color:#34d399;border-color:#164a2a">💬 Abrir WhatsApp</button></a>` : ''}
    </div>
  </div>`;
}

function copyMsg(text) {
  navigator.clipboard.writeText(text.replace(/&#39;/g,"'").replace(/&quot;/g,'"'));
  const t = document.getElementById('toast');
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}

function filterScore(el, min) {
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  minScore = min;
  renderAll();
}

document.getElementById('search').addEventListener('input', renderAll);
document.getElementById('filter-web').addEventListener('change', renderAll);
document.getElementById('sort').addEventListener('change', renderAll);

async function runScraper() {
  const btn = document.getElementById('run-btn');
  const overlay = document.getElementById('progress-overlay');
  const log = document.getElementById('progress-log');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Ejecutando...';
  overlay.classList.add('show');
  log.innerHTML = '';

  try {
    const resp = await fetch('/api/run', { method: 'POST' });
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      text.split('\\n').forEach(line => {
        if (line.trim()) {
          const p = document.createElement('div');
          p.textContent = line;
          log.appendChild(p);
          log.scrollTop = log.scrollHeight;
        }
      });
    }
    await loadLeads();
  } finally {
    btn.disabled = false;
    btn.innerHTML = '▶ Nueva búsqueda';
    overlay.classList.remove('show');
  }
}

loadLeads();
</script>
</body>
</html>
"""


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(TEMPLATE)

    @app.route("/api/leads")
    def api_leads():
        if DATA_PATH.exists():
            with open(DATA_PATH, encoding="utf-8") as f:
                return jsonify(json.load(f))
        return jsonify([])

    @app.route("/api/run", methods=["POST"])
    def api_run():
        import subprocess
        import sys

        def generate():
            proc = subprocess.Popen(
                [sys.executable, str(Path(__file__).parent / "main.py"), "--pipeline-only"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(Path(__file__).parent),
            )
            for line in proc.stdout:
                yield line
            proc.wait()

        from flask import Response
        return Response(generate(), mimetype="text/plain")

    @app.route("/api/config")
    def api_config():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return jsonify(json.load(f))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5050, debug=True)
