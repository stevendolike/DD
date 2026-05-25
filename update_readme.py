import os
import json
from datetime import datetime, timezone
from urllib.parse import quote

REPO   = os.environ.get("GITHUB_REPOSITORY", "your-username/your-repo")
BRANCH = "main"
BASE_RAW  = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
BASE_BLOB = f"https://github.com/{REPO}/blob/{BRANCH}"
updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

with open("stats.json") as f:
    STATS = json.load(f)

def get_count(base_dir, country, org_file):
    org = org_file.replace(".txt", "")
    return STATS.get(base_dir, {}).get(country, {}).get(org, 0)

def dir_total(base_dir):
    val = STATS.get(base_dir, {})
    if not val:
        return 0
    first = list(val.values())[0]
    if isinstance(first, dict):
        return sum(count for country_stats in val.values() for count in country_stats.values())
    else:
        return sum(val.values())

def get_country_dirs(base_dir):
    if not os.path.exists(base_dir):
        return []
    return sorted(d for d in os.listdir(base_dir) if os.path.isdir(f"{base_dir}/{d}"))

def make_country_links(base_dir):
    countries = get_country_dirs(base_dir)
    return " · ".join(
        f"[{c}]({BASE_BLOB}/{base_dir}/{c}/README.md)" for c in countries
    )

def make_asn_country_links(base_dir):
    if not os.path.exists(base_dir):
        return ""
    files = sorted(f for f in os.listdir(base_dir) if f.endswith(".txt"))
    return " · ".join(
        f"[{f.replace('.txt','')}]({BASE_RAW}/{base_dir}/{quote(f)})" for f in files
    )

def get_port_dirs():
    dirs = []
    for d in os.listdir("."):
        if d.startswith("regions_json_") and os.path.isdir(d):
            port = d.replace("regions_json_", "")
            if port.isdigit():
                dirs.append((port, d))
    return sorted(dirs, key=lambda x: int(x[0]))

def write_country_readmes(base_dir, is_ip_only=True):
    if not os.path.exists(base_dir):
        return
    label = "（純 IP）" if is_ip_only else ""
    for country in get_country_dirs(base_dir):
        country_path = f"{base_dir}/{country}"
        files = sorted(f for f in os.listdir(country_path) if f.endswith(".txt"))
        rows = []
        total = 0
        for fname in files:
            count = get_count(base_dir, country, fname)
            total += count
            raw_url = f"{BASE_RAW}/{base_dir}/{country}/{quote(fname)}"
            org = fname.replace(".txt", "")
            rows.append(f"| {org} | {count} | [raw]({raw_url}) |")
        table = "\n".join(rows) if rows else "_（無數據）_"
        content = f"""# {country} {label}

**共 {total} 條** · [返回主頁](../../README.md)

| 組織 | 條目數 | Raw URL |
|------|--------|---------|
{table}

---
*最後更新：{updated}*
"""
        with open(f"{country_path}/README.md", "w", encoding="utf-8") as f:
            f.write(content)
    print(f"{base_dir} country READMEs updated")

def build_asn_table(base_dir):
    if not os.path.exists(base_dir):
        return "_（無數據）_"
    files = sorted(f for f in os.listdir(base_dir) if f.endswith(".txt"))
    rows = []
    for fname in files:
        country = fname.replace(".txt", "")
        count = STATS.get(base_dir, {}).get(country, 0)
        raw_url = f"{BASE_RAW}/{base_dir}/{quote(fname)}"
        rows.append(f"| {country} | {count} | [raw]({raw_url}) |")
    return "\n".join(rows) if rows else "_（無數據）_"

def write_main_readme():
    links_all     = make_country_links("regions_json")
    total_all     = dir_total("regions_json")
    total_asn     = dir_total("regions_json_preferred_asn")
    total_asn_443 = dir_total("regions_json_preferred_asn_443")
    table_asn     = build_asn_table("regions_json_preferred_asn")
    table_asn_443 = build_asn_table("regions_json_preferred_asn_443")

    port_sections = ""
    for port, base_dir in get_port_dirs():
        links = make_country_links(base_dir)
        total = dir_total(base_dir)
        port_sections += f"""
## 🔒 Port {port} 純 IP（按國家 + 組織）

**共 {total} 條**

{links}

---
"""

    content = f"""# IP List by Region

> 💡 用 `Ctrl+F` 搜尋國家代碼

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並分類，每日更新 4 次。

---

## 📁 全部 Port（按國家 + 組織）

**共 {total_all} 條**

{links_all}

---
{port_sections}
## ⭐ 優選 ASN（全部 Port）

**共 {total_asn} 條**

| 國家 | 條目數 | Raw URL |
|------|--------|---------|
{table_asn}

---

## ⭐ 優選 ASN（443 純 IP）

**共 {total_asn_443} 條**

| 國家 | 條目數 | Raw URL |
|------|--------|---------|
{table_asn_443}

---
*最後更新：{updated}*
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md updated")


write_main_readme()
write_country_readmes("regions_json", is_ip_only=False)
for port, base_dir in get_port_dirs():
    write_country_readmes(base_dir, is_ip_only=True)
