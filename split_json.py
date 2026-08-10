#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_json.py — 從 all.json 生成按地區/組織分類的 IP 清單

統一格式規則（與 reformat.py 一致）：
1. 組織名 sanitize：NFC → strip → 壓縮空白 → 移除尾部句點 → 非法字符轉 _
2. 合併：忽略大小階/空白/底線/尾部句點的組織名視為同一組織
3. 內容：去重 + 按 IP 排序（IPv4/IPv6 安全）
4. 寫檔：LF 換行、末行 newline、無空行
5. _all.txt / _all_443.txt 由 org 檔重新生成
"""
import ipaddress
import json
import os
import re
import shutil
import unicodedata
from collections import OrderedDict, defaultdict

from asns import PREFERRED_ASN

ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


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


def sanitize_org(name):
    """統一檔名規則。"""
    n = unicodedata.normalize("NFC", str(name)).strip()
    n = n.strip(" _")                    # 移除首尾底線（組織名怪異前綴）
    n = re.sub(r"\s+", " ", n)
    n = re.sub(r"\.+$", "", n)
    n = ILLEGAL.sub("_", n)
    return n.strip() or "UNKNOWN"


def merge_key(name):
    """合併偵測 key：忽略大小階 / 空白 / 底線 / 尾部句點。"""
    n = unicodedata.normalize("NFC", str(name)).lower()
    n = re.sub(r"[\s_]+", "", n)
    n = re.sub(r"\.+$", "", n)
    return n


def entry_sort_key(entry):
    """'ip' 或 'ip:port' 或 'ip:port#tag' → (ip_int, port_int) 排序。"""
    entry = entry.strip()
    base = entry.split("#")[0]          # 剝離 #國家 標記
    ip_part, port_part = base, "0"
    if ":" in base:
        head, _, tail = base.rpartition(":")
        if tail.isdigit() and head:
            ip_part, port_part = head, tail
    try:
        ip_int = int(ipaddress.ip_address(ip_part))
    except ValueError:
        ip_int = 1 << 200
    try:
        port_int = int(port_part)
    except ValueError:
        port_int = 0
    return (ip_int, port_int)


def write_entries(path, entries, key=entry_sort_key):
    """寫檔：去重 + 排序（可指定 key）+ LF + 末行 newline。"""
    unique = OrderedDict((e, None) for e in entries)
    lines = sorted(unique.keys(), key=key)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def asn_all_key(entry):
    """ip:port#國家（或 ip#國家）→ (國家, ip_int, port_int)：跟國家排列。"""
    country = entry.rpartition("#")[2]
    ip_int, port_int = entry_sort_key(entry)
    return (country, ip_int, port_int)


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

# 結構：key(merge_key) -> list[entries]；name_map: (country,key) -> [候選 display 名]
groups             = defaultdict(lambda: defaultdict(list))
groups_port        = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
groups_asn         = defaultdict(list)
groups_asn_443     = defaultdict(list)
groups_clientip_v4 = defaultdict(lambda: defaultdict(list))
name_map           = defaultdict(lambda: defaultdict(list))

skipped = 0
for item in data:
    ip = item.get("ip", "")
    if not is_valid_ip(ip):
        skipped += 1
        continue
    item_ports = item.get("port", [])
    meta = item.get("meta", {})
    country = str(meta.get("country", "UNKNOWN")).upper()
    org = str(meta.get("asOrganization", "UNKNOWN"))
    asn = meta.get("asn", 0)
    client_ip = meta.get("clientIp", "")
    display = sanitize_org(org)
    key = merge_key(org)

    for port in item_ports:
        entry = f"{ip}:{port}"
        groups[country][key].append(entry)
        groups_port[port][country][key].append(ip)

        if asn in PREFERRED_ASN:
            groups_asn[country].append(entry)
            if port == 443:
                groups_asn_443[country].append(ip)

        if is_ipv4(client_ip):
            groups_clientip_v4[country][key].append(entry)

        name_map[country][key].append(display)

print(f"跳過無效 IP：{skipped} 條")


def pick_display(country, key):
    """display 名 = 候選名 alphabetical 首名（與 reformat.py 一致）。"""
    return min(name_map[country][key])


def rebuild_dir(base_dir, country_data):
    """按國家+組織分類，加 _all.txt 和 _all_443.txt"""
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    for country, orgs in country_data.items():
        path = f"{base_dir}/{country}"
        os.makedirs(path, exist_ok=True)
        all_entries = []
        for key, entries in orgs.items():
            display = pick_display(country, key)
            write_entries(f"{path}/{display}.txt", entries)
            all_entries.extend(entries)
        write_entries(f"{path}/_all.txt", all_entries)
        all_443 = [
            e.rpartition(":")[0] for e in all_entries
            if e.rpartition(":")[2] == "443"
        ]
        write_entries(f"{path}/_all_443.txt", all_443)


def rebuild_port_dir(base_dir, country_data):
    """port 目錄：純 IP，加 _all.txt"""
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    for country, orgs in country_data.items():
        path = f"{base_dir}/{country}"
        os.makedirs(path, exist_ok=True)
        all_entries = []
        for key, entries in orgs.items():
            display = pick_display(country, key)
            write_entries(f"{path}/{display}.txt", entries)
            all_entries.extend(entries)
        write_entries(f"{path}/_all.txt", all_entries)


def rebuild_asn_dir(base_dir, country_data):
    """ASN 目錄：扁平國家文件 + _all.txt（格式 ip:port#國家）"""
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    all_entries = []
    for country, entries in sorted(country_data.items()):
        write_entries(f"{base_dir}/{country}.txt", entries)
        all_entries.extend(f"{e}#{country}" for e in entries)
    write_entries(f"{base_dir}/_all.txt", all_entries, key=asn_all_key)


rebuild_dir("regions_json", groups)
for port, countries in groups_port.items():
    rebuild_port_dir(f"regions_json_{port}", countries)
rebuild_asn_dir("regions_json_preferred_asn", groups_asn)
rebuild_asn_dir("regions_json_preferred_asn_443", groups_asn_443)
rebuild_dir("regions_json_clientip_v4", groups_clientip_v4)

# stats.json（不計 _all.txt / _all_443.txt；國家/組織均按名排序，與 reformat.py 一致）
stats = {}
stats["regions_json"] = {
    country: {pick_display(country, k): len(entries) for k, entries in sorted(orgs.items(), key=lambda kv: pick_display(country, kv[0]))}
    for country, orgs in sorted(groups.items())
}
for port, countries in groups_port.items():
    base_dir = f"regions_json_{port}"
    stats[base_dir] = {
        country: {pick_display(country, k): len(entries) for k, entries in sorted(orgs.items(), key=lambda kv: pick_display(country, kv[0]))}
        for country, orgs in sorted(countries.items())
    }
stats["regions_json_preferred_asn"] = {
    country: len(entries) for country, entries in sorted(groups_asn.items())
}
stats["regions_json_preferred_asn_443"] = {
    country: len(entries) for country, entries in sorted(groups_asn_443.items())
}
stats["regions_json_clientip_v4"] = {
    country: {pick_display(country, k): len(entries) for k, entries in sorted(orgs.items(), key=lambda kv: pick_display(country, kv[0]))}
    for country, orgs in sorted(groups_clientip_v4.items())
}

stats = dict(sorted(stats.items()))  # 鍵按字母序，與 reformat.py 一致
with open("stats.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)
    f.write("\n")

total = sum(
    (sum(v.values()) if isinstance(list(v.values())[0], int) else sum(sum(x.values()) for x in v.values()))
    for v in stats.values() if v
)
print(f"完成，共 {total} 條")
