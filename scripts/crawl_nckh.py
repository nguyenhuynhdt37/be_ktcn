import asyncio
from scripts.crawler_base import run_crawler

if __name__ == "__main__":
    asyncio.run(run_crawler(
        category_slug="nghien-cuu-khoa-hoc",
        category_name_vi="Nghiên cứu khoa học",
        category_name_en="Scientific Research",
        url_base="https://vienktcn.vinhuni.edu.vn/nghien-cuu-khoa-hoc",
        url_keyword="/nghien-cuu-khoa-hoc/",
        max_pages=8,
        max_articles=40
    ))
