#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reclassify_asn.py — 由 RIPEstat announced prefixes 重建優選 ASN 清單。

用途：數據源 all.json 失效時（zip.cm.edu.kg 404），無法靠 split_json.py
重新分類 ASN。呢個工具改用 RIPE 資料庫：攞每粒 PREFERRED_ASN 而家
公佈嘅 IP 前綴，再喺現有 regions_json（全部國家/組織數據）度做最長
前綴匹配，篩選出優選清單。

用法：python reclassify_asn.py
（改完 split_json.py 嘅 PREFERRED_ASN 之後再跑，就會用新清單重建）
"""
import ipaddress
import json
import os
import shutil
import subprocess
import sys
import urllib.request

from asns import PREFERRED_ASN
from reformat import SYSTEM_FILES, asn_all_key, write_entries

BASE = os.path.dirname(os.path.abspath(__file__))


def fetch_prefixes(asn):
    url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}"
    req = urllib.request.Request(url, headers={"User-Agent": "DD-reclassify/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return [p["prefix"] for p in d.get("data", {}).get("prefixes", []) if "prefix" in p]


def main():
    # 1. 攞每粒 ASN 嘅 announced prefixes（IPv4/IPv6 分開 collapse）
    asn_nets = {}
    for asn in sorted(PREFERRED_ASN):
        try:
            raw = fetch_prefixes(asn)
            v4 = [p for p in raw if ":" not in p.split("/")[0]]
            v6 = [p for p in raw if ":" in p.split("/")[0]]
            nets = list(ipaddress.collapse_addresses(
                ipaddress.ip_network(p, strict=False) for p in v4))
            nets += list(ipaddress.collapse_addresses(
                ipaddress.ip_network(p, strict=False) for p in v6))
            asn_nets[asn] = nets
            if not nets:
                print(f"AS{asn}: 0 個前綴（RIPEstat 無數據，跳過）")
            else:
                print(f"AS{asn}: {len(nets)} 個前綴")
        except Exception as e:
            print(f"AS{asn}: 攞前綴失敗 — {e}")

    if not asn_nets:
        print("無任何前綴，中止")
        sys.exit(1)

    # 2. 最長前綴匹配
    def match_asn(ip_str):
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return None
        best, best_len = None, -1
        for asn, nets in asn_nets.items():
            for n in nets:
                if addr in n and n.prefixlen > best_len:
                    best, best_len = asn, n.prefixlen
        return best

    # 3. 掃 regions_json 全部 entry
    results = {}      # country -> {ip:port}
    results_443 = {}  # country -> {ip}
    matched = 0
    src = os.path.join(BASE, "regions_json")
    for country in sorted(os.listdir(src)):
        cdir = os.path.join(src, country)
        if not os.path.isdir(cdir):
            continue
        for f in os.listdir(cdir):
            if not (f.endswith(".txt") and f not in SYSTEM_FILES):
                continue
            for line in open(os.path.join(cdir, f), encoding="utf-8"):
                e = line.strip()
                if not e:
                    continue
                ip_part, _, port = e.rpartition(":")
                if match_asn(ip_part) is None:
                    continue
                results.setdefault(country, set()).add(e)
                if port == "443":
                    results_443.setdefault(country, set()).add(ip_part)
                matched += 1
    print(f"匹配到 {matched} 條（全部 port），443 版另計")

    # 4. 重建目錄（國家檔 + _all.txt 跟國家排列）
    for d in ("regions_json_preferred_asn", "regions_json_preferred_asn_443"):
        p = os.path.join(BASE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
        os.makedirs(p)

    def write_group(base_dir, data):
        all_entries = []
        for country, entries in sorted(data.items()):
            write_entries(os.path.join(base_dir, f"{country}.txt"), entries)
            all_entries.extend(f"{e}#{country}" for e in entries)
        write_entries(os.path.join(base_dir, "_all.txt"), all_entries, key=asn_all_key)
        print(f"  {base_dir}: {len(data)} 國家, {len(all_entries)} 條")

    write_group(os.path.join(BASE, "regions_json_preferred_asn"), results)
    write_group(os.path.join(BASE, "regions_json_preferred_asn_443"), results_443)

    # 5. 重整 + 更新 README
    print("\n重整同更新 README...")
    subprocess.run([sys.executable, "reformat.py"], cwd=BASE, check=True)
    subprocess.run([sys.executable, "update_readme.py"], cwd=BASE, check=True)
    print("完成")


if __name__ == "__main__":
    main()
