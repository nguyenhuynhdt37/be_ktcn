import asyncio
from scripts.crawler_base import run_crawler

if __name__ == "__main__":
    asyncio.run(run_crawler(
        category_slug="dao-tao",
        category_name_vi="Đào tạo",
        category_name_en="Education",
        url_base="https://vienktcn.vinhuni.edu.vn/dao-tao",
        url_keyword="/dao-tao/",
        max_pages=8,
        max_articles=40
    ))
