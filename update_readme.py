import os
from datetime import datetime, timezone
from urllib.parse import quote

REPO = os.environ.get("GITHUB_REPOSITORY", "your-username/your-repo")
BRANCH = "main"
BASE_RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
BASE_BLOB = f"https://github.com/{REPO}/blob/{BRANCH}"

updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def count_lines(filepath):
    return sum(1 for line in open(filepath, encoding="utf-8") if line.strip())

# ── 主 README ──────────────────────────────────────────
def write_main_readme():
    countries_all  = sorted(d for d in os.listdir("regions_json") if os.path.isdir(f"regions_json/{d}")) if os.path.exists("regions_json") else []
    countries_443  = sorted(d for d in os.listdir("regions_json_443") if os.path.isdir(f"regions_json_443/{d}")) if os.path.exists("regions_json_443") else []
    port_files     = sorted(f for f in os.listdir("ports") if f.endswith(".txt")) if os.path.exists("ports") else []

    country_links_all = " · ".join(
        f"[{c}]({BASE_BLOB}/regions_json/{c}/README.md)" for c in countries_all
    )
    country_links_443 = " · ".join(
        f"[{c}]({BASE_BLOB}/regions_json_443/{c}/README.md)" for c in countries_443
    )
    port_links = " · ".join(
        f"[{p.replace('.txt','')}]({BASE_RAW}/ports/{p})" for p in port_files
    )

    content = f"""# IP List by Region

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並分類，每日更新 4 次。

---

## 📁 全部 Port（按國家 + 組織）

> 點擊國家代碼進入詳細列表

{country_links_all}

---

## 🔒 僅 443 Port（純 IP，按國家 + 組織）

> 點擊國家代碼進入詳細列表

{country_links_443}

---

## 🔌 按 Port 分類

{port_links}

| Port | 條目數 | Raw URL |
|------|--------|---------|
"""
    for p in port_files:
        port_num = p.replace(".txt", "")
        count = count_lines(f"ports/{p}")
        raw_url = f"{BASE_RAW}/ports/{quote(p)}"
        content += f"| {port_num} | {count} | [raw]({raw_url}) |\n"

    content += f"\n---\n*最後更新：{updated}*\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md updated")


# ── 國家 README ────────────────────────────────────────
def write_country_readme(base_dir, is_443=False):
    if not os.path.exists(base_dir):
        return
    label = "（純 IP）" if is_443 else ""
    for country in sorted(os.listdir(base_dir)):
        country_path = f"{base_dir}/{country}"
        if not os.path.isdir(country_path):
            continue
        files = sorted(f for f in os.listdir(country_path) if f.endswith(".txt"))
        rows = []
        for fname in files:
            org = fname.replace(".txt", "")
            count = count_lines(f"{country_path}/{fname}")
            raw_url = f"{BASE_RAW}/{base_dir}/{country}/{quote(fname)}"
            rows.append(f"| {org} | {count} | [raw]({raw_url}) |")

        table = "\n".join(rows) if rows else "_（無數據）_"
        total = sum(count_lines(f"{country_path}/{f}") for f in files)

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
        print(f"{country_path}/README.md updated")


# ── ports README ───────────────────────────────────────
def write_ports_readme():
    if not os.path.exists("ports"):
        return
    files = sorted(f for f in os.listdir("ports") if f.endswith(".txt"))
    rows = []
    for fname in files:
        port_num = fname.replace(".txt", "")
        count = count_lines(f"ports/{fname}")
        raw_url = f"{BASE_RAW}/ports/{quote(fname)}"
        rows.append(f"| {port_num} | {count} | [raw]({raw_url}) |")

    table = "\n".join(rows)
    content = f"""# 按 Port 分類

[返回主頁](../README.md)

| Port | 條目數 | Raw URL |
|------|--------|---------|
{table}

---
*最後更新：{updated}*
"""
    with open("ports/README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("ports/README.md updated")


write_main_readme()
write_country_readme("regions_json", is_443=False)
write_country_readme("regions_json_443", is_443=True)
write_ports_readme()
