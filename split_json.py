import json
import os
from collections import defaultdict

with open("all.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# { country: { org: [lines] } }
groups = defaultdict(lambda: defaultdict(list))
groups_443 = defaultdict(lambda: defaultdict(list))

for item in data:
    ip = item.get("ip", "")
    ports = item.get("port", [])
    meta = item.get("meta", {})
    country = meta.get("country", "UNKNOWN").upper()
    org = meta.get("asOrganization", "UNKNOWN")
    # 清理 org 名稱，避免非法字符出現在文件名
    org_safe = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in org).strip()

    for port in ports:
        line = f"{ip}:{port}"
        groups[country][org_safe].append(line)
        if port == 443:
            groups_443[country][org_safe].append(ip)

# 寫入 regions_json/
for country, orgs in groups.items():
    for org, entries in orgs.items():
        path = f"regions_json/{country}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/{org}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(entries))
        print(f"regions_json/{country}/{org}.txt — {len(entries)} 條")

# 寫入 regions_json_443/ (純 IP)
for country, orgs in groups_443.items():
    for org, entries in orgs.items():
        path = f"regions_json_443/{country}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/{org}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(entries))
        print(f"regions_json_443/{country}/{org}.txt — {len(entries)} 條 (443 only)")
