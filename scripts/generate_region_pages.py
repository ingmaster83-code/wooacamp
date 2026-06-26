#!/usr/bin/env python3
"""
generate_region_pages.py - 지역별 정적 페이지 생성
데이터 수집 완료 후 실행

사용법:
  python scripts/generate_region_pages.py
"""
import sys, json, re
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / "_rawdata" / "camps.json"
REGION  = ROOT / "region"

# 시/도 약칭 → (URL 키, 표시명, 이모지)
DO_MAP = {
    "서울특별시":        ("서울", "서울특별시", "🏙️"),
    "경기도":            ("경기", "경기도", "🌾"),
    "인천광역시":        ("인천", "인천광역시", "⚓"),
    "강원특별자치도":    ("강원", "강원특별자치도", "🏔️"),
    "강원도":            ("강원", "강원특별자치도", "🏔️"),   # 구 명칭 통합
    "충청북도":          ("충북", "충청북도", "🌲"),
    "충청남도":          ("충남", "충청남도", "🌊"),
    "대전광역시":        ("대전", "대전광역시", "🏛️"),
    "세종특별자치시":    ("세종", "세종특별자치시", "🌿"),
    "전북특별자치도":    ("전북", "전북특별자치도", "🌾"),
    "전라북도":          ("전북", "전북특별자치도", "🌾"),   # 구 명칭 통합
    "전라남도":          ("전남", "전라남도", "🐚"),
    "광주광역시":        ("광주", "광주광역시", "🎨"),
    "경상북도":          ("경북", "경상북도", "🍎"),
    "경상남도":          ("경남", "경상남도", "🎋"),
    "부산광역시":        ("부산", "부산광역시", "🌅"),
    "대구광역시":        ("대구", "대구광역시", "🍑"),
    "울산광역시":        ("울산", "울산광역시", "🏭"),
    "제주특별자치도":    ("제주", "제주특별자치도", "🌺"),
}


def main():
    camps = json.loads(DATA.read_text(encoding='utf-8'))
    print(f"총 {len(camps)}개 캠핑장 로드")

    # 지역별 그룹핑 — 구 명칭은 새 명칭 키로 통합
    do_groups = defaultdict(list)
    for c in camps:
        do = c.get('doNm', '')
        if not do:
            continue
        key_info = DO_MAP.get(do)
        if key_info:
            do_groups[key_info[1]].append(c)   # display name을 키로 사용
        else:
            do_groups[do].append(c)

    # 시/도 페이지 생성
    REGION.mkdir(exist_ok=True)
    total_pages = 0

    for do_name, do_camps in do_groups.items():
        key, display, emoji = DO_MAP.get(do_name, (do_name, do_name, "📍"))

        # 시/군/구 집계
        sg_groups = defaultdict(list)
        for c in do_camps:
            sg = c.get('sigunguNm', '')
            if sg:
                sg_groups[sg].append(c)

        subregions = [{"name": sg, "count": len(cs)}
                      for sg, cs in sorted(sg_groups.items())]

        # 시/도 index 페이지
        do_dir = REGION / key
        do_dir.mkdir(exist_ok=True)
        page = f"""---
layout: region
title: {display} 캠핑장 | 우아캠프
description: {display} 캠핑장 {len(do_camps)}개 정보. 위치, 시설, 예약 정보를 확인하세요. 일반야영장, 자동차야영장, 글램핑, 카라반.
do_name: {key}
do_key: {key}
title_h1: {emoji} {display} 캠핑장 {len(do_camps)}개
subtitle: {display} 지역 캠핑장을 유형별, 시설별로 검색하세요.
subregions:
{chr(10).join(f"  - name: {s['name']}" + chr(10) + f"    count: {s['count']}" for s in subregions)}
---
"""
        (do_dir / "index.html").write_text(page, encoding='utf-8')
        total_pages += 1

        # 시/군/구 페이지
        for sg, sg_camps in sg_groups.items():
            sg_dir = do_dir / sg
            sg_dir.mkdir(exist_ok=True)
            sg_page = f"""---
layout: region
title: {sg} 캠핑장 | {display} | 우아캠프
description: {display} {sg} 캠핑장 {len(sg_camps)}개 정보. 위치, 시설, 예약 정보를 확인하세요.
do_name: {key}
do_key: {key}
sigungu: {sg}
title_h1: 📍 {sg} 캠핑장 {len(sg_camps)}개
subtitle: {display} {sg} 지역 캠핑장을 유형별, 시설별로 검색하세요.
---
"""
            (sg_dir / "index.html").write_text(sg_page, encoding='utf-8')
            total_pages += 1

    print(f"지역 페이지 생성 완료: {total_pages}개")
    print(f"  시/도: {len(do_groups)}개")


if __name__ == "__main__":
    main()
