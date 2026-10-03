#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_pages.py — 生成 GitHub Pages 網站（docs/index.html）

設計：
- 由 stats.json + 實際目錄結構自動生成（治本：加新分類唔使改 HTML）
- 網站係單頁 app：fetch raw.githubusercontent.com 嘅 stats.json + 清單檔
- 內嵌 CSS/JS，無外部依賴（GitHub Pages 直接 serve）

用法：
  python gen_pages.py
環境變數：
  GITHUB_REPOSITORY（Actions 自動提供，例如 stevendolike/DD）
"""
import json
import os
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "stevendolike/DD")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
OUT_DIR = "docs"
OUT_FILE = os.path.join(OUT_DIR, "index.html")

# 分類顯示資料：(圖示, 標題, 說明, 排序權重)
CATEGORY_META = {
    "regions_json_preferred_asn": ("⭐", "優選 ASN", "中國線路優化：CN2 / CUII / CMI 骨幹、CN2 GIA 機房、香港直連、中國雲廠、台灣", 10),
    "regions_json_preferred_asn_443": ("⭐", "優選 ASN（443 純 IP）", "優選 ASN 嘅 443 端口純 IP 版", 11),
    "regions_json_residential": ("🏠", "家庭寬帶", "住宅寬帶 ISP（含混合型電訊商，如 HKT / Korea Telecom / Comcast）", 20),
    "regions_json_residential_443": ("🏠", "家庭寬帶（443 純 IP）", "家庭寬帶嘅 443 端口純 IP 版", 21),
    "regions_json": ("🌍", "全部（所有 Port）", "完整清單，按國家 → 組織分類，保留原始端口", 30),
    "regions_json_clientip_v4": ("🧩", "ClientIP v4", "客戶端 IP（IPv4），按國家 → 組織分類", 40),
}
PORT_TITLES = {
    "443": "443", "2053": "2053", "2083": "2083",
    "2087": "2087", "2096": "2096", "8443": "8443",
}

HEAD = """<!DOCTYPE html>
<html lang="zh-HK">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>IP List by Region · Cloudflare 優選 IP</title>
<meta name="description" content="Cloudflare 優選 IP 清單，按地區、營運商、ASN 分類。含中國線路優化 ASN、家庭寬帶 ISP。">
<style>
:root{
  --bg:#0b0f17; --panel:#131a26; --panel2:#182231; --line:#243044;
  --fg:#e6edf7; --dim:#8b9bb4; --accent:#4da3ff; --accent2:#7ee787;
  --radius:clamp(9px,2vw,12px);
  color-scheme:dark;                 /* 原生控件 / 滾動條跟深色 */
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--fg);
  font:clamp(13.5px,3.4vw,15px)/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif;
  overflow-x:hidden;
  padding-left:env(safe-area-inset-left);      /* 劉海屏安全區 */
  padding-right:env(safe-area-inset-right);
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{
  padding:calc(clamp(24px,6vw,38px) + env(safe-area-inset-top)) clamp(14px,4vw,20px) clamp(18px,4.5vw,26px);
  text-align:center;border-bottom:1px solid var(--line);
  background:radial-gradient(1200px 300px at 50% -80px,rgba(77,163,255,.18),transparent);
}
h1{margin:0 0 6px;font-size:clamp(19px,5.4vw,27px);line-height:1.25;letter-spacing:.3px}
.sub{margin:0;color:var(--dim);font-size:clamp(12.5px,3.4vw,14px)}
.meta{margin-top:clamp(8px,2.4vw,12px);color:var(--dim);font-size:clamp(11.5px,3.1vw,12.5px);
  display:flex;flex-wrap:wrap;gap:4px 10px;justify-content:center;align-items:center}
.meta b{color:var(--accent2)}
main{max-width:1120px;margin:0 auto;
  padding:clamp(16px,3.6vw,26px) clamp(12px,3.4vw,18px) clamp(46px,9vw,70px)}
