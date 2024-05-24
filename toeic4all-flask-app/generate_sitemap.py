import datetime

routes = [
    '/',
    '/part5/test',
    '/board',
    '/user-detail',
    '/mypage',
    '/mynote',
    '/my-learning-analysis',
    '/rank',
    '/voca-test',
    '/myvoca'
]

sitemap_template = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""

url_template = """
<url>
  <loc>{loc}</loc>
  <lastmod>{lastmod}Z</lastmod>
  <changefreq>{changefreq}</changefreq>
  <priority>{priority}</priority>
</url>
"""

urls = []

# 웹사이트의 각 페이지에 대해:
for route in routes:
    url = url_template.format(
        loc="https://toeic4all.com" + route,
        lastmod=datetime.datetime.utcnow().replace(microsecond=0).isoformat(),
        changefreq="weekly",
        priority=0.8
    )
    urls.append(url)

sitemap = sitemap_template.format(urls="".join(urls))

# 사이트맵을 파일로 저장
with open("./static/sitemap.xml", "w") as f:
    f.write(sitemap)
