import json
import os
import ipaddress
from collections import defaultdict

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

try:
    with open("all.json", "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        print("all.json 是空文件，跳過")
        exit(0)
    raw = json.loads(content)
    data = raw["data"] if isinstance(raw, dict) else raw
except (json.JSONDecodeError, KeyError) as e:
    print(f"all.json 解析失敗：{e}")
    exit(0)

groups      = defaultdict(lambda: defaultdict(list))
groups_port = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

skipped = 0
for item in data:
    ip = item.get("ip", "")
    if not is_valid_ip(ip):
        skipped += 1
        continue
    item_ports = item.get("port", [])
    meta = item.get("meta", {})
    country = meta.get("country", "UNKNOWN").upper()
    org = meta.get("asOrganization", "UNKNOWN")
    org_safe = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in org).strip()

    for port in item_ports:
        groups[country][org_safe].append(f"{ip}:{port}")
        groups_port[port][country][org_safe].append(ip)

print(f"跳過無效 IP：{skipped} 條")

# regions_json/ 全部 port
os.makedirs("regions_json", exist_ok=True)
for country, orgs in groups.items():
    path = f"regions_json/{country}"
    os.makedirs(path, exist_ok=True)
    for org, entries in orgs.items():
        with open(f"{path}/{org}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(entries))

# regions_json_PORT/ 每個 port 純 IP
for port, countries in groups_port.items():
    for country, orgs in countries.items():
        path = f"regions_json_{port}/{country}"
        os.makedirs(path, exist_ok=True)
        for org, entries in orgs.items():
            with open(f"{path}/{org}.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(entries))

# stats.json
stats = {}
stats["regions_json"] = {
    country: {org: len(entries) for org, entries in orgs.items()}
    for country, orgs in groups.items()
}
for port, countries in groups_port.items():
    base_dir = f"regions_json_{port}"
    stats[base_dir] = {
        country: {org: len(entries) for org, entries in orgs.items()}
        for country, orgs in countries.items()
    }

with open("stats.json", "w") as f:
    json.dump(stats, f)

total = sum(
    count
    for dir_stats in stats.values()
    for country_stats in dir_stats.values()
    for count in country_stats.values()
)
print(f"完成，共 {total} 條")
