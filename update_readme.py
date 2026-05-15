import os
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "your-username/your-repo")
BRANCH = "main"
BASE_RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

def build_nested_table(base_dir):
    if not os.path.exists(base_dir):
        return "_（無數據）_"
    rows = []
    for country in sorted(os.listdir(base_dir)):
        country_path = f"{base_dir}/{country}"
        if not os.path.isdir(country_path):
            continue
        for fname in sorted(os.listdir(country_path)):
            if not fname.endswith(".txt"):
                continue
            org = fname.replace(".txt", "")
            count = sum(1 for line in open(f"{country_path}/{fname}", encoding="utf-8") if line.strip())
            raw_url = f"{BASE_RAW}/{base_dir}/{country}/{fname}"
            rows.append(f"| {country} | {org} | {count} | [raw]({raw_url}) |")
    return "\n".join(rows) if rows else "_（無數據）_"

table_json  = build_nested_table("regions_json")
table_j443  = build_nested_table("regions_json_443")
updated     = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

readme = f"""# IP List by Region

自動從 [all.json](https://zip.cm.edu.kg/all.json) 抓取並按地區 / 組織分類，每日更新 4 次。

## 按地區 + 組織（全部 Port）

| 國家 | 組織 | 條目數 | Raw URL |
|------|------|--------|---------|
{table_json}

## 按地區 + 組織（僅 443 Port，純 IP）

| 國家 | 組織 | 條目數 | Raw URL |
|------|------|--------|---------|
{table_j443}

---
*最後更新：{updated}*
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("README.md updated")
