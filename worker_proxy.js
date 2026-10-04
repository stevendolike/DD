// Cloudflare Worker：代理 all.json（GitHub Actions 數據源）
// ============================================================
// 設定步驟：
//   1. Cloudflare Dashboard → Workers → 你嘅 Worker → Settings → Variables
//      → 加 TOKEN = <隨機秘密字串>（冇設定一律 403，fail closed）
//   2. Edit code → 刪晒預設代碼 → 貼呢段 → Deploy
//   3. GitHub repo → Settings → Secrets and variables → Actions
//      → Secret:   PROXY_TOKEN = <同一字串>
//      → Variable: PROXY_URL  = https://<你嘅worker>.workers.dev/all.json
// 使用：GET /all.json + header "X-Auth-Token: ***
// ============================================================
// 2026-10 修復：上游 zip.cm.edu.kg 喺 Cloudflare 後面，會對「Cloudflare
// Worker 嘅 subrequest」返 403（Bot Fight Mode / WAF 攔 CF-to-CF 請求）。
// 改為三層策略：
//   ① 完整瀏覽器 headers（似真 Chrome）
//   ② 簡化 headers（只 UA + Referer）
//   ③ 經非 Cloudflare 機房嘅公共 CORS proxy 中轉
// 回應會帶 X-Upstream-Status / X-Fetch-Strategy 方便診斷。
// ============================================================

const EXPECTED_TOKEN = typeof TOKEN !== "undefined" ? TOKEN : "";
const UPSTREAM = "https://zip.cm.edu.kg/all.json";

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
           "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

// ① 完整瀏覽器 headers
const FULL_HEADERS = {
  "User-Agent": UA,
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-US,en;q=0.9,zh-HK;q=0.8,zh;q=0.7",
  "Referer": "https://zip.cm.edu.kg/",
  "Origin": "https://zip.cm.edu.kg",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
  "Sec-Ch-Ua-Mobile": "?0",
  "Sec-Ch-Ua-Platform": '"Windows"',
  "Cache-Control": "no-cache",
  "Pragma": "no-cache",
};

// ② 簡化 headers
const MINIMAL_HEADERS = {
  "User-Agent": UA,
  "Referer": "https://zip.cm.edu.kg/",
};

// ③ 非 Cloudflare 機房嘅公共中轉（最後防線，不穩定 — 時段性會 5xx/403）
//    實測 2026-10：allorigins/jina/codetabs 等都試過得，但同一日亦會死。
//    只用嚟「搏一搏」，唔應該視為可靠路徑。
const PROXY_BUILDERS = [
  (u) => "https://api.allorigins.win/raw?url=" + encodeURIComponent(u),
  (u) => "https://api.codetabs.com/v1/proxy?quest=" + encodeURIComponent(u),
  (u) => "https://r.jina.ai/" + u,
];

addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  if (url.pathname !== "/all.json") {
    event.respondWith(new Response("Not Found", { status: 404 }));
    return;
  }

  if (!EXPECTED_TOKEN || event.request.headers.get("X-Auth-Token") !== EXPECTED_TOKEN) {
    event.respondWith(new Response("Forbidden", { status: 403 }));
    return;
  }

  event.respondWith(proxyAllJson());
});

function looksLikeJson(text) {
  const t = (text || "").trimStart();
  return t.startsWith("{") || t.startsWith("[");
}

async function tryFetch(label, target, init) {
  try {
    const r = await fetch(target, init);
    const body = await r.text();
    if (r.ok && looksLikeJson(body)) {
      return { ok: true, label, status: r.status, body };
    }
    return { ok: false, label, status: r.status, body: body.slice(0, 200) };
  } catch (e) {
    return { ok: false, label, status: 0, body: "throw: " + e.message };
  }
}

async function proxyAllJson() {
  const attempts = [
    ["full-headers", UPSTREAM, {
      headers: FULL_HEADERS,
      cf: { cacheTtl: 1800, cacheEverything: true },
    }],
    ["minimal-headers", UPSTREAM, {
      headers: MINIMAL_HEADERS,
      cf: { cacheTtl: 1800 },
    }],
  ];
  // ③ 逐個公共中轉試（最後防線）
  for (const build of PROXY_BUILDERS) {
    attempts.push(["proxy:" + new URL(build(UPSTREAM)).hostname,
                   build(UPSTREAM),
                   { headers: { "User-Agent": UA }, cf: { cacheTtl: 1800 } }]);
  }

  const log = [];
  for (const [label, target, init] of attempts) {
    const res = await tryFetch(label, target, init);
    log.push(`${label}:${res.status}`);
    if (res.ok) {
      return new Response(res.body, {
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Cache-Control": "public, max-age=1800",
          "X-Fetch-Strategy": label,
          "X-Upstream-Status": String(res.status),
          "X-Attempts": log.join(","),
        },
      });
    }
  }

  // 全部失敗
  return new Response(
    JSON.stringify({ error: "all upstream attempts failed", attempts: log }),
    {
      status: 502,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "X-Attempts": log.join(","),
      },
    }
  );
}
