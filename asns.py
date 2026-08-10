#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asns.py — 中國線路優化（優選）ASN 清單。split_json.py 同 reclassify_asn.py 共用。

想調整優選清單，淨係改呢個檔，然後：
- 有 all.json：跑 python split_json.py
- 冇 all.json：跑 python reclassify_asn.py
"""
PREFERRED_ASN = {
    # 三大電訊商骨幹（中國優化核心）
    4809,    # 中國電信 CN2
    9929,    # 中國聯通 CUII（A 網）
    58453,   # 中國移動國際 CMI
    10099,   # 中國聯通國際 China Unicom Global
    58807,   # 中國移動國際 CMI（第二 ASN）
    23764,   # 中國電信國際 CTGNet
    # 機房（CN2 / CMI 直連，中國線路優化）
    906,     # DMIT Cloud Services
    137929,  # DMIT Inc APAC
    25820,   # IT7 Networks
    32097,   # WholeSale Internet
    40065,   # CNSERVERS
    63888,   # DataWing Limited
    396982,  # Google Cloud
    9304,    # HGC 環電（香港）
    3491,    # PCCW 電訊盈科（香港）
    8100,    # QuadraNet（美西）
    35916,   # Multacom（美西）
    45102,   # Alibaba US（阿里雲美國）
}
