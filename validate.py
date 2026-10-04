import json
import os
import sys

# all.json 結構：
#   {"generated_at": "...", "list": {"country": {CC: n}, "ips": int}, "data": [ {ip, port, meta}, ... ]}
# data 先係真正嘅 entries（正常 ~14,000-15,000 條）
MIN_ENTRIES = 3000     # 硬下限：低於此一律當壞數據
MIN_RATIO = 0.5        # 同現有 all.json 比，唔可以縮水超過一半


def die(msg):
    print(f"❌ 驗證失敗：{msg}")
    if os.path.exists("all_new.json"):
        try:
            with open("all_new.json", encoding="utf-8", errors="replace") as f:
                print("   回應頭 200 字：", repr(f.read(200)))
        except Exception:
            pass
    sys.exit(1)


try:
    with open("all_new.json", encoding="utf-8") as f:
        raw = f.read()
except FileNotFoundError:
    die("搵唔到 all_new.json")

if not raw.strip():
    die("all_new.json 係空檔案（數據源冇回應）")

try:
    d = json.loads(raw)
except Exception as e:
    die(f"唔係有效 JSON（{e}）")

if not isinstance(d, dict):
    die(f"頂層唔係 object（係 {type(d).__name__}）")

# ① proxy / Worker 嘅錯誤回應（例如 {"error": "all upstream attempts failed", ...}）
if "error" in d:
    die(f"數據源回報錯誤：{d.get('error')} · attempts={d.get('attempts')}")

# ② 必須有 data 陣列（真正 entries）
data = d.get("data")
if not isinstance(data, list) or not data:
    die(f"缺少 data 陣列（頂層 keys={list(d)[:10]}）")

count = len(data)
if count < MIN_ENTRIES:
    die(f"data 只有 {count:,} 條（下限 {MIN_ENTRIES:,}），疑似壞數據")

# ③ 抽查項目結構
first = data[0]
if not (isinstance(first, dict) and "ip" in first):
    die(f"data 項目結構唔對（樣本 {str(first)[:100]}）")

# ④ 同現有 all.json 比對，防大幅縮水
if os.path.exists("all.json"):
    try:
        with open("all.json", encoding="utf-8") as f:
            old = json.load(f)
        old_data = old.get("data") or []
        if len(old_data) >= MIN_ENTRIES:
            ratio = count / len(old_data)
            print(f"新 {count:,} / 舊 {len(old_data):,} = {ratio:.1%}")
            if ratio < MIN_RATIO:
                die(f"數據縮水太嚴重（{ratio:.1%} < {MIN_RATIO:.0%}），拒絕覆蓋")
    except json.JSONDecodeError:
        print("⚠️ 現有 all.json 唔係有效 JSON，跳過比對")
    except Exception as e:
        print(f"⚠️ 比對現有 all.json 失敗（{e}），跳過")

countries = d.get("list", {}).get("country", {})
print(f"✓ {count:,} entries · {len(countries)} 個國家 · generated_at={d.get('generated_at')}")
os.replace("all_new.json", "all.json")
print("✓ all.json updated")
