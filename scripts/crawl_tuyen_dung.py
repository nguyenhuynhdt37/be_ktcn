import asyncio
from scripts.crawler_base import run_crawler

if __name__ == "__main__":
    asyncio.run(run_crawler(
        category_slug="tuyen-dung",
        category_name_vi="Tuyển dụng",
        category_name_en="Recruitment",
        url_base="https://vienktcn.vinhuni.edu.vn/tuyen-dung",
        url_keyword="/tuyen-dung/",
        max_pages=8,
        max_articles=40
    ))
