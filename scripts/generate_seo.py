#!/usr/bin/env python3
"""
generate_seo.py - DeepSeek API로 캠핑장별 SEO 설명문 생성

사용법:
  python scripts/generate_seo.py            # 전체 (seoDescription 없는 것만)
  python scripts/generate_seo.py --limit 50 # 50건만 테스트
  python scripts/generate_seo.py --force    # 기존 것도 덮어쓰기
"""
import json, sys, time, argparse
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding='utf-8')

API_KEY_PATH = Path(r"C:\개인\개인 프로젝트\blogwriter_new\blogger_seo_bot\config\deepseek_api_key.txt")
DATA_FILE    = Path(__file__).parent.parent / "_rawdata" / "camps.json"
DELAY        = 0.1

PROMPT_TMPL = """다음 캠핑장 정보를 바탕으로 네이버/구글 검색 최적화용 한국어 소개문을 120자 이내로 작성하세요.
위치, 유형, 주요 시설을 자연스럽게 담아주세요. 문장으로 끝내세요. 따옴표나 특수기호 없이.

캠핑장명: {name}
위치: {loc}
유형: {induty}
부대시설: {sbrs}
소개: {intro}

소개문만 출력하세요 (설명 없이):"""


def get_api_key() -> str:
    return API_KEY_PATH.read_text(encoding="utf-8").strip()


def generate_desc(camp: dict, api_key: str) -> str:
    loc   = f"{camp.get('doNm', '')} {camp.get('sigunguNm', '')}".strip()
    sbrs  = (camp.get('sbrsCl') or '')[:80]
    intro = (camp.get('lineIntro') or '')[:80]
    prompt = PROMPT_TMPL.format(
        name=camp.get('facltNm', ''),
        loc=loc,
        induty=camp.get('induty', ''),
        sbrs=sbrs,
        intro=intro,
    )
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.5,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()[:155]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    camps   = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    api_key = get_api_key()

    targets = [c for c in camps if args.force or not c.get("seoDescription")]
    if args.limit:
        targets = targets[:args.limit]

    id_map = {c["contentId"]: i for i, c in enumerate(camps)}
    total  = len(targets)
    print(f"생성 대상: {total}건\n")

    done = 0
    for camp in targets:
        try:
            desc = generate_desc(camp, api_key)
            camp["seoDescription"] = desc
            idx = id_map.get(camp["contentId"])
            if idx is not None:
                camps[idx]["seoDescription"] = desc
            done += 1
            print(f"  [{done}/{total}] {camp.get('facltNm','')[:20]}: {desc[:40]}...")
        except Exception as e:
            print(f"  [실패] {camp.get('facltNm','')}: {e}")

        if done % 100 == 0:
            DATA_FILE.write_text(
                json.dumps(camps, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"  [저장] {done}건 완료")

        time.sleep(DELAY)

    DATA_FILE.write_text(
        json.dumps(camps, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n완료: {done}/{total}건 생성")


if __name__ == "__main__":
    main()
