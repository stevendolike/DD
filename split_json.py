import json
import os
import shutil
import ipaddress
from collections import defaultdict

PREFERRED_ASN = {906, 25820, 32097, 63888, 396982, 137929, 40065, 135064, 4809, 9929, 58453}

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_ipv4(ip):
    try:
        return ipaddress.ip_address(ip).version == 4
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

groups             = defaultdict(lambda: defaultdict(list))
groups_port        = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
groups_asn         = defaultdict(list)
groups_asn_443     = defaultdict(list)
groups_clientip_v4 = defaultdict(lambda: defaultdict(list))

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
    asn = meta.get("asn", 0)
    client_ip = meta.get("clientIp", "")
    org_safe = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in org).strip()

    for port in item_ports:
        groups[country][org_safe].append(f"{ip}:{port}")
        groups_port[port][country][org_safe].append(ip)

        if asn in PREFERRED_ASN:
            groups_asn[country].append(f"{ip}:{port}")
            if port == 443:
                groups_asn_443[country].append(ip)

        if is_ipv4(client_ip):
            groups_clientip_v4[country][org_safe].append(f"{ip}:{port}")

print(f"跳過無效 IP：{skipped} 條")

def rebuild_dir(base_dir, country_data):
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    for country, orgs in country_data.items():
        path = f"{base_dir}/{country}"
        os.makedirs(path, exist_ok=True)
        for org, entries in orgs.items():
            with open(f"{path}/{org}.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(entries))

def rebuild_asn_dir(base_dir, country_data):
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    for country, entries in country_data.items():
        with open(f"{base_dir}/{country}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(entries))

rebuild_dir("regions_json", groups)
for port, countries in groups_port.items():
    rebuild_dir(f"regions_json_{port}", countries)
rebuild_asn_dir("regions_json_preferred_asn", groups_asn)
rebuild_asn_dir("regions_json_preferred_asn_443", groups_asn_443)
rebuild_dir("regions_json_clientip_v4", groups_clientip_v4)

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
stats["regions_json_preferred_asn"] = {
    country: len(entries) for country, entries in groups_asn.items()
}
stats["regions_json_preferred_asn_443"] = {
    country: len(entries) for country, entries in groups_asn_443.items()
}
stats["regions_json_clientip_v4"] = {
    country: {org: len(entries) for org, entries in orgs.items()}
    for country, orgs in groups_clientip_v4.items()
}

with open("stats.json", "w") as f:
    json.dump(stats, f)

total = sum(
    (sum(v.values()) if isinstance(list(v.values())[0], int) else sum(sum(x.values()) for x in v.values()))
    for v in stats.values() if v
)
print(f"完成，共 {total} 條")