.grid{display:grid;gap:clamp(10px,2.4vw,14px);
  grid-template-columns:repeat(auto-fill,minmax(min(100%,clamp(150px,44vw,255px)),1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:clamp(13px,3vw,16px) clamp(14px,3.2vw,17px);cursor:pointer;transition:.16s;position:relative}
.card:hover{border-color:var(--accent);transform:translateY(-2px);background:var(--panel2)}
.card.active{border-color:var(--accent);background:var(--panel2)}
.card .ic{font-size:clamp(17px,4.4vw,20px)}
.card h3{margin:8px 0 5px;font-size:clamp(14.5px,3.9vw,15.5px);overflow-wrap:anywhere}
.card .n{color:var(--accent2);font-weight:600}
.card .d{color:var(--dim);font-size:clamp(11.5px,3.2vw,12.5px);margin-top:5px;line-height:1.5}
.card .cc{color:var(--dim);font-size:clamp(11px,3.1vw,12px);margin-top:8px}
.row{display:flex;flex-wrap:wrap;align-items:center;gap:clamp(7px,2vw,10px);margin:0 0 clamp(11px,2.6vw,14px)}
input[type=search]{flex:1 1 180px;min-width:0;background:var(--panel);border:1px solid var(--line);
  color:var(--fg);border-radius:9px;padding:clamp(9px,2.4vw,10px) clamp(11px,3vw,13px);
  font-size:clamp(13px,3.6vw,14px);outline:none}
input[type=search]:focus{border-color:var(--accent)}
button,.btn{background:var(--panel);border:1px solid var(--line);color:var(--fg);border-radius:9px;
  padding:clamp(8px,2.2vw,9px) clamp(11px,3vw,14px);font-size:clamp(12.5px,3.4vw,13.5px);
  cursor:pointer;transition:.14s;white-space:nowrap}
button:hover:not(:disabled),.btn:hover{border-color:var(--accent);color:var(--accent)}
button:disabled{cursor:default}
button.primary{background:rgba(77,163,255,.14);border-color:var(--accent);color:var(--accent)}
#detail{margin-top:clamp(22px,5vw,30px);border-top:1px solid var(--line);padding-top:clamp(18px,4.4vw,24px)}
#detail[hidden]{display:none}
h2{margin:0 0 4px;font-size:clamp(17px,4.6vw,20px);overflow-wrap:anywhere}
.hint{color:var(--dim);font-size:clamp(12px,3.4vw,13px);margin:0 0 clamp(11px,2.6vw,14px)}
h4{margin:clamp(16px,3.8vw,22px) 0 9px;font-size:clamp(13px,3.6vw,14.5px);color:var(--dim);
  text-transform:uppercase;letter-spacing:.5px;font-weight:600}
.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 clamp(14px,3.4vw,20px);
  border-radius:var(--radius)}
table{width:100%;min-width:min(100%,400px);border-collapse:collapse;
  font-size:clamp(12.5px,3.4vw,14px)}
th,td{padding:clamp(7px,2vw,9px) clamp(8px,2.4vw,11px);border-bottom:1px solid var(--line);
  text-align:left;white-space:nowrap}
td.wrap{white-space:normal;overflow-wrap:anywhere}
th{color:var(--dim);font-weight:600;font-size:clamp(11.5px,3.2vw,12.5px);text-transform:uppercase;
  letter-spacing:.4px}
tbody tr:hover{background:var(--panel)}
td.num{color:var(--accent2);text-align:right;font-variant-numeric:tabular-nums}
pre{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:clamp(12px,3.2vw,16px);max-height:min(62vh,460px);overflow:auto;
  font:clamp(11.5px,3.2vw,13px)/1.65 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  white-space:pre-wrap;word-break:break-all;margin:0}
.toolbar{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin:0 0 12px}
.stat{color:var(--dim);font-size:clamp(12px,3.3vw,13px)}
.loading{color:var(--dim);padding:18px 0}
.toast{position:fixed;left:50%;bottom:calc(clamp(14px,4vw,22px) + env(safe-area-inset-bottom));
  transform:translateX(-50%) translateY(80px);background:var(--accent2);color:#07130a;
  padding:clamp(9px,2.4vw,10px) clamp(15px,4vw,20px);border-radius:9px;font-weight:600;
  font-size:clamp(12.5px,3.4vw,13.5px);max-width:calc(100vw - 28px);text-align:center;
  transition:.25s;opacity:0;pointer-events:none;z-index:99}
.toast.on{transform:translateX(-50%) translateY(0);opacity:1}
footer{text-align:center;color:var(--dim);font-size:clamp(11.5px,3.2vw,12.5px);
  padding:clamp(20px,5vw,26px) clamp(14px,4vw,16px) calc(clamp(30px,7vw,40px) + env(safe-area-inset-bottom));
  border-top:1px solid var(--line)}
</style>
</head>
<body>
<header>
  <h1>⚡ IP List by Region</h1>
  <p class="sub">Cloudflare 優選 IP · 按地區 / 營運商 / ASN 分類</p>
  <div class="meta">共 <b id="m-total">–</b> 條 · <b id="m-cats">–</b> 個分類 ·
    <a id="m-repo" href="#">GitHub</a> · <span id="m-updated">–</span></div>
</header>
<main>
  <div class="grid" id="grid"><div class="loading">載入中…</div></div>
  <section id="detail" hidden>
    <h2 id="d-title"></h2>
    <p class="hint" id="d-desc"></p>
    <div class="row">
      <input type="search" id="q" placeholder="搜尋 IP / 國家 / 端口…（例如 1.1.1 或 HK）">
      <button id="btn-all" class="primary">顯示全部</button>
      <button id="btn-copy">複製清單</button>
      <a class="btn" id="d-raw" target="_blank" rel="noopener">Raw 檔</a>
    </div>
    <div id="d-body"><div class="loading">載入中…</div></div>
  </section>
</main>
<footer>
  資料來源：Cloudflare 優選 IP 掃描 · 每 6 小時自動更新<br>
  由 <a id="f-repo" href="#">GitHub Actions</a> 生成 · 想自己改就 fork（設定見 README）
</footer>
<div class="toast" id="toast">已複製</div>
<script>
const REPO = "__REPO__", BRANCH = "__BRANCH__";
const RAW = "https://raw.githubusercontent.com/" + REPO + "/" + BRANCH;
const CATS = __CATS__;
const STATS = __STATS__;
const UPDATED = "__UPDATED__";
document.getElementById("m-repo").href = "https://github.com/" + REPO;
document.getElementById("f-repo").href = "https://github.com/" + REPO;
document.getElementById("m-updated").textContent = "更新 " + UPDATED;

const $ = (id) => document.getElementById(id);
const sum = (o) => Object.values(o || {}).reduce((a, b) => a + b, 0);

function toast(msg){
  const t = $("toast"); t.textContent = msg; t.classList.add("on");
  setTimeout(() => t.classList.remove("on"), 1400);
}
async function copy(text, msg){
  try { await navigator.clipboard.writeText(text); toast(msg || "已複製"); }
  catch(e){ toast("複製失敗（瀏覽器限制）"); }
}
function esc(s){ return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

/* ── 總覽 ── */
let totalAll = 0, catCount = 0;
function renderOverview(){
  const grid = $("grid"); grid.innerHTML = "";
  CATS.forEach(c => {
    const st = STATS[c.dir] || {};
    const n = sumOne(st);   // 統一：flat 同 nested 都支援
    const ncc = Object.keys(st).length;
    totalAll += n; catCount++;
    const d = document.createElement("div");
    d.className = "card"; d.dataset.dir = c.dir;
    d.innerHTML = `<div class="ic">${c.icon}</div><h3>${esc(c.title)}</h3>
      <div><span class="n">${n.toLocaleString()}</span> 條</div>
      <div class="cc">${ncc} 個國家／地區</div>
      <div class="d">${esc(c.desc)}</div>`;
    d.onclick = () => openCat(c, d);
    grid.appendChild(d);
  });
  $("m-total").textContent = totalAll.toLocaleString();
  $("m-cats").textContent = catCount;
}
function sumOne(st){ // regions_json 係 國家 -> 組織 -> 數
  let t = 0;
  for (const k in st){
    const v = st[k];
    t += (typeof v === "number") ? v : sum(v);
  }
  return t;
}
function countryMap(dir){
  const st = STATS[dir] || {};
  const out = {};
  for (const k in st){
    const v = st[k];
    out[k] = (typeof v === "number") ? v : sum(v);
  }
  return out;
}
</script>
<script>
/* ── 詳情 ── */
let curCat = null, curMode = "all", curData = [], curText = "", allTextCache = "";
function fileFor(dir, c, mode){
  if (mode === "all") return dir + "/_all.txt";
  return dir + "/" + c + ".txt";
}
async function fetchText(rel){
  const r = await fetch(RAW + "/" + rel + "?t=" + Date.now());
  if (!r.ok) throw new Error(r.status);
  return await r.text();
}
async function openCat(cat, cardEl){
  curCat = cat; curMode = "all";
  document.querySelectorAll(".card").forEach(e => e.classList.remove("active"));
  if (cardEl) cardEl.classList.add("active");
  $("d-title").textContent = cat.icon + " " + cat.title;
  $("d-desc").textContent = cat.desc;
  $("detail").hidden = false;
  $("detail").scrollIntoView({behavior:"smooth", block:"start"});
  $("d-raw").href = RAW + "/" + cat.dir + "/_all.txt";
  $("d-body").innerHTML = '<div class="loading">載入中…</div>';
  try {
    curText = await fetchText(fileFor(cat.dir, null, "all"));
    allTextCache = curText;
    renderDetail();
  } catch(e){
    $("d-body").innerHTML = '<div class="loading">載入失敗：' + esc(e.message) +
      '（<a href="' + RAW + "/" + cat.dir + '/_all.txt" target="_blank">直接開 raw</a>）</div>';
  }
}
function renderDetail(){
  const lines = curText.split("\\n").map(s => s.trim()).filter(Boolean);
  curData = lines;
  const cm = countryMap(curCat.dir);
  const isOrg = curCat.dir === "regions_json" || curCat.dir === "regions_json_clientip_v4";

  let html = "";
  if (curMode === "all"){
    html += '<h4>國家／地區</h4>';
    html += '<div class="table-wrap"><table><thead><tr><th>國家</th><th style="text-align:right">條目數</th><th>檔案</th></tr></thead><tbody>';
    Object.keys(cm).sort().forEach(c => {
      html += `<tr><td><b>${esc(c)}</b></td><td class="num">${cm[c].toLocaleString()}</td>
        <td><a href="${RAW}/${curCat.dir}/${c}.txt" target="_blank" rel="noopener">raw</a>
        · <a href="#" data-cc="${esc(c)}" class="lnk">睇清單</a></td></tr>`;
    });
    html += "</tbody></table></div>";
  }
  html += `<h4>清單 <span class="stat" id="cnt"></span></h4>`;
  html += '<pre id="list"></pre>';
  $("d-body").innerHTML = html;
  $("d-body").querySelectorAll(".lnk").forEach(a => {
    a.onclick = async (ev) => {
      ev.preventDefault();
      const c = a.dataset.cc;
      $("d-body").innerHTML = '<div class="loading">載入中…</div>';
      try { curText = await fetchText(curCat.dir + "/" + c + ".txt"); }
      catch(e){ $("d-body").innerHTML = '<div class="loading">載入失敗</div>'; return; }
      curMode = c; renderDetail();
    };
  });
  paint();
}
function paint(){
  const q = $("q").value.trim().toLowerCase();
  const rows = q ? curData.filter(l => l.toLowerCase().includes(q)) : curData;
  $("list").textContent = rows.join("\\n");
  $("cnt").textContent = "· 顯示 " + rows.length.toLocaleString() +
    " / " + curData.length.toLocaleString() + " 條";
  const atAll = curMode === "all";
  $("btn-all").textContent = atAll ? "顯示全部 IP" : "← 返回國家列表";
  $("btn-all").disabled = atAll;
  $("btn-all").style.opacity = atAll ? ".45" : "1";
}
$("q").addEventListener("input", paint);
$("btn-all").onclick = () => {
  if (curMode === "all") return;
  curMode = "all"; curText = allTextCache; renderDetail();
};
$("btn-copy").onclick = () => {
  const q = $("q").value.trim().toLowerCase();
  const rows = q ? curData.filter(l => l.toLowerCase().includes(q)) : curData;
  copy(rows.join("\\n"), "已複製 " + rows.length + " 條");
};
renderOverview();
</script>
</body>
</html>
"""


def discover_categories():
    """掃目錄自動偵測分類（治本：加新目錄唔使改 script 邏輯）"""
    dirs = [d for d in sorted(os.listdir("."))
            if d.startswith("regions_json") and os.path.isdir(d)]
    cats = []
    extra = []
    for d in dirs:
        if d in CATEGORY_META:
            icon, title, desc, w = CATEGORY_META[d]
            cats.append({"dir": d, "icon": icon, "title": title, "desc": desc, "w": w})
        else:
            # 自動推斷：regions_json_XXX → XXX 純 IP
            suffix = d[len("regions_json_"):] if d.startswith("regions_json_") else ""
            if suffix in PORT_TITLES:
                title = f"🔒 {PORT_TITLES[suffix]} 純 IP"
                desc = f"只保留 {PORT_TITLES[suffix]} 端口，格式 ip#國家"
            else:
                title = f"📁 {suffix or d}"
                desc = "自動偵測嘅分類"
            extra.append({"dir": d, "icon": "🔹", "title": title, "desc": desc, "w": 100})
    cats.sort(key=lambda c: c["w"])
    extra.sort(key=lambda c: c["dir"])
    return cats + extra


def main():
    with open("stats.json", encoding="utf-8") as f:
        stats = json.load(f)
    cats = discover_categories()
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = (HEAD
            .replace("__REPO__", REPO)
            .replace("__BRANCH__", BRANCH)
            .replace("__CATS__", json.dumps(cats, ensure_ascii=False, indent=1))
            .replace("__STATS__", json.dumps(stats, ensure_ascii=False))
            .replace("__UPDATED__", updated))

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"✓ {OUT_FILE} 已生成（{len(cats)} 個分類, {len(html):,} bytes）")
    for c in cats:
        n = stats.get(c["dir"])
        total = sum(v if isinstance(v, int) else sum(v.values()) for v in (n or {}).values())
        print(f"   {c['icon']} {c['title']}: {total:,} 條")


if __name__ == "__main__":
    main()
