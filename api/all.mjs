// all.js — all.json 中轉（Vercel Edge Function，非 Cloudflare 機房）
// ============================================================
// 用途：同 deno_proxy.ts 一樣，繞過 Cloudflare 對雲端 IP 嘅封鎖。
// Vercel Edge 跑喺非 CF 機房（AWS/GCP）→ 可以正常攞到上游數據。
//
// 部署步驟（免費 hobby plan，5 分鐘）：
//   1. 開 https://vercel.com/new → 匯入你嘅 repo（或者用 CLI：npx vercel）
//   2. 確保 `api/all.js` 喺 repo（呢個檔）
//   3. Vercel → Project → Settings → Environment Variables
//      → 加 TOKEN = <隨機字串>（同 GitHub Secret PROXY_TOKEN 一致）
//   4. 部署後攞到 URL：https://<project>.vercel.app/api/all
//   5. GitHub repo → Settings → Variables → PROXY_URL = 該 URL
//
// 用法：GET /api/all + header "X-Auth-Token: <TOKEN>"
// ============================================================

export const config = { runtime: "edge" };

const UPSTREAM = "https://zip.cm.edu.kg/all.json";

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-US,en;q=0.9,zh-HK;q=0.8,zh;q=0.7",
  "Referer": "https://zip.cm.edu.kg/",
};

export default async function handler(req) {
  const token = process.env.TOKEN ?? "";

  if (!token || req.headers.get("x-auth-token") !== token) {
    return new Response("Forbidden", { status: 403 });
  }

  try {
    const r = await fetch(UPSTREAM, { headers: HEADERS });
    if (!r.ok) {
      return new Response(`upstream error: ${r.status}`, { status: 502 });
    }
    const body = await r.text();
    const t = body.trimStart();
    if (!t.startsWith("{") && !t.startsWith("[")) {
      return new Response("upstream returned non-JSON", { status: 502 });
    }
    return new Response(body, {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=1800",
        "X-Upstream-Status": String(r.status),
        "X-Upstream-Bytes": String(body.length),
      },
    });
  } catch (e) {
    return new Response(`proxy error: ${e.message}`, { status: 502 });
  }
}
