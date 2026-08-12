// worker_proxy.js — Cloudflare Worker：代理 zip.cm.edu.kg/all.json
// ============================================================
// 用途：GitHub Actions 連唔到 zip.cm.edu.kg 官方源時，經呢個 Worker 攞數據
// 部署後網址: https://<你的子域>.workers.dev/all.json
//
// 部署方法（dashboard）:
//   1. dashboard.cloudflare.com → Workers & Pages → Create → Worker
//   2. 改名（例如 dd-proxy）→ Deploy
//   3. Edit code → 貼上呢段代碼 → Deploy
// 或者 (wrangler CLI):
//   npm i -g wrangler && wrangler login
//   wrangler deploy worker_proxy.js --name dd-proxy
//
// 部署完將網址填入 .github/workflows/split.yml 嘅 fallback 鏈
// ============================================================

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // 只代理 all.json，其他路徑一律 404
    if (url.pathname !== "/all.json") {
      return new Response("Not Found", { status: 404 });
    }

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
  },
};
