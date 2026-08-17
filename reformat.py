#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reformat.py — 一次性重整 DD repo 內所有 IP 清單檔的格式。

統一規範：
1. 檔名：NFC normalize → strip → 壓縮空白 → 移除尾部句點 → 非法字符轉 _
2. 合併：忽略大小階/空白/底線/尾部句點的組織名視為同一組織，合併內容
3. 內容：每檔去重 + 按 IP 排序（IPv4/IPv6 混合安全）
4. 換行：統一 LF，末行 newline，無空行、無 trailing whitespace
5. _all.txt / _all_443.txt 由 org 檔重新生成（保證一致）
6. stats.json 重新計算

用法：python reformat.py
"""
import ipaddress
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import OrderedDict, defaultdict

# 目錄偵測：動態（唔硬編碼），支援任意 port 目錄
def discover_dirs():
    """分組：organized（國家/組織結構）vs flat（扁平國家檔）。

    - regions_json / regions_json_clientip_v4 / regions_json_<port> → organized
    - regions_json_preferred_asn* / regions_json_residential* → flat
    """
    organized, flat = [], []
    for d in sorted(os.listdir(".")):
        if not (d.startswith("regions_json") and os.path.isdir(d)):
            continue
        suffix = d[len("regions_json"):]
        if suffix == "" or (suffix.startswith("_") and suffix[1:].isdigit()):
            organized.append(d)
        elif d.startswith("regions_json_preferred_asn") or d.startswith("regions_json_residential"):
            flat.append(d)
        elif d == "regions_json_clientip_v4":
            organized.append(d)
    return organized, flat

ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
SYSTEM_FILES = ("_all.txt", "_all_443.txt")


def is_org_file(fname):
    """組織檔：.txt 且唔係系統聚合檔。"""
    return fname.endswith(".txt") and fname not in SYSTEM_FILES


def clean_filename(name):
    """統一的檔名規則（與 split_json.py 一致）。"""
    n = unicodedata.normalize("NFC", name).strip()
    n = n.strip(" _")                    # 移除首尾底線（組織名怪異前綴）
    n = re.sub(r"\s+", " ", n)
    n = re.sub(r"\.+$", "", n)          # 移除尾部句點（避免 ..txt）
    n = ILLEGAL.sub("_", n)
    return n.strip() or "UNKNOWN"


def merge_key(name):
    """合併偵測 key：忽略大小階 / 空白 / 底線 / 尾部句點。"""
    n = unicodedata.normalize("NFC", name).lower()
    n = re.sub(r"[\s_]+", "", n)
    n = re.sub(r"\.+$", "", n)
    return n


def entry_sort_key(entry):
    """'ip' 或 'ip:port' 或 'ip:port#tag' → (ip_int, port_int) 排序。"""
    entry = entry.strip()
    base = entry.split("#")[0]          # 剝離 #國家 標記
    ip_part, port_part = base, "0"
    if ":" in base:
        # IPv6 內含多個冒號，用 rsplit 分 port
        head, _, tail = base.rpartition(":")
        if tail.isdigit() and head:
            ip_part, port_part = head, tail
    try:
        ip_int = int(ipaddress.ip_address(ip_part))
    except ValueError:
        ip_int = 1 << 200  # 無效 IP 排最後
    try:
        port_int = int(port_part)
    except ValueError:
        port_int = 0
    return (ip_int, port_int)


def read_entries(path):
    """讀檔 → 去空行 → strip → 去重。"""
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f.read().splitlines() if l.strip()]


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


def rebuild_organized_dir(base_dir):
    """重整 國家/組織 結構目錄。回傳 (org_count, entry_total, merged_list)。"""
    if not os.path.isdir(base_dir):
        return 0, 0, []
    merged_report = []
    total_entries = 0
    org_count = 0

    for country in sorted(os.listdir(base_dir)):
        cdir = os.path.join(base_dir, country)
        if not os.path.isdir(cdir):
            continue
        old_org_files = sorted(
            f for f in os.listdir(cdir)
            if is_org_file(f)
        )
        if not old_org_files:
            continue

        # 按合併 key 分組：key -> {new_name, files, entries}
        groups = OrderedDict()
        for fname in old_org_files:
            org_name = fname[:-4]
            key = merge_key(org_name)
            if key not in groups:
                groups[key] = {
                    "new_name": clean_filename(org_name),
                    "files": [],
                    "entries": [],
                }
            groups[key]["files"].append(fname)
            groups[key]["entries"].extend(read_entries(os.path.join(cdir, fname)))

        # 檔名衝突保險（clean 後撞名）
        used = {}
        for key, g in groups.items():
            base = g["new_name"]
            candidate, i = base, 2
            while candidate in used and used[candidate] != key:
                candidate = f"{base}_{i}"
                i += 1
            used[candidate] = key
            g["new_name"] = candidate

        # 寫 .tmp → 刪舊檔 → rename
        staged = []
        for key, g in groups.items():
            tmp = os.path.join(cdir, g["new_name"] + ".tmp")
            write_entries(tmp, g["entries"])
            staged.append((tmp, os.path.join(cdir, g["new_name"] + ".txt"), g))
        for fname in old_org_files:
            os.remove(os.path.join(cdir, fname))
        for tmp, final, g in staged:
            os.replace(tmp, final)
            n = len(read_entries(final))
            total_entries += n
            org_count += 1
            if len(g["files"]) > 1:
                merged_report.append(
                    f"{base_dir}/{country}: {g['files']} → {os.path.basename(final)} ({n} 條)"
                )

        # 重新生成 _all.txt（及 _all_443.txt）
        all_entries = []
        for key, g in groups.items():
            all_entries.extend(g["entries"])
        write_entries(os.path.join(cdir, "_all.txt"), all_entries)
        if base_dir in ("regions_json", "regions_json_clientip_v4"):
            all_443 = [
                e.rpartition(":")[0] for e in all_entries
                if e.rpartition(":")[2] == "443"
            ]
            write_entries(os.path.join(cdir, "_all_443.txt"), all_443)

    return org_count, total_entries, merged_report


def rebuild_flat_dir(base_dir):
    """重整扁平國家目錄 + 重新生成 _all.txt（格式 ip:port#國家）。"""
    if not os.path.isdir(base_dir):
        return 0, 0
    total = 0
    files = 0
    country_files = [
        f for f in sorted(os.listdir(base_dir))
        if f.endswith(".txt") and f not in SYSTEM_FILES
    ]
    all_entries = []
    for fname in country_files:
        path = os.path.join(base_dir, fname)
        entries = read_entries(path)
        write_entries(path, entries)
        total += len(entries)
        files += 1
        all_entries.extend(f"{e}#{fname[:-4]}" for e in entries)
    write_entries(os.path.join(base_dir, "_all.txt"), all_entries, key=asn_all_key)
    return files, total


