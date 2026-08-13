// Cloudflare Worker：代理 all.json（GitHub Actions 數據源）
// ============================================================
// 設定步驟：
//   1. Cloudflare Dashboard → Workers → 你嘅 Worker → Settings → Variables
//      → 加 TOKEN = <隨機秘密字串>（冇設定一律 403，fail closed）
//   2. Edit code → 刪晒預設代碼 → 貼呢段 → Deploy
//   3. GitHub repo → Settings → Secrets and variables → Actions
//      → Secret:   PROXY_TOKEN = <同一字串>
//      → Variable: PROXY_URL  = https://<你嘅worker>.workers.dev/all.json
// 使用：GET /all.json + header "X-Auth-Token: <TOKEN>"
// ============================================================

const EXPECTED_TOKEN = typeof TOKEN !== "undefined" ? TOKEN : "";

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

async function proxyAllJson() {
  try {
    const r = await fetch("https://zip.cm.edu.kg/all.json", {
      headers: { "User-Agent": "Mozilla/5.0" },
      cf: { cacheTtl: 1800 },
    });

    if (!r.ok) {
      return new Response("upstream error: " + r.status, { status: 502 });
    }

    return new Response(r.body, {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=1800",
      },
    });
  } catch (e) {
    return new Response("proxy error: " + e.message, { status: 502 });
  }
}
