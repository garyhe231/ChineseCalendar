#!/usr/bin/env python3
"""
URL Connection Analyzer — Web Interface

A mobile-friendly web UI for the URL connection analyzer.
No external dependencies — uses only Python standard library.

Usage:
    python3 url_analyzer_web.py              # starts on port 8080
    python3 url_analyzer_web.py --port 3000  # custom port
"""

import argparse
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from url_analyzer import analyze, normalize_url, report_to_dict

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>URL Connection Analyzer</title>
<style>
  :root {
    --bg: #0f172a;
    --card: #1e293b;
    --border: #334155;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #38bdf8;
    --green: #4ade80;
    --yellow: #facc15;
    --red: #f87171;
    --bar-bg: #334155;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 16px;
  }
  .container { max-width: 600px; margin: 0 auto; }
  h1 {
    font-size: 1.4rem;
    text-align: center;
    margin: 20px 0 8px;
    color: var(--accent);
  }
  .subtitle {
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    margin-bottom: 24px;
  }
  .input-group {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
  }
  input[type="text"] {
    flex: 1;
    padding: 12px 16px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--text);
    font-size: 1rem;
    outline: none;
    transition: border-color 0.2s;
  }
  input[type="text"]:focus { border-color: var(--accent); }
  input[type="text"]::placeholder { color: var(--muted); }
  button {
    padding: 12px 20px;
    border-radius: 10px;
    border: none;
    background: var(--accent);
    color: var(--bg);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity 0.2s;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }

  .spinner {
    display: none;
    text-align: center;
    padding: 40px;
    color: var(--muted);
  }
  .spinner.active { display: block; }
  .spinner .dot {
    display: inline-block;
    width: 10px; height: 10px;
    margin: 0 4px;
    border-radius: 50%;
    background: var(--accent);
    animation: bounce 1.4s infinite ease-in-out both;
  }
  .spinner .dot:nth-child(1) { animation-delay: -0.32s; }
  .spinner .dot:nth-child(2) { animation-delay: -0.16s; }
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }

  #results { display: none; }
  #results.active { display: block; }

  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
  }
  .card-title {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin-bottom: 12px;
  }
  .meta-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 0.9rem;
  }
  .meta-label { color: var(--muted); }
  .meta-value { font-weight: 500; }

  .phase {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
  }
  .phase:last-child { border-bottom: none; }
  .phase-icon {
    width: 24px; height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    flex-shrink: 0;
  }
  .phase-icon.ok { background: rgba(74,222,128,0.15); color: var(--green); }
  .phase-icon.warning { background: rgba(250,204,21,0.15); color: var(--yellow); }
  .phase-icon.error { background: rgba(248,113,113,0.15); color: var(--red); }
  .phase-info { flex: 1; min-width: 0; }
  .phase-name { font-size: 0.9rem; font-weight: 500; }
  .phase-detail { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }
  .phase-time {
    font-size: 0.9rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .bar-wrap {
    width: 100%;
    height: 6px;
    background: var(--bar-bg);
    border-radius: 3px;
    margin-top: 6px;
    overflow: hidden;
  }
  .bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
  }
  .bar-fill.ok { background: var(--green); }
  .bar-fill.warning { background: var(--yellow); }
  .bar-fill.error { background: var(--red); }

  .total-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 12px;
    margin-top: 4px;
    border-top: 2px solid var(--border);
    font-weight: 700;
    font-size: 1rem;
  }

  .verdict-card {
    text-align: center;
    padding: 20px 16px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 1.05rem;
  }
  .verdict-card.healthy { background: rgba(74,222,128,0.1); border: 1px solid var(--green); color: var(--green); }
  .verdict-card.slow { background: rgba(250,204,21,0.1); border: 1px solid var(--yellow); color: var(--yellow); }
  .verdict-card.failed { background: rgba(248,113,113,0.1); border: 1px solid var(--red); color: var(--red); }

  .issue-item, .suggestion-item {
    padding: 8px 0;
    font-size: 0.88rem;
    line-height: 1.5;
    border-bottom: 1px solid var(--border);
  }
  .issue-item:last-child, .suggestion-item:last-child { border-bottom: none; }
  .issue-item::before { content: "● "; color: var(--yellow); }
  .suggestion-item::before { content: "→ "; color: var(--accent); }
  .issue-item.healthy::before { content: "● "; color: var(--green); }
</style>
</head>
<body>
<div class="container">
  <h1>URL Connection Analyzer</h1>
  <p class="subtitle">Analyze DNS, TCP, TLS &amp; HTTP connection details</p>

  <div class="input-group">
    <input type="text" id="urlInput" placeholder="Enter a URL, e.g. google.com" autocapitalize="none" autocorrect="off" spellcheck="false">
    <button id="analyzeBtn" onclick="runAnalysis()">Analyze</button>
  </div>

  <div class="spinner" id="spinner">
    <div><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
    <p style="margin-top:12px">Analyzing connection&hellip;</p>
  </div>

  <div id="results"></div>
</div>

<script>
const input = document.getElementById('urlInput');
input.addEventListener('keydown', e => { if (e.key === 'Enter') runAnalysis(); });

async function runAnalysis() {
  const url = input.value.trim();
  if (!url) return;

  const btn = document.getElementById('analyzeBtn');
  const spinner = document.getElementById('spinner');
  const results = document.getElementById('results');

  btn.disabled = true;
  results.className = '';
  results.innerHTML = '';
  spinner.className = 'spinner active';

  try {
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await resp.json();
    renderResults(data);
  } catch (err) {
    results.innerHTML = `<div class="verdict-card failed">Request failed: ${err.message}</div>`;
    results.className = 'active';
  } finally {
    btn.disabled = false;
    spinner.className = 'spinner';
  }
}

