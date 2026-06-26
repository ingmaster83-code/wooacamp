#!/usr/bin/env python3
"""
fetch_camps.py - 고캠핑 API에서 전체 캠핑장 데이터 수집

사용법:
  python scripts/fetch_camps.py            # 전체 수집
  python scripts/fetch_camps.py --test 50  # 50개만 테스트
"""
import sys, json, time, argparse, os
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding='utf-8')

API_KEY  = os.environ.get("GOCAMPING_API_KEY", "")
BASE_URL = "http://apis.data.go.kr/B551011/GoCamping"
OUT_FILE = Path(__file__).parent.parent / "_rawdata" / "camps.json"
DELAY    = 0.3  # 요청 간격 (초)

COMMON_PARAMS = {
    "serviceKey": API_KEY,
    "MobileOS": "ETC",
    "MobileApp": "WooaCamp",
    "_type": "json",
}


def fetch_based_list(page: int, rows: int = 100) -> dict:
    url = f"{BASE_URL}/basedList"
    params = {**COMMON_PARAMS, "numOfRows": rows, "pageNo": page}
    query = "&".join(f"{k}={v}" for k, v in params.items())
    resp = requests.get(f"{url}?{query}", timeout=30)
    resp.raise_for_status()
    return json.loads(resp.content.decode("utf-8"))


def fetch_image_list(content_id: str) -> list:
    url = f"{BASE_URL}/imageList"
    params = {**COMMON_PARAMS, "contentId": content_id, "numOfRows": 10, "pageNo": 1}
    query = "&".join(f"{k}={v}" for k, v in params.items())
    resp = requests.get(f"{url}?{query}", timeout=30)
    if resp.status_code != 200 or not resp.text.strip():
        return []
    try:
        data = json.loads(resp.content.decode("utf-8"))
        items = data.get("response", {}).get("body", {}).get("items", {})
        if not items or items == "":
            return []
        item = items.get("item", [])
        if isinstance(item, dict):
            item = [item]
        return [i.get("imageUrl", "") for i in item if i.get("imageUrl")]
    except Exception:
        return []


def make_slug(content_id: str, name: str) -> str:
    import re
    # 캠핑장명에서 URL-safe 슬러그 생성
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return f"{content_id}-{slug}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, default=0, help="테스트: N개만 수집")
    args = parser.parse_args()

    if not API_KEY:
        print("오류: GOCAMPING_API_KEY 환경변수를 설정하세요.")
        print("  set GOCAMPING_API_KEY=<인증키>")
        sys.exit(1)

    # 1단계: 전체 목록 수집
    print("=== basedList 수집 시작 ===")
    first = fetch_based_list(1, 1)
    total = int(first["response"]["body"]["totalCount"])
    rows_per_page = 100
    total_pages = (total + rows_per_page - 1) // rows_per_page
    print(f"총 캠핑장 수: {total}개 / {total_pages}페이지")

    if args.test:
        total_pages = max(1, args.test // rows_per_page + 1)
        print(f"테스트 모드: {args.test}개 수집")

    all_camps = []
    for page in range(1, total_pages + 1):
        try:
            data = fetch_based_list(page, rows_per_page)
            items = data["response"]["body"]["items"].get("item", [])
            if isinstance(items, dict):
                items = [items]
            all_camps.extend(items)
            print(f"  페이지 {page}/{total_pages}: {len(items)}개 수집 (누적 {len(all_camps)})")
            if args.test and len(all_camps) >= args.test:
                all_camps = all_camps[:args.test]
                break
            time.sleep(DELAY)
        except Exception as e:
            print(f"  [오류] 페이지 {page}: {e}")
            time.sleep(1)

    print(f"\n기본 데이터 수집 완료: {len(all_camps)}개\n")

    # 2단계: 이미지 수집 (firstImageUrl이 없는 것 + 추가 이미지)
    print("=== imageList 수집 시작 ===")
    for i, camp in enumerate(all_camps):
        cid = camp.get("contentId", "")
        if not cid:
            continue

        # firstImageUrl이 없거나 이미지 슬라이더용 추가 이미지가 필요한 경우
        images = fetch_image_list(cid)
        camp["images"] = images
        if not camp.get("firstImageUrl") and images:
            camp["firstImageUrl"] = images[0]

        # 슬러그 생성
        camp["slug"] = make_slug(cid, camp.get("facltNm", cid))

        if (i + 1) % 50 == 0:
            print(f"  이미지 {i+1}/{len(all_camps)} 처리 완료...")
            # 중간 저장
            OUT_FILE.write_text(
                json.dumps(all_camps, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        time.sleep(DELAY)

    # 최종 저장
    OUT_FILE.write_text(
        json.dumps(all_camps, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n완료: {OUT_FILE}")
    print(f"  총 {len(all_camps)}개 캠핑장 저장")
    print(f"  이미지 있는 캠핑장: {sum(1 for c in all_camps if c.get('firstImageUrl'))}개")

    # 지역 통계
    from collections import Counter
    do_counts = Counter(c.get("doNm", "기타") for c in all_camps)
    print("\n지역별 수:")
    for do, cnt in sorted(do_counts.items(), key=lambda x: -x[1]):
        print(f"  {do}: {cnt}개")


if __name__ == "__main__":
    main()
