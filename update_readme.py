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

def country_links(base_dir, readme_base):
    if not os.path.exists(base_dir):
        return ""
    countries = sorted(d for d in os.listdir(base_dir) if os.path.isdir(f"{base_dir}/{d}"))
    return " · ".join(f"[{c}]({readme_base}/{c}/README.md)" for c in countries)

def write_country_readmes(base_dir, depth_prefix, is_ip_only=False):
    if not os.path.exists(base_dir):
        return
    label = "（純 IP）" if is_ip_only else ""
    for country in sorted(os.listdir(base_dir)):
        country_path = f"{base_dir}/{country}"
        if not os.path.isdir(country_path):
            continue
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

**共 {total} 條** · [返回上層]({depth_prefix}README.md)

| 組織 | 條目數 | Raw URL |
|------|--------|---------|
{table}

---
*最後更新：{updated}*
"""
        with open(f"{country_path}/README.md", "w", encoding="utf-8") as f:
            f.write(content)

def write_port_readmes():
    if not os.path.exists("ports"):
        return
    port_dirs = sorted(str(p) for p in sorted(int(d) for d in os.listdir("ports") if os.path.isdir(f"ports/{d}")))

    for port in port_dirs:
        port_path = f"ports/{port}"
        countries = sorted(d for d in os.listdir(port_path) if os.path.isdir(f"{port_path}/{d}"))
        is_ip_only = (port == "443")

        # 寫每個 country README
        write_country_readmes(port_path, "../../", is_ip_only=is_ip_only)

        # 寫 port README
        country_links_str = " · ".join(
            f"[{c}]({BASE_BLOB}/ports/{port}/{c}/README.md)" for c in countries
        )
        total = sum(
            count_lines(f"{port_path}/{c}/{f}")
            for c in countries
            for f in os.listdir(f"{port_path}/{c}") if f.endswith(".txt")
        )
        content = f"""# Port {port}{'（純 IP）' if is_ip_only else ''}

**共 {total} 條** · [返回主頁](../../README.md)

{country_links_str}

---
*最後更新：{updated}*
"""
        with open(f"{port_path}/README.md", "w", encoding="utf-8") as f:
            f.write(content)

    # 寫 ports 總 README
    rows = []
    for port in port_dirs:
        port_path = f"ports/{port}"
        total = sum(
            count_lines(f"{port_path}/{c}/{f}")
            for c in os.listdir(port_path) if os.path.isdir(f"{port_path}/{c}")
            for f in os.listdir(f"{port_path}/{c}") if f.endswith(".txt")
        )
        rows.append(f"| [{port}]({BASE_BLOB}/ports/{port}/README.md) | {total} |")

    table = "\n".join(rows)
    content = f"""# 按 Port 分類

[返回主頁](../README.md)

| Port | 條目數 |
|------|--------|
{table}

---
*最後更新：{updated}*
"""
    with open("ports/README.md", "w", encoding="utf-8") as f:
        f.write(content)


# ── 主 README ──────────────────────────────────────────
def write_main_readme():
    links_all = country_links("regions_json", f"{BASE_BLOB}/regions_json")
    links_443 = country_links("regions_json_443", f"{BASE_BLOB}/regions_json_443")

    port_dirs = sorted(str(p) for p in sorted(int(d) for d in os.listdir("ports") if os.path.isdir(f"ports/{d}"))) if os.path.exists("ports") else []
    port_links = " · ".join(f"[{p}]({BASE_BLOB}/ports/{p}/README.md)" for p in port_dirs)

    content = f"""# IP List by Region

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並分類，每日更新 4 次。

---

## 📁 全部 Port（按國家 + 組織）

{links_all}

---

## 🔒 僅 443 Port（純 IP，按國家 + 組織）

{links_443}

---

## 🔌 按 Port 分類

{port_links}

---
*最後更新：{updated}*
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md updated")


write_main_readme()
write_country_readmes("regions_json", "../../", is_ip_only=False)
write_country_readmes("regions_json_443", "../../", is_ip_only=True)
write_port_readmes()
