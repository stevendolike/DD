#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classify_residential.py — 由現有數據分類「家庭寬帶」IP。

掃 regions_json（全部國家/組織），用 residential.is_residential() 判斷
組織名係咪家庭 ISP，生成：
- regions_json_residential/    {國家}.txt + _all.txt（ip:port#國家）
- regions_json_residential_443/ 純 IP 版本

用法：python classify_residential.py
"""
import os
import shutil
import subprocess
import sys

from reformat import SYSTEM_FILES, asn_all_key, write_entries
from residential import is_residential

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    results = {}      # country -> {ip:port}
    results_443 = {}  # country -> {ip}
    matched_orgs = set()

    src = os.path.join(BASE, "regions_json")
    for country in sorted(os.listdir(src)):
        cdir = os.path.join(src, country)
        if not os.path.isdir(cdir):
            continue
        for f in os.listdir(cdir):
            if not (f.endswith(".txt") and f not in SYSTEM_FILES):
                continue
            if not is_residential(f[:-4]):
                continue
            matched_orgs.add(f[:-4])
            for line in open(os.path.join(cdir, f), encoding="utf-8"):
                e = line.strip()
                if not e:
                    continue
                ip_part, _, port = e.rpartition(":")
                results.setdefault(country, set()).add(e)
                if port == "443":
                    results_443.setdefault(country, set()).add(ip_part)

    print(f"命中 {len(matched_orgs)} 個家庭 ISP 組織：")
    for org in sorted(matched_orgs):
        print(f"  - {org}")
    print(f"共 {sum(len(v) for v in results.values())} 條（全部 port），443 版 {sum(len(v) for v in results_443.values())} 條")

    # 重建目錄
    for d in ("regions_json_residential", "regions_json_residential_443"):
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

    write_group(os.path.join(BASE, "regions_json_residential"), results)
    write_group(os.path.join(BASE, "regions_json_residential_443"), results_443)


if __name__ == "__main__":
    main()
