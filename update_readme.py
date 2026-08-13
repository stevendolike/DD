#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_readme.py — 生成主 README.md、各目錄 README.md 及國家 README.md

結構：
- 主 README：精簡（分類總覽表格 + 文件結構）
- 目錄 README：每個分類目錄一個（國家列表 + 條數 + 檔案連結）
- 國家 README：組織列表（組織 | 條目數 | Raw URL）
"""
import os
import json
from datetime import datetime, timezone
from urllib.parse import quote

REPO   = os.environ.get("GITHUB_REPOSITORY", "stevendolike/DD")
BRANCH = "main"
BASE_RAW  = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
BASE_BLOB = f"https://github.com/{REPO}/blob/{BRANCH}"
updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

with open("stats.json", encoding="utf-8") as f:
    STATS = json.load(f)


def dir_total(base_dir):
    val = STATS.get(base_dir, {})
    if not val:
        return 0
    first = list(val.values())[0]
    if isinstance(first, dict):
        return sum(count for cs in val.values() for count in cs.values())
    return sum(val.values())


def get_country_dirs(base_dir):
    if not os.path.exists(base_dir):
        return []
    return sorted(d for d in os.listdir(base_dir) if os.path.isdir(f"{base_dir}/{d}"))


def country_count(base_dir, country):
    return sum(STATS.get(base_dir, {}).get(country, {}).values())


def get_port_dirs():
    dirs = []
    for d in os.listdir("."):
        if d.startswith("regions_json_") and os.path.isdir(d):
            port = d.replace("regions_json_", "")
            if port.isdigit():
                dirs.append((port, d))
    return sorted(dirs, key=lambda x: int(x[0]))


def write_country_readmes(base_dir, is_ip_only=False, has_443=True):
    """國家層 README：組織列表（組織 | 條目數 | Raw URL）"""
    if not os.path.exists(base_dir):
        return
    label = "（純 IP）" if is_ip_only else ""
    title_suffix = f" {label}" if label else ""
    for country in get_country_dirs(base_dir):
        country_path = f"{base_dir}/{country}"
        files = sorted(f for f in os.listdir(country_path)
                       if f.endswith(".txt") and f not in ("_all.txt", "_all_443.txt"))
        rows, total = [], 0
        for fname in files:
            count = STATS.get(base_dir, {}).get(country, {}).get(fname[:-4], 0)
            total += count
            raw_url = f"{BASE_RAW}/{base_dir}/{country}/{quote(fname)}"
            rows.append(f"| {fname[:-4]} | {count:,} | [raw]({raw_url}) |")
        table = "\n".join(rows) if rows else "_（無數據）_"

        all_url = f"{BASE_RAW}/{base_dir}/{country}/_all.txt"
        combined = f"[📥 整合全部]({all_url})"
        if has_443:
            combined += f" · [🔒 整合 443 純 IP]({BASE_RAW}/{base_dir}/{country}/_all_443.txt)"

        content = f"""# {country}{title_suffix}

**共 {total:,} 條** · [返回主頁](../../README.md)

{combined}

| 組織 | 條目數 | Raw URL |
|------|--------|---------|
{table}

---
*最後更新：{updated}*
"""
        with open(f"{country_path}/README.md", "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    print(f"{base_dir} country READMEs updated")


def write_category_readme(base_dir, title, is_ip_only=False, has_443=True, is_flat=False):
    """目錄層 README：國家列表（國家 | 條目數 | 檔案連結）

    is_flat=True：國家檔直接喺目錄（優選 ASN / 家庭寬帶）
    is_flat=False：國家係子目錄（regions_json / port / clientip_v4）
    """
    if not os.path.exists(base_dir):
        return
    label = "（純 IP）" if is_ip_only else ""
    title_full = f"{title}{label}"

    if is_flat:
        files = sorted(f for f in os.listdir(base_dir)
                       if f.endswith(".txt") and f != "_all.txt")
        rows = []
        for fname in files:
            country = fname[:-4]
            count = STATS.get(base_dir, {}).get(country, 0)
            raw_url = f"{BASE_RAW}/{base_dir}/{quote(fname)}"
            rows.append(f"| {country} | {count:,} | [raw]({raw_url}) |")
        total = sum(STATS.get(base_dir, {}).values())
        header = "| 國家 | 條目數 | Raw URL |\n|------|--------|---------|\n"
        all_url = f"{BASE_RAW}/{base_dir}/_all.txt"
        back = "../README.md"
    else:
        rows = []
        for c in get_country_dirs(base_dir):
            count = country_count(base_dir, c)
            links = f"[列表]({BASE_BLOB}/{base_dir}/{c}/README.md)"
            links += f" · [all]({BASE_RAW}/{base_dir}/{c}/_all.txt)"
            if has_443:
                links += f" · [443]({BASE_RAW}/{base_dir}/{c}/_all_443.txt)"
            rows.append(f"| {c} | {count:,} | {links} |")
        total = dir_total(base_dir)
        header = "| 國家 | 條目數 | 檔案 |\n|------|--------|------|\n"
        all_url = f"{BASE_RAW}/{base_dir}/_all.txt"
        back = "../README.md"

    table = "\n".join(rows) if rows else "_（無數據）_"

    content = f"""# {title_full}

