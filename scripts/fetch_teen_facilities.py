#!/usr/bin/env python3
"""
fetch_teen_facilities.py - 전국 청소년수련시설표준데이터에서
숙박형 청소년수련시설(수련원/유스호스텔/야영장)만 추려 camps.json에 병합한다.

캠핑장과 마찬가지로 "숙박 가능한 야외활동 시설"이라는 공통점으로 wooacamp에
소카테고리로 편입한다. 문화의집/수련관/센터 등 지역 상시이용 시설은
캠핑과 성격이 달라 제외한다.

사용법:
  python scripts/fetch_teen_facilities.py
"""
import json
import os
import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
CAMPS_FILE = ROOT / "_rawdata" / "camps.json"
RAW_FILE = ROOT / "_rawdata" / "teen_facilities_raw.json"

API_KEY = os.environ.get("DATA_GO_KR_API_KEY", "9490b1d34e92aa9e25b32a4cff1438fc7b9c71e5d332413916a391e867f61e86")
API_URL = "https://api.data.go.kr/openapi/tn_pubr_public_teen_training_fclt_api"

# 시설명에 이 키워드가 있으면 "숙박형" 시설로 간주 (캠핑과 성격이 맞는 것만)
TYPE_MAP = [
    ("수련원", "청소년수련원"),
    ("유스호스텔", "청소년유스호스텔"),
    ("야영장", "청소년야영장"),
]


def classify(name: str):
    for keyword, induty in TYPE_MAP:
        if keyword in name:
            return induty
    return None


def make_slug(content_id: str, name: str) -> str:
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return f"{content_id}-{slug}"


def split_facilities(raw: str):
    if not raw:
        return ""
    raw = raw.strip()
    raw = re.sub(r"\s*등\s*$", "", raw)
    parts = re.split(r"[+,]", raw)
    parts = [p.strip() for p in parts if p.strip()]
    return ",".join(parts)


def fetch_all():
    resp = requests.get(
        API_URL,
        params={"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 1, "type": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    total = resp.json()["body"]["totalCount"]

    resp = requests.get(
        API_URL,
        params={"serviceKey": API_KEY, "pageNo": 1, "numOfRows": total, "type": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    items = resp.json()["body"]["items"]["item"]
    return items


def normalize(items):
    records = []
    for idx, it in enumerate(items):
        name = (it.get("fcltNm") or "").strip()
        induty = classify(name)
        if not induty:
            continue

        content_id = f"teen{idx:04d}"
        addr = (it.get("lctnRoadNm") or it.get("lctnLotnoAddr") or "").strip()
        sido = (it.get("ctpvNm") or "").strip()
        sggu = (it.get("sggNm") or "").strip()
        tel = (it.get("telno") or "").strip()
        oper = (it.get("operGrpNm") or "").strip()
        sbrs = split_facilities(it.get("mainFclt", ""))

        desc = f"{sido} {sggu} {name} {induty} 위치, 연락처 정보를 확인하세요."
        if oper:
            desc += f" 운영단체: {oper}."

        records.append({
            "contentId": content_id,
            "facltNm": name,
            "induty": induty,
            "doNm": sido,
            "sigunguNm": sggu,
            "addr1": addr,
            "addr2": "",
            "tel": tel,
            "facltDivNm": oper,
            "sbrsCl": sbrs,
            "lineIntro": f"운영단체: {oper}" if oper else "",
            "seoDescription": desc[:155],
            "slug": make_slug(content_id, name),
            "images": [],
            "firstImageUrl": "",
        })
    return records


def main():
    print("=== 청소년수련시설 데이터 수집 시작 ===")
    items = fetch_all()
    print(f"전체 {len(items)}건 수신")

    RAW_FILE.parent.mkdir(exist_ok=True)
    RAW_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    records = normalize(items)
    print(f"숙박형(수련원/유스호스텔/야영장) 필터링 후: {len(records)}건")

    from collections import Counter
    type_cnt = Counter(r["induty"] for r in records)
    for k, v in type_cnt.items():
        print(f"  {k}: {v}건")

    if not CAMPS_FILE.exists():
        raise SystemExit(f"camps.json이 없습니다: {CAMPS_FILE}")

    camps = json.loads(CAMPS_FILE.read_text(encoding="utf-8"))
    before = len(camps)
    camps = [c for c in camps if not str(c.get("contentId", "")).startswith("teen")]
    removed = before - len(camps)
    camps.extend(records)

    CAMPS_FILE.write_text(json.dumps(camps, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ncamps.json 병합 완료: 기존 청소년시설 {removed}건 제거 후 {len(records)}건 추가")
    print(f"총 캠핑장+청소년수련시설: {len(camps)}건")


if __name__ == "__main__":
    main()
