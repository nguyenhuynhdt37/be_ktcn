import asyncio
from scripts.crawler_base import run_crawler

if __name__ == "__main__":
    asyncio.run(run_crawler(
        category_slug="sinh-vien",
        category_name_vi="Sinh viên",
        category_name_en="Students",
        url_base="https://vienktcn.vinhuni.edu.vn/sinh-vien",
        url_keyword="/sinh-vien/",
        max_pages=8,
        max_articles=40
    ))
