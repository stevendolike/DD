// deno_proxy.ts — all.json 中轉（Deno Deploy，非 Cloudflare 機房）
// ============================================================
// 為何需要：上游 zip.cm.edu.kg 喺 Cloudflare 後面，會擋「雲端 IP」請求
//   · Cloudflare Worker（CF-to-CF）→ 403
//   · GitHub Actions（Azure）→ CF 挑戰頁
//   · 只有住宅 / 普通 ISP IP 攞得到 200
// Deno Deploy 喺 GCP（非 CF）機房 → 可以正常攞到上游數據。（已驗證 2026-10 ✓）
//
// 部署步驟（免費，5 分鐘）：
//   1. 開 https://dash.deno.com/ → 用 GitHub 登入
//   2. New Project → Deploy from Playground（或連結一個 repo）
//   3. 貼呢段代碼 → Deploy
//   4. Settings → Environment Variables → 加 TOKEN = <隨機字串>
//   5. 攞到 URL（例如 https://xxx.deno.dev/all.json）
//   6. GitHub repo → Settings → Variables → 改 PROXY_URL = 該 URL
//      （Secret PROXY_TOKEN 改成同一個 TOKEN 值）
//
// 用法：GET /all.json + header "X-Auth-Token: <TOKEN>"
//
// 安全：所有回應一律 no-store（唔經 CDN cache）→ 確保驗證每次執行，
//       避免「帶 token 嘅請求 cache 咗，冇 token 嘅請求食 cache 返 200」。
// ============================================================

const UPSTREAM = "https://zip.cm.edu.kg/all.json";
const TOKEN = Deno.env.get("TOKEN") ?? "";

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-US,en;q=0.9,zh-HK;q=0.8,zh;q=0.7",
  "Referer": "https://zip.cm.edu.kg/",
};

// 一律唔 cache（連錯誤回應都唔好 cache）— 確保 auth 每次執行
const NO_STORE: HeadersInit = { "Cache-Control": "no-store" };

function jsonResponse(body: string, upstream: Response): Response {
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

Deno.serve(async (req: Request): Promise<Response> => {
  const url = new URL(req.url);

  if (req.method !== "GET" && req.method !== "HEAD") {
    return new Response("Method Not Allowed", { status: 405, headers: NO_STORE });
  }
  if (url.pathname !== "/all.json") {
    return new Response("Not Found", { status: 404, headers: NO_STORE });
  }
  if (!TOKEN || req.headers.get("X-Auth-Token") !== TOKEN) {
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
    return new Response(`proxy error: ${(e as Error).message}`, { status: 502, headers: NO_STORE });
  }
});
