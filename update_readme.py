import os
from datetime import datetime, timezone
from urllib.parse import quote

REPO = os.environ.get("GITHUB_REPOSITORY", "your-username/your-repo")
BRANCH = "main"
BASE_RAW  = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
BASE_BLOB = f"https://github.com/{REPO}/blob/{BRANCH}"

updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def count_lines(filepath):
    return sum(1 for line in open(filepath, encoding="utf-8") if line.strip())

def get_country_dirs(base_dir):
    if not os.path.exists(base_dir):
        return []
    return sorted(d for d in os.listdir(base_dir) if os.path.isdir(f"{base_dir}/{d}"))

def make_country_links(base_dir):
    countries = get_country_dirs(base_dir)
    return " · ".join(
        f"[{c}]({BASE_BLOB}/{base_dir}/{c}/README.md)" for c in countries
    )

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
            org = fname.replace(".txt", "")
            count = count_lines(f"{country_path}/{fname}")
            total += count
            raw_url = f"{BASE_RAW}/{base_dir}/{country}/{quote(fname)}"
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

def get_port_dirs():
    dirs = []
    for d in os.listdir("."):
        if d.startswith("regions_json_") and os.path.isdir(d):
            port = d.replace("regions_json_", "")
            dirs.append((port, d))
    return sorted(dirs, key=lambda x: int(x[0]) if x[0].isdigit() else 9999)

def write_main_readme():
    # 全部 port 區塊
    links_all = make_country_links("regions_json")

    # 每個 port 純 IP 區塊
    port_sections = ""
    for port, base_dir in get_port_dirs():
        links = make_country_links(base_dir)
        total = sum(
            count_lines(f"{base_dir}/{c}/{f}")
            for c in get_country_dirs(base_dir)
            for f in os.listdir(f"{base_dir}/{c}") if f.endswith(".txt")
        )
        port_sections += f"""
## 🔒 Port {port} 純 IP（按國家 + 組織）

**共 {total} 條**

{links}

---
"""

    content = f"""# IP List by Region

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並分類，每日更新 4 次。

---

## 📁 全部 Port（按國家 + 組織）

{links_all}

---
{port_sections}
*最後更新：{updated}*
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md updated")


# 執行
write_main_readme()
write_country_readmes("regions_json", is_ip_only=False)
for port, base_dir in get_port_dirs():
    write_country_readmes(base_dir, is_ip_only=True)