function statusClass(s) {
  return s === 'OK' ? 'ok' : s === 'WARNING' ? 'warning' : 'error';
}
function statusIcon(s) {
  return s === 'OK' ? '✓' : s === 'WARNING' ? '!' : '✗';
}
function fmt(ms) {
  return ms >= 1000 ? (ms / 1000).toFixed(2) + ' s' : ms.toFixed(0) + ' ms';
}

function renderResults(d) {
  const results = document.getElementById('results');
  const total = d.total_ms || 1;

  // Build phases
  const phases = [
    { name: 'DNS Resolution', data: d.dns, detail: d.dns.resolved_ips?.join(', ') },
    { name: 'TCP Handshake', data: d.tcp, detail: null },
  ];
  if (d.tls) {
    const tlsDetail = d.tls.protocol_version
      ? `${d.tls.protocol_version} · ${d.tls.cipher || ''}` : null;
    phases.push({ name: 'TLS Handshake', data: d.tls, detail: tlsDetail });
  }
  const httpDetail = d.http.status_code ? `HTTP ${d.http.status_code} ${d.http.reason || ''}` : null;
  phases.push({ name: 'HTTP Response', data: d.http, detail: httpDetail });

  let phaseHTML = phases.map(p => {
    const cls = statusClass(p.data.status);
    const pct = Math.min((p.data.duration_ms / total) * 100, 100);
    return `
      <div class="phase">
        <div class="phase-icon ${cls}">${statusIcon(p.data.status)}</div>
        <div class="phase-info">
          <div class="phase-name">${p.name}</div>
          ${p.data.error ? `<div class="phase-detail" style="color:var(--red)">${esc(p.data.error)}</div>`
            : p.detail ? `<div class="phase-detail">${esc(p.detail)}</div>` : ''}
          <div class="bar-wrap"><div class="bar-fill ${cls}" style="width:${pct}%"></div></div>
        </div>
        <div class="phase-time">${fmt(p.data.duration_ms)}</div>
      </div>`;
  }).join('');

  // Determine verdict
  const errCount = phases.filter(p => p.data.status === 'ERROR').length;
  const warnCount = phases.filter(p => p.data.status === 'WARNING').length;
  let verdictClass, verdictText;
  if (errCount) {
    verdictClass = 'failed';
    verdictText = `Connection Failed — ${errCount} error(s) detected`;
  } else if (warnCount || d.total_ms > 3000) {
    verdictClass = 'slow';
    verdictText = `Connection OK — with ${warnCount} warning(s)`;
  } else {
    verdictClass = 'healthy';
    verdictText = 'Connection Healthy — everything looks good!';
  }

  // Issues & suggestions
  const hasRealIssues = d.issues?.some(i => !i.includes('No issues'));
  let issuesHTML = '';
  if (d.issues?.length) {
    issuesHTML = `<div class="card"><div class="card-title">Diagnosis</div>` +
      d.issues.map(i => `<div class="issue-item${i.includes('No issues') ? ' healthy' : ''}">${esc(i)}</div>`).join('') +
      `</div>`;
  }
  let suggestionsHTML = '';
  if (hasRealIssues && d.suggestions?.length) {
    suggestionsHTML = `<div class="card"><div class="card-title">Suggestions</div>` +
      d.suggestions.map(s => `<div class="suggestion-item">${esc(s)}</div>`).join('') +
      `</div>`;
  }

  results.innerHTML = `
    <div class="card">
      <div class="card-title">Connection Details</div>
      <div class="meta-row"><span class="meta-label">URL</span><span class="meta-value" style="word-break:break-all">${esc(d.url)}</span></div>
      <div class="meta-row"><span class="meta-label">Host</span><span class="meta-value">${esc(d.hostname)}:${d.port}</span></div>
      <div class="meta-row"><span class="meta-label">Scheme</span><span class="meta-value">${d.is_https ? 'HTTPS' : 'HTTP'}</span></div>
      ${d.http.server ? `<div class="meta-row"><span class="meta-label">Server</span><span class="meta-value">${esc(d.http.server)}</span></div>` : ''}
    </div>
    <div class="card">
      <div class="card-title">Timing Breakdown</div>
      ${phaseHTML}
      <div class="total-row"><span>Total</span><span>${fmt(d.total_ms)}</span></div>
    </div>
    ${issuesHTML}
    ${suggestionsHTML}
    <div class="verdict-card ${verdictClass}">${verdictText}</div>
  `;
  results.className = 'active';
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
</script>
</body>
</html>
"""


class AnalyzerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode())

    def do_POST(self):
        if self.path != "/analyze":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
            raw_url = payload.get("url", "").strip()
        except (json.JSONDecodeError, AttributeError):
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        if not raw_url:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "URL is required"}).encode())
            return

        url = normalize_url(raw_url)
        report = analyze(url)
        result = report_to_dict(report)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def log_message(self, format, *args):
        print(f"  {self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="URL Connection Analyzer — Web Interface")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), AnalyzerHandler)
    print(f"\n  URL Connection Analyzer is running!")
    print(f"  Open in your browser: http://localhost:{args.port}")
    print(f"  On your phone (same Wi-Fi): http://<your-ip>:{args.port}")
    print(f"  Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
