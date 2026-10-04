# proxy/ — 上游數據中轉（繞過 Cloudflare 對雲端 IP 嘅封鎖）

## 為何需要

上游 `zip.cm.edu.kg/all.json` 喺 Cloudflare 後面，會擋「雲端 IP」：

| 來源 | 結果 | 原因 |
|------|------|------|
| 住宅 / 普通 ISP IP（本機） | ✅ 200 | — |
| **Cloudflare Worker** | ❌ 403 | 上游 Bot Fight Mode 擋 CF-to-CF subrequest |
| **GitHub Actions**（Azure runner） | ❌ 403 / CF 挑戰頁 | 上游唔信任雲端 IP |
| yx1/2/3.rjj.cc.cd | ❌ CF 挑戰頁 | 呢啲 proxy 自己都喺 Cloudflare 後面 |
| 公共 CORS proxy（allorigins 等） | ❌ 5xx/403 | 唔穩定 |

→ **要一個非 Cloudflare 機房嘅中轉**，Actions 先攞得到數據。

## 兩個現成方案（二選一，都免費）

### A. Deno Deploy（`deno_proxy.ts`）

1. 開 https://dash.deno.com/ → GitHub 登入
2. New Project → Deploy from Playground
3. 貼 `deno_proxy.ts` 全文 → Deploy
4. Settings → Environment Variables → 加 `TOKEN` = 隨機字串
5. 攞到 URL（`https://xxx.deno.dev/all.json`）
6. GitHub repo → Settings → Variables → `PROXY_URL` 改成呢個 URL
   （Secret `PROXY_TOKEN` 改成同一個 TOKEN 值）

### B. Vercel Edge Function（`api/all.mjs`）

1. 開 https://vercel.com/new → 匯入呢個 repo（或者 `npx vercel`）
2. Vercel → Settings → Environment Variables → 加 `TOKEN`
3. 部署後 URL 係 `https://<project>.vercel.app/api/all`
4. 同樣改 GitHub 嘅 `PROXY_URL` + `PROXY_TOKEN`

## 驗證部署成功

```bash
curl -s -H "X-Auth-Token: <你嘅 TOKEN>" \
  -o /tmp/probe.json -w "HTTP %{http_code} · %{size_download}B\n" \
  https://<你嘅 proxy URL>
# 期望：HTTP 200 · 約 10,000,000 B
head -c 80 /tmp/probe.json   # 應見到 {"generated_at": ...
```

成功之後，去 GitHub → Actions → Split by Region → **Run workflow**，
run 應該由 failure 變 success，`all.json` 亦會自動更新。

## 為何唔用 Cloudflare Worker

`worker_proxy.js` 仍保留（如果你之後換上游、或者上游解除封鎖就用得着），
但**現時上游會擋 CF Worker**，所以唔可以單靠佢。
