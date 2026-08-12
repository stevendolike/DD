#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_readme.py — 生成主 README.md 及各國家 README.md

統一格式：
- 主 README：每個分類用表格（國家 | 條目數 | 檔案連結），唔再一行塞晒
- 國家 README：標題無 trailing space，表格排序
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
    """該國家所有組織條目總數。"""
    return sum(STATS.get(base_dir, {}).get(country, {}).values())


def make_country_table(base_dir, has_443=True):
    """國家表格：| 國家 | 條目數 | all | 443(可選) |"""
    countries = get_country_dirs(base_dir)
    if not countries:
        return "_（無數據）_"
    rows = []
    for c in countries:
        count = country_count(base_dir, c)
        all_url = f"{BASE_RAW}/{base_dir}/{c}/_all.txt"
        links = f"[all]({all_url})"
        if has_443:
            links += f" · [443]({BASE_RAW}/{base_dir}/{c}/_all_443.txt)"
        rows.append(f"| {c} | {count:,} | {links} |")
    return "| 國家 | 條目數 | 檔案 |\n|------|--------|------|\n" + "\n".join(rows)


def get_port_dirs():
    dirs = []
    for d in os.listdir("."):
        if d.startswith("regions_json_") and os.path.isdir(d):
            port = d.replace("regions_json_", "")
            if port.isdigit():
                dirs.append((port, d))
    return sorted(dirs, key=lambda x: int(x[0]))


def write_country_readmes(base_dir, is_ip_only=False, has_443=True):
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


def build_asn_table(base_dir):
    if not os.path.exists(base_dir):
        return "_（無數據）_"
    files = sorted(f for f in os.listdir(base_dir)
                   if f.endswith(".txt") and f != "_all.txt")
    rows = []
    for fname in files:
        country = fname[:-4]
        count = STATS.get(base_dir, {}).get(country, 0)
        raw_url = f"{BASE_RAW}/{base_dir}/{quote(fname)}"
        rows.append(f"| {country} | {count:,} | [raw]({raw_url}) |")
    return "| 國家 | 條目數 | Raw URL |\n|------|--------|---------|\n" + (
        "\n".join(rows) if rows else "_（無數據）_")


def write_main_readme():
    total_all = dir_total("regions_json")
    total_asn = dir_total("regions_json_preferred_asn")
    total_asn_443 = dir_total("regions_json_preferred_asn_443")
    total_v4 = dir_total("regions_json_clientip_v4")
    total_res = dir_total("regions_json_residential")
    total_res_443 = dir_total("regions_json_residential_443")

    table_all = make_country_table("regions_json", has_443=True)
    table_v4 = make_country_table("regions_json_clientip_v4", has_443=True)
    table_asn = build_asn_table("regions_json_preferred_asn")
    table_asn_443 = build_asn_table("regions_json_preferred_asn_443")
    table_res = build_asn_table("regions_json_residential")
    table_res_443 = build_asn_table("regions_json_residential_443")

    port_sections = []
    for port, base_dir in get_port_dirs():
        table = make_country_table(base_dir, has_443=False)
        total = dir_total(base_dir)
        port_sections.append(
            f"### 🔒 Port {port}\n\n**共 {total:,} 條**\n\n{table}"
        )
    ports_block = "\n\n---\n\n".join(port_sections) if port_sections else "_（無數據）_"

    content = f"""# IP List by Region

> 💡 用 `Ctrl+F` 搜尋國家代碼

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並分類，每日更新 4 次。

---

## 📋 目錄

- [📁 全部 Port](#-全部-port)
- [🔒 各 Port 純 IP](#-各-port-純-ip)
- [⭐ 優選 ASN](#-優選-asn)
- [🏠 家庭寬帶](#-家庭寬帶)
- [🌐 ClientIP 為 IPv4](#-clientip-為-ipv4)
- [📂 文件結構](#-文件結構)

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

## 📁 全部 Port

**共 {total_all:,} 條**

{table_all}

---

## 🔒 各 Port 純 IP

{ports_block}

---

## ⭐ 優選 ASN

### 全部 Port（共 {total_asn:,} 條）

📥 [整合全部（ip:port#國家）]({BASE_RAW}/regions_json_preferred_asn/_all.txt)

{table_asn}

### 443 純 IP（共 {total_asn_443:,} 條）

📥 [整合全部]({BASE_RAW}/regions_json_preferred_asn_443/_all.txt)

{table_asn_443}

---

## 🏠 家庭寬帶

### 全部 Port（共 {total_res:,} 條）

📥 [整合全部（ip:port#國家）]({BASE_RAW}/regions_json_residential/_all.txt)

{table_res}

### 443 純 IP（共 {total_res_443:,} 條）

📥 [整合全部]({BASE_RAW}/regions_json_residential_443/_all.txt)

{table_res_443}

---

## 🌐 ClientIP 為 IPv4

**共 {total_v4:,} 條**

{table_v4}

---
*最後更新：{updated}*
"""
    with open("README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("README.md updated")


write_main_readme()
write_country_readmes("regions_json", is_ip_only=False, has_443=True)
for port, base_dir in get_port_dirs():
    write_country_readmes(base_dir, is_ip_only=True, has_443=False)
write_country_readmes("regions_json_clientip_v4", is_ip_only=False, has_443=True)
