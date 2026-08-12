// worker_proxy.js — Cloudflare Worker：代理 zip.cm.edu.kg/all.json
// ============================================================
// 格式：Service Worker 格式（addEventListener）— dashboard 舊版/新版都支援
// 用途：GitHub Actions 唯一數據源（zip.cm.edu.kg 喺 Actions 環境 403）
// 安全：X-Auth-Token header 驗證（token 喺環境變量，唔寫死喺代碼）
// 部署後網址: https://proxy-cm-json.[REDACTED]/all.json
//
// ⚠️ 設定（重要）：
//   Cloudflare dashboard → Workers → proxy-cm-json →
//   Settings → Variables → Add variable:
//     Variable name:  TOKEN
//     Value:          <你自己嘅秘密字串，例如 32 位隨機>
//   之後再 Edit code 貼呢段代碼 → Deploy
//
//   GitHub repo → Settings → Secrets and variables → Actions →
//   New repository secret:
//     Name:  PROXY_TOKEN
//     Value: <同一字串>
//
// 冇設定 TOKEN 環境變量 → 一律 403（fail closed，安全）
// ============================================================

const EXPECTED_TOKEN = typeof TOKEN !== "undefined" ? TOKEN : "";

addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // 只代理 all.json，其他路徑一律 404
  if (url.pathname !== "/all.json") {
    event.respondWith(new Response("Not Found", { status: 404 }));
    return;
  }

  // Token 驗證：冇設定 token 或冇帶正確 token → 403
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
      cf: { cacheTtl: 1800 },   // Cloudflare 邊緣快取 30 分鐘，減少上游請求
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
