import asyncio
from scripts.crawler_base import run_crawler

if __name__ == "__main__":
    asyncio.run(run_crawler(
        category_slug="thong-bao",
        category_name_vi="Thông báo",
        category_name_en="Announcements",
        url_base="https://vienktcn.vinhuni.edu.vn/thong-bao",
        url_keyword="/thong-bao/",
        max_pages=8,
        max_articles=40
    ))
