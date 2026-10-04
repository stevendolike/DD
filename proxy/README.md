# proxy/ — 上游數據中轉（繞過 Cloudflare 對雲端 IP 嘅封鎖）

## 為何需要

上游 `zip.cm.edu.kg/all.json` 喺 Cloudflare 後面，會擋「雲端 IP」：

| 來源 | 結果 | 原因 |
|------|------|------|
| 住宅 / 普通 ISP IP（本機） | ✅ 200 | — |
| **Cloudflare Worker** | ❌ 403 | 上游 Bot Fight Mode 擋 CF-to-CF subrequest |
| **GitHub Actions**（Azure runner） | ❌ 403 / CF 挑戰頁 | 上游唔信任雲端 IP |
| yx1/2/3.rjj.cc.cd | ❌ CF 挑戰頁 | 呢啲 proxy 自己都喺 Cloudflare 後面 |
| 公共 CORS proxy（allorigins 等） | ❌ 5xx/403/截斷 | 唔穩定 |
| **Deno Deploy**（GCP，非 CF） | ✅ **200** | **已驗證可行** ✓ |

→ **要一個非 Cloudflare 機房嘅中轉**，Actions 先攞得到數據。

## 現況（2026-10）

| 方案 | 狀態 |
|------|------|
| **A. Deno Deploy**（`deno_proxy.ts`） | ✅ **已部署並接入** — GitHub vars `PROXY_URL` + secrets `PROXY_TOKEN`；`split.yml` 每 6 小時自動更新成功 |
| B. Vercel Edge Function（`api/all.mjs`） | 🟡 已寫好，備用（未部署） |
| C. Cloudflare Worker（`worker_proxy.js`） | ❌ 現時唔可用（上游擋 CF），保留以備換上游 |

## 部署步驟（如需重做／改設定）

### A. Deno Deploy（`deno_proxy.ts`）— 現用

1. 開 https://dash.deno.com/ → GitHub 登入
2. New Playground → 貼 `deno_proxy.ts` 全文 → **Save & Deploy**
3. Settings → Environment Variables → 加 `TOKEN` = 隨機字串
4. 攞到 URL（`https://<project>.deno.dev/all.json`）
5. GitHub repo → Settings → Variables → `PROXY_URL` 改成呢個 URL
   （Secret `PROXY_TOKEN` 改成同一個 TOKEN 值）
6. **改完 code 要重新 Save & Deploy**（Playground 唔會自動同步 repo）

### B. Vercel Edge Function（`api/all.mjs`）

1. 開 https://vercel.com/new → 匯入呢個 repo（或者 `npx vercel`）
2. Vercel → Settings → Environment Variables → 加 `TOKEN`
3. 部署後 URL 係 `https://<project>.vercel.app/api/all`
4. 同樣改 GitHub 嘅 `PROXY_URL` + `PROXY_TOKEN`

## 驗證部署成功

```bash
# ① 帶 token → 期望 200 + 約 10,400,000 bytes
curl -s -H "X-Auth-Token: <你嘅 TOKEN>" \
  -o /tmp/probe.json -w "HTTP %{http_code} · %{size_download}B\n" \
  https://<你嘅 proxy URL>
head -c 80 /tmp/probe.json   # 應見到 {"generated_at": ...

# ② 冇 token → 期望 403
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://<你嘅 proxy URL>
```

成功之後，去 GitHub → Actions → Split by Region → **Run workflow**，
run 應該由 failure 變 success，`all.json` 亦會自動更新。

## 安全性

- `X-Auth-Token` 驗證（TOKEN 存喺 Deno 環境變數 + GitHub secret，唔入 repo）
- **所有回應 `Cache-Control: no-store`** — 唔經 CDN cache，確保驗證每次執行
  （避免「帶 token 嘅請求 cache 咗，冇 token 嘅請求食 cache 返 200」）
- Method 限 GET / HEAD；非 `/all.json` 回 404
- 上游回應會做 JSON 驗證，非 JSON 回 502

## 為何唔用 Cloudflare Worker

`worker_proxy.js` 仍保留（如果你之後換上游、或者上游解除封鎖就用得着），
但**現時上游會擋 CF Worker**，所以唔可以單靠佢。
