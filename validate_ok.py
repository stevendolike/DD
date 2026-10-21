#!/usr/bin/env python3
"""validate_ok.py — 判斷下載到嘅 all.json 係唔係有效數據（split.yml download step 用）

⚠️ 為何唔可以靠 `grep '"error"'`：
   上游數據本身嘅單一條 entry 可能有 `meta.error`（例：data[12480].meta.error =
   "页面不存在。"）——2026-10-20 起出現，令舊檢查 `! grep -q '"error"'` 誤判成
   「下載失敗」→ 所有源都判死 → workflow exit 1（proxy 其實完全正常）。

有效條件（只看頂層結構）：
  1. 檔案 > 100 KB
  2. 係合法 JSON 且頂層係 object
  3. 頂層冇 "error" key（proxy / 上游嘅錯誤回應）
  4. 頂層有 "data" 或 "list" key（真正數據）
"""
import json
import os
import sys

MIN_BYTES = 100_000


def main(path: str) -> int:
    try:
        size = os.path.getsize(path)
    except OSError:
        print(f"missing file: {path}", file=sys.stderr)
        return 1
    if size <= MIN_BYTES:
        print(f"too small: {size} bytes", file=sys.stderr)
        return 1

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            doc = json.load(f)
    except Exception as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(doc, dict):
        print(f"top-level is {type(doc).__name__}, not object", file=sys.stderr)
        return 1

    if "error" in doc:
        print(f"top-level error response: {str(doc.get('error'))[:120]}", file=sys.stderr)
        return 1

    if "data" not in doc and "list" not in doc:
        keys = ", ".join(list(doc)[:8])
        print(f"no data/list key (top-level keys: {keys})", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: validate_ok.py <json-file>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
