#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asns.py — 中國線路優化（優選）ASN 清單。split_json.py 同 reclassify_asn.py 共用。

想調整優選清單，淨係改呢個檔，然後：
- 有 all.json：跑 python split_json.py
- 冇 all.json：跑 python reclassify_asn.py

分類：
- 骨幹：三大電訊商優化線路（CN2 / CUII / CMI）及其國際版
- 美西機房：租 CN2 GIA 線路
- 亞太機房：香港/日本/新加坡 CN2/CMI 直連
- 中國雲廠：海外節點接咗優化線路
"""
PREFERRED_ASN = {
    # ── 三大電訊商骨幹（中國優化核心）──
    4809,    # 中國電信 CN2
    9929,    # 中國聯通 CUII（A 網）
    58453,   # 中國移動國際 CMI
    10099,   # 中國聯通國際 China Unicom Global
    58807,   # 中國移動國際 CMI（第二 ASN）
    23764,   # 中國電信國際 CTGNet
    # ── 美西機房（CN2 GIA 直連）──
    906,     # DMIT Cloud Services
    137929,  # DMIT Inc APAC
    25820,   # IT7 Networks
    32097,   # WholeSale Internet
    8100,    # QuadraNet
    35916,   # Multacom
    # ── 亞太機房（香港/日本 CN2/CMI 直連）──
    9304,    # HGC 環電（香港）
    3491,    # PCCW 電訊盈科（香港）
    9381,    # HKBN Enterprise Solutions（香港寬頻企業方案）
    40065,   # CNSERVERS
    63888,   # DataWing Limited
    3258,    # xTom Japan（東京/大阪 CN2 GIA）
    # ── 中國雲廠海外節點 ──
    45102,   # 阿里雲（美國）
    132203,  # 騰訊雲國際
    136907,  # 華為雲
    55990,   # 華為雲數據中心
    21859,   # Zenlayer
    135377,  # UCloud 香港
    138915,  # 靠譜雲香港
    55967,   # 百度
    # ── 對等互聯型 ──
    396982,  # Google Cloud（同 CN2 對等互聯）
}