**共 {total:,} 條** · [返回主頁]({back})

📥 [整合全部]({all_url})

{header}{table}

---
*最後更新：{updated}*
"""
    with open(f"{base_dir}/README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"{base_dir}/README.md updated")


def write_main_readme():
    total_all = dir_total("regions_json")
    total_asn = dir_total("regions_json_preferred_asn")
    total_res = dir_total("regions_json_residential")
    total_v4 = dir_total("regions_json_clientip_v4")

    port_rows = []
    for port, base_dir in get_port_dirs():
        port_rows.append(
            f"| 🔒 Port {port} 純 IP | {dir_total(base_dir):,} | "
            f"[國家列表]({base_dir}/README.md) |"
        )
    ports_block = "\n".join(port_rows) if port_rows else "_（無數據）_"

    content = f"""# IP List by Region

> 💡 用 `Ctrl+F` 搜尋國家代碼

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並分類，每日更新 4 次。

---

## 📋 目錄

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
| `reformat.py` | 工具：一次性重整全庫格式（檔名/排序/LF） |
| `worker_proxy.js` | Cloudflare Worker：all.json 代理（GitHub Actions 唯一數據源） |

---

## 📁 分類總覽

| 分類 | 條數 | 明細 |
|------|------|------|
| 📁 全部 Port | {total_all:,} | [國家列表](regions_json/README.md) |
{ports_block}
| ⭐ 優選 ASN | {total_asn:,} | [列表](regions_json_preferred_asn/README.md) · [整合全部（ip:port#國家）]({BASE_RAW}/regions_json_preferred_asn/_all.txt) · [443 目錄](regions_json_preferred_asn_443/README.md) |
| 🏠 家庭寬帶 | {total_res:,} | [列表](regions_json_residential/README.md) · [整合全部（ip:port#國家）]({BASE_RAW}/regions_json_residential/_all.txt) · [443 目錄](regions_json_residential_443/README.md) |
| 🌐 ClientIP 為 IPv4 | {total_v4:,} | [國家列表](regions_json_clientip_v4/README.md) |

---

## 🍴 Fork 後自動同步

Fork 之後 repo 內置 [Upstream Sync](.github/workflows/upstream-sync.yml)：每日 00:00 自動同步上游改動（或者 Actions → Upstream Sync → Run workflow 手動同步）。

如果 GitHub 因 workflow 變更暫停自動更新，手動 Run 一次即可。

---
*最後更新：{updated}*
"""
    with open("README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("README.md updated")


# ── 主 README ──
write_main_readme()

# ── 目錄 README（分類總覽）──
write_category_readme("regions_json", "全部 Port", is_ip_only=False, has_443=True, is_flat=False)
for port, base_dir in get_port_dirs():
    write_category_readme(base_dir, f"Port {port} 純 IP", is_ip_only=True, has_443=False, is_flat=False)
write_category_readme("regions_json_clientip_v4", "ClientIP 為 IPv4", is_ip_only=False, has_443=True, is_flat=False)
write_category_readme("regions_json_preferred_asn", "優選 ASN（全部 Port）", is_ip_only=False, has_443=False, is_flat=True)
write_category_readme("regions_json_preferred_asn_443", "優選 ASN 443 純 IP", is_ip_only=True, has_443=False, is_flat=True)
write_category_readme("regions_json_residential", "家庭寬帶（全部 Port）", is_ip_only=False, has_443=False, is_flat=True)
write_category_readme("regions_json_residential_443", "家庭寬帶 443 純 IP", is_ip_only=True, has_443=False, is_flat=True)

# ── 國家 README（組織列表）──
write_country_readmes("regions_json", is_ip_only=False, has_443=True)
for port, base_dir in get_port_dirs():
    write_country_readmes(base_dir, is_ip_only=True, has_443=False)
write_country_readmes("regions_json_clientip_v4", is_ip_only=False, has_443=True)
