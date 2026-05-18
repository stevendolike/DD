import json
import os
import sys

try:
    with open("all_new.json") as f:
        d = json.load(f)
    data = d.get("data", d) if isinstance(d, dict) else d
    count = len(data)
    print(f"Got {count} entries")
    if count >= 100:
        os.replace("all_new.json", "all.json")
        print("all.json updated")
    else:
        print("條目太少，保留舊數據")
except Exception as e:
    print(f"驗證失敗：{e}，保留舊數據")
