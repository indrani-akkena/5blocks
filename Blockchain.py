"""
Blockchain Visualizer - Python (Flask) + HTML Frontend
Run: pip install flask
     python blockchain_app.py
Open: http://localhost:5000
"""

import hashlib
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

DIFFICULTY = 4
TARGET = "0" * DIFFICULTY

def calc_hash(num, nonce, data, prev):
    content = f"{num}{nonce}{data}{prev}"
    return hashlib.sha256(content.encode()).hexdigest()

def mine(num, data, prev):
    nonce = 0
    while True:
        h = calc_hash(num, nonce, data, prev)
        if h.startswith(TARGET):
            return nonce, h
        nonce += 1

chain = []

def init_chain():
    nonce, h = mine(1, "", "0" * 64)
    chain.append({"num": 1, "nonce": nonce, "data": "", "prev": "0" * 64, "hash": h})

init_chain()

@app.route("/api/chain")
def get_chain():
    return jsonify(chain)

@app.route("/api/mine/<int:idx>", methods=["POST"])
def mine_block(idx):
    if idx < 0 or idx >= len(chain):
        return jsonify({"error": "Invalid index"}), 400
    b = chain[idx]
    nonce, h = mine(b["num"], b["data"], b["prev"])
    chain[idx]["nonce"] = nonce
    chain[idx]["hash"] = h
    for i in range(idx + 1, len(chain)):
        chain[i]["prev"] = chain[i - 1]["hash"]
    return jsonify(chain)

@app.route("/api/update/<int:idx>", methods=["POST"])
def update_data(idx):
    if idx < 0 or idx >= len(chain):
        return jsonify({"error": "Invalid index"}), 400
    data = request.json.get("data", "")
    chain[idx]["data"] = data
    # Recalculate this block's hash (will no longer start with 0000)
    chain[idx]["hash"] = calc_hash(chain[idx]["num"], chain[idx]["nonce"], data, chain[idx]["prev"])
    # Cascade the broken hash forward so downstream blocks show mismatched prev
    for i in range(idx + 1, len(chain)):
        chain[i]["prev"] = chain[i - 1]["hash"]
    return jsonify(chain)

