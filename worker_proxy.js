// worker_proxy.js — Cloudflare Worker：代理 zip.cm.edu.kg/all.json
// ============================================================
// 格式：Service Worker 格式（addEventListener）— dashboard 舊版/新版都支援
// 用途：GitHub Actions 唯一數據源（zip.cm.edu.kg 喺 Actions 環境 403）
// 安全：X-Auth-Token header 驗證 — 冇正確 token 一律 403
//       部署後網址: https://proxy-cm-json.[REDACTED]/all.json
//
// ⚠️ 部署前必改：將下方 TOKEN 換成你自己嘅秘密字串（例如 32 位隨機）
//    然後喺 GitHub repo Settings → Secrets → Actions 加 PROXY_TOKEN（同一值）
//
// 部署方法（dashboard）:
//   1. dashboard.cloudflare.com → Workers & Pages → 揀 proxy-cm-json → Edit code
//   2. 改 TOKEN 值 → 貼上呢段 → Deploy
// ============================================================

const TOKEN = "CHANGE_ME_TO_A_LONG_RANDOM_STRING";

addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // 只代理 all.json，其他路徑一律 404
  if (url.pathname !== "/all.json") {
    event.respondWith(new Response("Not Found", { status: 404 }));
    return;
  }

  // Token 驗證：冇正確 token 一律 403
  if (event.request.headers.get("X-Auth-Token") !== TOKEN) {
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
