# IP List by Region

> 💡 用 `Ctrl+F` 搜尋國家代碼

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並分類，每日更新 4 次。

---

## 📋 目錄

- [🌐 網站（GitHub Pages）](#-網站github-pages)
- [📂 文件結構](#-文件結構)
- [📁 分類總覽](#-分類總覽)

---

## 📂 文件結構

| 檔案 | 用途 |
|------|------|
| `split_json.py` | 主程式：all.json → 按國家/組織/port 拆分（Actions 自動跑） |
| `update_readme.py` | 生成 README（Actions 自動跑） |
| `validate.py` | 驗證下載嘅 all_new.json 有效性（Actions 自動跑） |
| `asns.py` | **優選 ASN 清單**（中國優化線路，想調整改呢個） |
| `residential.py` | **家庭寬帶 ISP 關鍵字**（想調整改呢個） |
| `reclassify_asn.py` | 工具：數據源失效時用 RIPEstat 重建優選 ASN |
| `classify_residential.py` | 工具：重新生成家庭寬帶分類 |
| `gen_pages.py` | 生成 GitHub Pages 網站（Actions 自動跑） |
| `reformat.py` | 工具：一次性重整全庫格式（檔名/排序/LF） |
| `worker_proxy.js` | Cloudflare Worker：all.json 代理（GitHub Actions 唯一數據源） |

---

## 📁 分類總覽

| 分類 | 條數 | 明細 |
|------|------|------|
| 📁 全部 Port | 14,085 | [國家列表](regions_json/README.md) |
| 🔒 Port 443 純 IP | 8,018 | [國家列表](regions_json_443/README.md) |
| 🔒 Port 2053 純 IP | 1,348 | [國家列表](regions_json_2053/README.md) |
| 🔒 Port 2083 純 IP | 559 | [國家列表](regions_json_2083/README.md) |
| 🔒 Port 2087 純 IP | 547 | [國家列表](regions_json_2087/README.md) |
| 🔒 Port 2096 純 IP | 495 | [國家列表](regions_json_2096/README.md) |
| 🔒 Port 8443 純 IP | 3,118 | [國家列表](regions_json_8443/README.md) |
| ⭐ 優選 ASN | 189 | [列表](regions_json_preferred_asn/README.md) · [整合全部（ip:port#國家）](https://raw.githubusercontent.com/stevendolike/DD/main/regions_json_preferred_asn/_all.txt) · [443 目錄](regions_json_preferred_asn_443/README.md) |
| 🏠 家庭寬帶 | 82 | [列表](regions_json_residential/README.md) · [整合全部（ip:port#國家）](https://raw.githubusercontent.com/stevendolike/DD/main/regions_json_residential/_all.txt) · [443 目錄](regions_json_residential_443/README.md) |
| 🌐 ClientIP 為 IPv4 | 3,791 | [國家列表](regions_json_clientip_v4/README.md) |

---

## 🌐 網站（GitHub Pages）

本 repo 內置靜態網站（`docs/` 目錄，由 `gen_pages.py` 自動生成，隨 Actions 每 6 小時同步）：

**網址：** https://stevendolike.github.io/DD/

- 📱 響應式：320px 手機 → 桌面自動縮放（`clamp()` 流體排版 + `flex-wrap`）
- 🌙 深色主題 · 劉海屏安全區（`env(safe-area-inset-*)` + `viewport-fit=cover`）
- 🔍 搜尋 IP／國家、一鍵複製清單、每個分類嘅 raw 連結
- 🗂️ 12 個分類：優選 ASN、家庭寬帶、全部 Port、各 port 純 IP、ClientIP v4

**啟用方法（只做一次）**：Settings → Pages → Source 揀 **Deploy from a branch** → Branch 揀 **main** + 目錄揀 **/docs** → Save。Fork 嘅話一樣做法，網址自動變你嘅 `stevendolike.github.io/DD/`。

---

## 🍴 Fork 後自動同步

Fork 之後 repo 內置 [Upstream Sync](.github/workflows/upstream-sync.yml)：每日 00:00 自動同步上游改動（或者 Actions → Upstream Sync → Run workflow 手動同步）。

如果 GitHub 因 workflow 變更暫停自動更新，手動 Run 一次即可。

---
*最後更新：2026-10-09 16:55 UTC*