@app.route("/api/add", methods=["POST"])
def add_block():
    prev_block = chain[-1]
    num = len(chain) + 1
    nonce, h = mine(num, "", prev_block["hash"])
    chain.append({"num": num, "nonce": nonce, "data": "", "prev": prev_block["hash"], "hash": h})
    return jsonify(chain)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Blockchain Visualizer</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg:#f0f4f8;--surface:#ffffff;--surface2:#e8edf3;--border:#d1dbe8;
    --border-glow:#b0bfcf;--green:#0f9b6e;--green-dim:#0f9b6e18;
    --green-mid:#0f9b6e55;--red:#d63b52;--red-dim:#d63b5214;--red-mid:#d63b5250;
    --blue:#2563eb;--text:#334155;--text-dim:#7a8fa8;--text-bright:#0f172a;
    --mono:'Share Tech Mono',monospace;--sans:'Rajdhani',sans-serif;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;}
  header{padding:1.5rem 2rem;display:flex;align-items:center;gap:1rem;
    border-bottom:1px solid var(--border);background:var(--surface);}
  .logo{width:34px;height:34px;border:2px solid var(--green);border-radius:6px;
    display:flex;align-items:center;justify-content:center;background:var(--green-dim);}
  .logo svg{width:16px;height:16px;fill:var(--green);}
  header h1{font-size:1.3rem;font-weight:700;letter-spacing:.15em;
    text-transform:uppercase;color:var(--text-bright);}
  .tag{margin-left:auto;font-family:var(--mono);font-size:.62rem;color:var(--green);
    background:var(--green-dim);border:1px solid var(--green-mid);
    padding:3px 10px;border-radius:2px;letter-spacing:.1em;}

  .main{padding:2rem;overflow-x:auto;}
  .chain-row{display:flex;flex-direction:row;align-items:stretch;gap:0;min-width:max-content;}

  .connector{display:flex;align-items:center;justify-content:center;
    width:44px;flex-shrink:0;position:relative;}
  .connector::before{content:'';position:absolute;top:50%;left:0;right:0;
    height:2px;transform:translateY(-50%);}
  .connector.linked::before{background:var(--green-mid);}
  .connector.broken::before{background:var(--red-mid);}
  .connector-icon{width:22px;height:22px;background:var(--surface);
    border:1px solid var(--border-glow);border-radius:50%;display:flex;
    align-items:center;justify-content:center;font-size:11px;
    color:var(--text-dim);position:relative;z-index:1;font-family:var(--mono);}
  .connector.linked .connector-icon{border-color:var(--green-mid);color:var(--green);}
  .connector.broken .connector-icon{border-color:var(--red-mid);color:var(--red);}

  .block{background:var(--surface);border:1.5px solid var(--border);
    border-radius:8px;overflow:hidden;
    transition:border-color .25s,box-shadow .25s,background .25s;
    animation:slideIn .3s ease;width:265px;flex-shrink:0;display:flex;flex-direction:column;}
  @keyframes slideIn{from{opacity:0;transform:translateX(14px)}to{opacity:1;transform:translateX(0)}}
  .block.valid{border-color:var(--green-mid);box-shadow:0 4px 16px var(--green-dim);}
  .block.invalid{border-color:var(--red-mid);box-shadow:0 4px 20px var(--red-dim);background:#fff8f8;}
  .block.just-broken{animation:shake .35s ease;}
  @keyframes shake{
    0%{transform:translateX(0)} 20%{transform:translateX(-5px)}
    40%{transform:translateX(5px)} 60%{transform:translateX(-3px)}
    80%{transform:translateX(3px)} 100%{transform:translateX(0)}
  }

  .block-header{display:flex;align-items:center;gap:8px;padding:9px 14px;
    border-bottom:1px solid var(--border);transition:background .25s;}
  .block.valid   .block-header{background:var(--surface2);}
  .block.invalid .block-header{background:#fdecea;}

  .block-num{font-family:var(--mono);font-size:.65rem;color:var(--text-dim);}
  .block-title{font-size:.82rem;font-weight:700;letter-spacing:.12em;
    text-transform:uppercase;color:var(--text-bright);}
  .tamper-label{font-family:var(--mono);font-size:.56rem;color:var(--red);
    background:#fdecea;border:1px solid #fca5a5;border-radius:3px;padding:2px 6px;}
  .validity-dot{margin-left:auto;width:8px;height:8px;border-radius:50%;
    transition:background .25s;}
  .block.valid   .validity-dot{background:var(--green);}
  .block.invalid .validity-dot{background:var(--red);}

  .block-body{padding:12px 14px;display:flex;flex-direction:column;gap:9px;flex:1;}
  .field{display:flex;align-items:flex-start;gap:10px;}
  .field-label{font-family:var(--mono);font-size:.58rem;color:var(--text-dim);
    text-transform:uppercase;letter-spacing:.1em;min-width:50px;padding-top:6px;}
  .field-value{flex:1;font-family:var(--mono);font-size:.68rem;background:var(--bg);
    border:1px solid var(--border);border-radius:4px;padding:5px 9px;
    color:var(--text);word-break:break-all;line-height:1.6;}
  .field-value.nonce   {color:var(--blue);}
  .field-value.hash-ok {color:var(--green);font-size:.6rem;}
  .field-value.hash-bad{color:var(--red);font-size:.6rem;background:#fff0f0;border-color:#fca5a5;}
  .field-value.prev-ok {color:var(--text-dim);font-size:.6rem;}
  .field-value.prev-bad{color:var(--red);font-size:.6rem;background:#fff0f0;border-color:#fca5a5;}
  textarea.field-value{resize:none;min-height:52px;color:var(--text-bright);
    outline:none;transition:border-color .2s;}
  textarea.field-value:focus{border-color:var(--blue);}

  .block-footer{padding:9px 14px;border-top:1px solid var(--border);
    display:flex;align-items:center;gap:10px;transition:background .25s;}
  .block.valid   .block-footer{background:var(--surface2);}
  .block.invalid .block-footer{background:#fdecea;}

  .mine-btn{font-family:var(--sans);font-size:.78rem;font-weight:700;
    letter-spacing:.12em;text-transform:uppercase;padding:5px 18px;
    border:1px solid var(--green-mid);border-radius:4px;
    background:var(--green-dim);color:var(--green);cursor:pointer;transition:all .15s;}
  .mine-btn:hover{background:var(--green);color:#fff;}
  .mine-btn:disabled{opacity:.35;cursor:not-allowed;}
  @keyframes pulse{from{box-shadow:0 0 4px var(--green-mid)}to{box-shadow:0 0 12px var(--green-mid)}}

  .status-text{font-family:var(--mono);font-size:.6rem;}
  .status-text.ok {color:var(--green);}
  .status-text.bad{color:var(--red);font-weight:500;}

  .add-btn{display:flex;align-items:center;justify-content:center;gap:8px;
    padding:0 20px;height:100%;min-height:80px;background:var(--surface);
    border:1px dashed var(--border-glow);border-radius:8px;color:var(--text-dim);
    font-family:var(--sans);font-size:.82rem;font-weight:600;letter-spacing:.1em;
    text-transform:uppercase;cursor:pointer;transition:all .2s;
    white-space:nowrap;flex-shrink:0;}
  .add-btn:hover{border-color:var(--green-mid);color:var(--green);background:var(--green-dim);}
  .add-btn:disabled{opacity:.4;cursor:not-allowed;}

  .overlay{display:none;position:fixed;inset:0;background:#f0f4f8cc;
    z-index:99;align-items:center;justify-content:center;flex-direction:column;gap:12px;}
  .overlay.show{display:flex;}
  .overlay-text{font-family:var(--mono);font-size:.8rem;color:var(--green);
    letter-spacing:.1em;animation:pulse .5s infinite alternate;}

  ::-webkit-scrollbar{height:4px;}
  ::-webkit-scrollbar-track{background:var(--bg);}
  ::-webkit-scrollbar-thumb{background:var(--border-glow);border-radius:2px;}

  /* flash when hash/prev value changes */
  @keyframes hashflash{
    0%  {background:#fff3cd;}
    40% {background:#ffe082;}
    100%{background:transparent;}
  }
  .hash-flash{animation:hashflash .6s ease-out;}
  .hash-bad.hash-flash{animation:hashflash .6s ease-out;background:#ffcdd2!important;}
  .prev-bad.hash-flash{animation:hashflash .6s ease-out;background:#ffcdd2!important;}
</style>
</head>
<body>

<div class="overlay" id="overlay">
  <div class="logo" style="width:48px;height:48px;">
    <svg viewBox="0 0 20 20" style="width:22px;height:22px;fill:#0f9b6e">
      <path d="M10 1L3 5v5c0 4.4 3 8.5 7 9.5 4-1 7-5.1 7-9.5V5L10 1z"/>
    </svg>
  </div>
  <div class="overlay-text" id="overlay-msg">Mining block...</div>
</div>

<header>
  <div class="logo">
    <svg viewBox="0 0 20 20"><path d="M10 1L3 5v5c0 4.4 3 8.5 7 9.5 4-1 7-5.1 7-9.5V5L10 1zm-1 12l-3-3 1.4-1.4L9 10.2l4.6-4.6L15 7l-6 6z"/></svg>
  </div>
  <h1>Blockchain</h1>
  <div class="tag">SHA-256 · DIFFICULTY 0000</div>
</header>

<div class="main">
  <div class="chain-row" id="chain"></div>
</div>

<script>
let busy = false;
let chainData = [];

// ── SHA-256 in browser so we can update hashes instantly as user types ────────
async function sha256(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('');
}

async function calcHash(num, nonce, data, prev) {
  return sha256(`${num}${nonce}${data}${prev}`);
}

function isMined(hash)     { return hash.startsWith('0000'); }
function isLinked(b, prev) { return b.prev === prev; }
function isValid(b, prev)  { return isMined(b.hash) && isLinked(b, prev); }

// ── Flash animation on a DOM element ─────────────────────────────────────────
function flash(el) {
  el.classList.remove('hash-flash');
  void el.offsetWidth; // reflow
  el.classList.add('hash-flash');
  setTimeout(() => el.classList.remove('hash-flash'), 600);
}

// ── Apply validity state to a block card without re-creating it ───────────────
function patchCard(card, b, prevHash, animate) {
  const valid  = isValid(b, prevHash);
  const linked = isLinked(b, prevHash);
  const mined  = isMined(b.hash);

  // card border + bg
  card.classList.toggle('valid',   valid);
  card.classList.toggle('invalid', !valid);

  // tamper label
  let lbl = card.querySelector('.tamper-label');
  if (!valid) {
    if (!lbl) {
      lbl = document.createElement('span');
      lbl.className = 'tamper-label';
      lbl.textContent = 'tampered';
      card.querySelector('.block-header').insertBefore(lbl, card.querySelector('.validity-dot'));
    }
  } else {
    if (lbl) lbl.remove();
  }

  // connector before this card (it lives just before the card in the DOM)
  const conn = card.previousElementSibling;
  if (conn && conn.classList.contains('connector')) {
    conn.classList.toggle('linked', linked);
    conn.classList.toggle('broken', !linked);
    conn.querySelector('.connector-icon').innerHTML = linked ? '&rarr;' : '&times;';
  }

  // prev field
  const prevEl = card.querySelector('.prev-field');
  const oldPrev = prevEl.textContent;
  if (oldPrev !== b.prev) {
    prevEl.textContent = b.prev;
    prevEl.className = `field-value ${linked ? 'prev-ok' : 'prev-bad'} prev-field`;
    if (animate) flash(prevEl);
  } else {
    prevEl.className = `field-value ${linked ? 'prev-ok' : 'prev-bad'} prev-field`;
  }

  // hash field
  const hashEl = card.querySelector('.hash-field');
  const oldHash = hashEl.textContent;
  if (oldHash !== b.hash) {
    hashEl.textContent = b.hash;
    hashEl.className = `field-value ${mined ? 'hash-ok' : 'hash-bad'} hash-field`;
    if (animate) flash(hashEl);
  } else {
    hashEl.className = `field-value ${mined ? 'hash-ok' : 'hash-bad'} hash-field`;
  }

  // status text
  const st = card.querySelector('.status-text');
  st.className = `status-text ${valid ? 'ok' : 'bad'}`;
  st.innerHTML  = valid ? '&#10003; valid' : !mined ? '&#10007; hash invalid' : '&#10007; chain broken';
}

// ── Full render (used on first load / mine / add) ─────────────────────────────
function render(chain) {
  chainData = chain;
  const container = document.getElementById('chain');
  container.innerHTML = '';

  chain.forEach((b, i) => {
    const prevHash = i === 0 ? '0'.repeat(64) : chain[i-1].hash;
    const valid    = isValid(b, prevHash);
    const linked   = isLinked(b, prevHash);
    const mined    = isMined(b.hash);

    if (i > 0) {
      const conn = document.createElement('div');
      conn.className = `connector ${linked ? 'linked' : 'broken'}`;
      conn.innerHTML = `<div class="connector-icon">${linked ? '&rarr;' : '&times;'}</div>`;
      container.appendChild(conn);
    }

    const card = document.createElement('div');
    card.className = `block ${valid ? 'valid' : 'invalid'}`;
    card.dataset.idx = i;
    card.innerHTML = `
      <div class="block-header">
        <span class="block-num">#${String(b.num).padStart(3,'0')}</span>
        <span class="block-title">Block ${b.num}</span>
        ${!valid ? '<span class="tamper-label">tampered</span>' : ''}
        <div class="validity-dot"></div>
      </div>
      <div class="block-body">
        <div class="field">
          <span class="field-label">Nonce</span>
          <div class="field-value nonce">${b.nonce}</div>
        </div>
        <div class="field">
          <span class="field-label">Data</span>
          <textarea class="field-value" rows="2" placeholder="Enter transaction data...">${b.data}</textarea>
        </div>
        <div class="field">
          <span class="field-label">Prev</span>
          <div class="field-value ${linked ? 'prev-ok' : 'prev-bad'} prev-field">${b.prev}</div>
        </div>
        <div class="field">
          <span class="field-label">Hash</span>
          <div class="field-value ${mined ? 'hash-ok' : 'hash-bad'} hash-field">${b.hash}</div>
        </div>
      </div>
      <div class="block-footer">
        <button class="mine-btn" onclick="mineBlock(${i})">Mine</button>
        <span class="status-text ${valid ? 'ok' : 'bad'}">
          ${valid ? '&#10003; valid' : !mined ? '&#10007; hash invalid' : '&#10007; chain broken'}
        </span>
      </div>
    `;
    container.appendChild(card);

    // ── Instant live update on every keystroke ──────────────────────────────
    card.querySelector('textarea').addEventListener('input', async (e) => {
      const idx  = parseInt(card.dataset.idx);
      const data = e.target.value;

      // 1. Recompute this block's hash instantly in the browser
      const newHash = await calcHash(
        chainData[idx].num, chainData[idx].nonce, data, chainData[idx].prev
      );
      chainData[idx].data = data;
      chainData[idx].hash = newHash;

      // 2. Cascade prev hashes into downstream blocks
      for (let j = idx + 1; j < chainData.length; j++) {
        chainData[j].prev = chainData[j-1].hash;
      }

      // 3. Patch every card visually (animate downstream ones)
      const cards = document.querySelectorAll('.block');
      cards.forEach((c, ci) => {
        const ph = ci === 0 ? '0'.repeat(64) : chainData[ci-1].hash;
        patchCard(c, chainData[ci], ph, ci !== idx);
      });

      // 4. Sync to backend (no debounce — fire and forget)
      fetch(`/api/update/${idx}`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({data})
      });
    });
  });

  const sep = document.createElement('div');
  sep.className = 'connector linked';
  sep.innerHTML = `<div class="connector-icon">&rarr;</div>`;
  container.appendChild(sep);

  const addBtn = document.createElement('button');
  addBtn.className = 'add-btn';
  addBtn.onclick = addBlock;
  addBtn.innerHTML = `<span>+</span>&nbsp;Add Block`;
  container.appendChild(addBtn);
}

async function mineBlock(idx) {
  if (busy) return;
  busy = true;
  showOverlay(`Mining block #${idx+1}...`);
  render(await (await fetch(`/api/mine/${idx}`, {method:'POST'})).json());
  hideOverlay(); busy = false;
}

async function addBlock() {
  if (busy) return;
  busy = true;
  showOverlay('Mining new block...');
  render(await (await fetch('/api/add', {method:'POST'})).json());
  hideOverlay(); busy = false;
}

function showOverlay(msg) {
  document.getElementById('overlay-msg').textContent = msg;
  document.getElementById('overlay').classList.add('show');
}
function hideOverlay() {
  document.getElementById('overlay').classList.remove('show');
}

fetch('/api/chain').then(r => r.json()).then(render);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    print("\n🔗 Blockchain Visualizer running at http://localhost:5501\n")
    app.run(debug=True, port=5501)