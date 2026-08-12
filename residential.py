#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""residential.py — 家庭寬帶（residential ISP）組織名判斷。

分類原理：家庭寬帶 IP 嘅 ASN 名稱（asOrganization）係著名家用 ISP
（Comcast、AT&T、電信省級骨幹等）。用關鍵字匹配 + 排除機房字眼
（IDC/CLOUD/HOSTING/VPS…）嚟判斷。

注意：呢個分類依賴數據入面有家用 ISP 嘅 IP。現有掃描數據（all.json）
以機房為主，家寬 IP 好少；數據源恢復後先會充實。
"""
# 家庭 ISP 關鍵字（大階匹配；唔好加太短/太通用嘅字，避免誤判）
RESIDENTIAL_KEYWORDS = [
    # 美國
    "COMCAST",
    "AT&T",
    "ATT-INTERNET", "ATT-MOBILITY", "ATT-SERVICES",
    "VERIZON WIRELESS", "VERIZON FIOS",
    "CHARTER COMMUNICATIONS", "SPECTRUM",
    "COX COMMUNICATIONS",
    "FRONTIER COMMUNICATIONS",
    "CENTURYLINK", "LUMEN TECHNOLOGIES",
    "WINDSTREAM",
    "T-MOBILE",
    "MEDIACOM COMMUNICATIONS",
    "OPTIMUM", "ALTICE",
    "CONSOLIDATED COMMUNICATIONS",
    "TDS TELECOM",
    "WYYERD",
    "COGECO",           # 加拿大 Cogeco（家寬）
    "FIBERPOWER",       # 美國 FiberPower（光纖 ISP）
    "FIBERXPRESS",      # 荷蘭 FiberXpress（光纖家寬）
    "M-NET",            # 德國 M-net（慕尼黑家寬）
    "SUPERONLINE",      # 土耳其 Superonline（家寬）
    "ZIGGO",            # 荷蘭 Ziggo（家寬）
    "TELEMACH",         # 斯洛文尼亞 Telemach（家寬）
    "ROSTELECOM",       # 俄羅斯 Rostelecom（國營電訊）
    "KAZTELECOM",       # 哈薩克 Kazakhtelecom（國營電訊）
    "NOVOTELEKOM",      # 俄羅斯 Novotelecom（家寬）
    "SK BROADBAND",     # 韓國 SK Broadband（家寬）
    "SO-NET",           # 日本 So-net（家寬）
    # 家寬 pool 特徵：組織名係「客戶池」名（唔含 ISP 名）
    "XDSL", "FTTX", "ADSL", "BROADBAND",
    # 通用標記：任何 ISP 嘅住宅/大眾產品線
    "MASS INTERNET", "RESIDENTIAL",
    # ── 混合型電訊商（家用+商用同一品牌，家用為主體）──
    # 香港 / 台灣
    "HKT", "NETVIGATOR", "PCCW", "HKBN", "CHUNGHWA",
    # 日本
    "NTT", "IIJ",
    # BBIX：IX 名但數據入面嘅 IP 實為 SoftBank 光纖家寬（AS17676，126.x 網段）
    "BBIX",
    # 歐洲
    "TELIA", "TELENET", "PROXIMUS", "UPC", "LIBERTY GLOBAL",
    # 東南亞
    "AIS", "TRUE", "VNPT", "VIETTEL", "PLDT", "GLOBE TELECOM", "GLOBE MOBILE", "TELKOM", "INDOSAT",
    # 南亞
    "AIRTEL", "JIO", "BSNL",
    # 中東
    "ETISALAT", "OREDOO", "STC", "ZAIN",
    # 拉丁美洲
    "TELMEX", "CLARO", "VIVO", "ENTEL", "MOVISTAR",
    # 中國（省級骨幹 = 家寬線路；排除 IDC 由 EXCLUDE 處理）
    "CHINANET-", "CHINA169-", "CMNET-", "CHINATELECOM-",
    # 日本
    "KDDI CORPORATION",
    "SOFTBANK",
    "OCN", "BIGLOBE", "ASAHI-NET", "SONY NETWORK", "NIFTY",
    # 韓國
    "KORNET", "SK TELECOM", "LG U+", "KOREA TELECOM",   # Korea Telecom = KT（AS4766 家寬）
    # 台灣
    "HINET",
    # 英國
    "VIRGIN MEDIA", "TALKTALK", "SKY UK", "EE LIMITED",
    "BT-",              # 英國 BT（組織名 BT-R101-TEST 等，BT- 開頭）
    "COMMUNITY FIBRE",  # 英國光纖家寬（數據未有，等將來）
    # 德國 / 歐洲
    "DEUTSCHE TELEKOM", "VODAFONE", "TELEFONICA", "O2 GERMANY",
    "SWISSCOM", "TELENOR", "KPN",
    "TELE COLUMBUS",    # 德國有線家寬（PYUR 品牌）
    # 法國
    "ORANGE", "SFR", "BOUYGUES", "FREE SAS", "FREE MOBILE",
    # 意大利
    "TELECOM ITALIA", "WIND TRE",
    # 加拿大 / 澳洲
    "BELL CANADA", "ROGERS COMMUNICATIONS", "TELUS", "SHAW COMMUNICATIONS", "VIDEOTRON",
    "TELSTRA", "OPTUS", "TPG INTERNET",
    # 新加坡 / 香港
    "SINGTEL", "STARHUB", "VIEWQWEST", "NETVIGATOR",
]

# 機房 / 數據中心字眼：命中即排除（唔係家寬）
EXCLUDE_KEYWORDS = [
    "IDC", "CLOUD", "HOSTING", "VPS", "SERVER", "COLO", "DEDICATED", "DATACENTER", "DATA CENTER",
    "TRUSTEE",  # 信託公司（如 KEY STONE CORPORATE TRUSTEE），避免 EE LIMITED 誤中
    "WEBHORIZON",  # 新加坡 VPS 商（個名有 IT Broadband，但係 hosting）
    # 教育機構（如 Universitaet Kaiserslautern 會誤中 AIS 等短關鍵字）
    "UNIVERSIT", "COLLEGE", "SCHOOL", "ACADEMY", "UNIVERSITY",
]


def is_residential(org):
    """判斷組織名係咪家庭寬帶 ISP。"""
    up = str(org).upper()
    for ex in EXCLUDE_KEYWORDS:
        if ex in up:
            return False
    for kw in RESIDENTIAL_KEYWORDS:
        if kw in up:
            return True
    return False