def rebuild_organized_top(base_dir, has_443=True):
    """organized 目錄頂層統整：_all.txt（ip:port#國家 跟國家排）+ _all_443.txt（ip#國家）"""
    if not os.path.isdir(base_dir):
        return
    all_entries, all_443 = [], []
    for country in sorted(os.listdir(base_dir)):
        cdir = os.path.join(base_dir, country)
        if not os.path.isdir(cdir):
            continue
        for fname in sorted(os.listdir(cdir)):
            if not is_org_file(fname):
                continue
            for e in read_entries(os.path.join(cdir, fname)):
                if not e:
                    continue
                all_entries.append(f"{e}#{country}")
                if e.rpartition(":")[2] == "443":
                    all_443.append(f"{e.rpartition(':')[0]}#{country}")
    write_entries(os.path.join(base_dir, "_all.txt"), all_entries, key=asn_all_key)
    if has_443:
        write_entries(os.path.join(base_dir, "_all_443.txt"), all_443, key=asn_all_key)
    print(f"✓ {base_dir} 頂層統整: {len(all_entries)} 條（443: {len(all_443)}）")


def build_stats():
    """生成 stats.json（結構與 split_json.py 相同）。"""
    organized, flat = discover_dirs()
    stats = {}
    for base_dir in organized + flat:
        if not os.path.isdir(base_dir):
            continue
        if base_dir in flat:
            stats[base_dir] = {
                f[:-4]: len(read_entries(os.path.join(base_dir, f)))
                for f in sorted(os.listdir(base_dir))
                if f.endswith(".txt") and f not in SYSTEM_FILES
            }
        else:
            d = {}
            for country in sorted(os.listdir(base_dir)):
                cdir = os.path.join(base_dir, country)
                if not os.path.isdir(cdir):
                    continue
                orgs = {}
                for f in sorted(os.listdir(cdir)):
                    if f.endswith(".txt") and f not in SYSTEM_FILES:
                        orgs[f[:-4]] = len(read_entries(os.path.join(cdir, f)))
                if orgs:
                    d[country] = orgs
            stats[base_dir] = d
    with open("stats.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    organized, flat = discover_dirs()
    total_org, total_entries, merges = 0, 0, []
    for d in organized:
        oc, te, mg = rebuild_organized_dir(d)
        total_org += oc
        total_entries += te
        merges.extend(mg)
        print(f"✓ {d}: {oc} 個組織檔, {te} 條")
    # 頂層統整（_all.txt + _all_443.txt，ip:port#國家 跟國家排）
    for d in organized:
        if d in ("regions_json", "regions_json_clientip_v4"):
            rebuild_organized_top(d, has_443=True)
    for d in flat:
        fc, fe = rebuild_flat_dir(d)
        total_org += fc
        total_entries += fe
        print(f"✓ {d}: {fc} 個檔案, {fe} 條")

    build_stats()
    print(f"\n合計: {total_org} 檔, {total_entries} 條")
    if merges:
        print(f"\n⚠ 合併咗 {len(merges)} 組同名異寫組織:")
        for m in merges:
            print(f"  {m}")


if __name__ == "__main__":
    main()
