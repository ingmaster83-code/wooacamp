import json, os, sys
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://wooacamp.wooahouse.com"
TODAY = date.today().isoformat()

camps = json.loads(open("_rawdata/camps.json", encoding="utf-8").read())

urls = []

def u(loc, priority, changefreq):
    urls.append(f"""  <url>
    <loc>{BASE_URL}{loc}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

# 메인 페이지
u("/", "1.0", "weekly")

# 지역/유형/테마/검색 인덱스
u("/region/", "0.9", "monthly")
u("/type/", "0.9", "monthly")
u("/theme/", "0.9", "monthly")
u("/search/", "0.8", "monthly")

# 기타
u("/privacy/", "0.3", "yearly")

# 유형별 페이지
for t in ["일반야영장", "자동차야영장", "글램핑", "카라반"]:
    u(f"/type/{t}/", "0.8", "monthly")

# 지역 페이지 (region/ 디렉토리 순회)
for root, dirs, files in os.walk("region"):
    for f in files:
        if f == "index.html":
            path = os.path.join(root, f).replace("\\", "/").replace("region/", "/region/").replace("/index.html", "/")
            if not path.endswith("/"):
                path += "/"
            u(path, "0.8", "monthly")

# 캠핑장 상세 페이지
for c in camps:
    slug = c.get("slug", "")
    if slug:
        u(f"/camp/{slug}/", "0.7", "monthly")

xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(xml)

print(f"sitemap.xml 생성 완료: {len(urls)}개 URL")
