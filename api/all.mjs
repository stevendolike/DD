// all.js — all.json 中轉（Vercel Edge Function，非 Cloudflare 機房）
// ============================================================
// 用途：同 deno_proxy.ts 一樣，繞過 Cloudflare 對雲端 IP 嘅封鎖。
// Vercel Edge 跑喺非 CF 機房（AWS/GCP）→ 可以正常攞到上游數據。
//
// 部署步驟（免費 hobby plan）：
//   CLI：npx vercel login → npx vercel --prod
//   或：https://vercel.com/new 匯入含 api/ 嘅 repo
//   然後 Vercel → Project → Settings → Environment Variables → TOKEN = <隨機字串>
//   部署後 URL：https://<project>.vercel.app/api/all
//   GitHub repo → Settings → Variables → PROXY_URL = 該 URL
//   （Secret PROXY_TOKEN = 同一個 TOKEN 值）
//
// 用法：GET /api/all + header "X-Auth-Token: <TOKEN>"
//
// 安全：所有回應一律 no-store（唔經 CDN cache）→ 確保驗證每次執行，
//       避免「帶 token 嘅請求 cache 咗，冇 token 嘅請求食 cache 返 200」。
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

// 一律唔 cache（連錯誤回應都唔好 cache）— 確保 auth 每次執行
const NO_STORE = { "Cache-Control": "no-store" };

function jsonResponse(body, upstream) {
  return new Response(body, {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "X-Upstream-Status": String(upstream.status),
      "X-Upstream-Bytes": String(body.length),
    },
  });
}

export default async function handler(req) {
  const token = process.env.TOKEN ?? "";

  if (req.method !== "GET" && req.method !== "HEAD") {
    return new Response("Method Not Allowed", { status: 405, headers: NO_STORE });
  }
  if (!token || req.headers.get("x-auth-token") !== token) {
    return new Response("Forbidden", { status: 403, headers: NO_STORE });
  }

  try {
    const r = await fetch(UPSTREAM, { headers: HEADERS });
    if (!r.ok) {
      return new Response(`upstream error: ${r.status}`, { status: 502, headers: NO_STORE });
    }
    const body = await r.text();
    const t = body.trimStart();
    if (!t.startsWith("{") && !t.startsWith("[")) {
      return new Response("upstream returned non-JSON", { status: 502, headers: NO_STORE });
    }
    return jsonResponse(body, r);
  } catch (e) {
    return new Response(`proxy error: ${e.message}`, { status: 502, headers: NO_STORE });
  }
}
