import asyncio
from scripts.crawler_base import run_crawler

if __name__ == "__main__":
    asyncio.run(run_crawler(
        category_slug="tuyen-sinh",
        category_name_vi="Tuyển sinh",
        category_name_en="Admissions",
        url_base="https://vienktcn.vinhuni.edu.vn/tuyen-sinh",
        url_keyword="/tuyen-sinh/",
        max_pages=8,
        max_articles=40
    ))
