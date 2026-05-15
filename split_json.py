import json
import os
from collections import defaultdict

try:
    with open("all.json", "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        print("all.json 是空文件，跳過")
        exit(0)
    raw = json.loads(content)
    # 頂層是 dict，IP 數據在 data["data"]
    data = raw["data"] if isinstance(raw, dict) else raw
except (json.JSONDecodeError, KeyError) as e:
    print(f"all.json 解析失敗：{e}")
    exit(0)

groups = defaultdict(lambda: defaultdict(list))
groups_443 = defaultdict(lambda: defaultdict(list))

for item in data:
    ip = item.get("ip", "")
    ports = item.get("port", [])
    meta = item.get("meta", {})
    country = meta.get("country", "UNKNOWN").upper()
    org = meta.get("asOrganization", "UNKNOWN")
    org_safe = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in org).strip()

    for port in ports:
        line = f"{ip}:{port}"
        groups[country][org_safe].append(line)
        if port == 443:
            groups_443[country][org_safe].append(ip)

os.makedirs("regions_json", exist_ok=True)
os.makedirs("regions_json_443", exist_ok=True)

for country, orgs in groups.items():
    for org, entries in orgs.items():
        path = f"regions_json/{country}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/{org}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(entries))
        print(f"regions_json/{country}/{org}.txt — {len(entries)} 條")

for country, orgs in groups_443.items():
    for org, entries in orgs.items():
        path = f"regions_json_443/{country}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/{org}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(entries))
        print(f"regions_json_443/{country}/{org}.txt — {len(entries)} 條 (443 only)")
