#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asns.py — 中國線路優化（優選）ASN 清單。split_json.py 同 reclassify_asn.py 共用。

2026-08-12 大精簡：只保留「確定有優化線路」嘅 ASN：
- 骨幹：三大電訊商優化線路（CN2 / CUII / CMI）及其國際版
- CN2 GIA 機房：賣 CN2 GIA 專線產品嘅機房（實測優化）
- 香港直連：香港 CN2/CMI 直連 ISP

已移除：Google（對等互聯非優化）、中國雲廠（有優化路由但非 GIA 專線）、
一般 CN2 直連機房（Multacom/WII/CNSERVERS 等，混有普通線路）。

想調整優選清單，淨係改呢個檔，然後：
- 有 all.json：跑 python split_json.py
- 冇 all.json：跑 python reclassify_asn.py
"""
PREFERRED_ASN = {
    # ── 三大電訊商骨幹（一定優化）──
    4809,    # 中國電信 CN2
    9929,    # 中國聯通 CUII（A 網）
    58453,   # 中國移動國際 CMI
    58807,   # 中國移動國際 CMI（第二 ASN）
    10099,   # 中國聯通國際 China Unicom Global
    23764,   # 中國電信國際 CTGNet
    # ── CN2 GIA 機房（實測優化線路）──
    906,     # DMIT Cloud Services（美西/東京 CN2 GIA）
    137929,  # DMIT Inc APAC
    25820,   # IT7 Networks（CN2 GIA）
    3258,    # xTom Japan（東京/大阪 CN2 GIA）
    # ── 香港 CN2/CMI 直連 ──
    9304,    # HGC 環電（香港）
    3491,    # PCCW 電訊盈科（香港）
}
