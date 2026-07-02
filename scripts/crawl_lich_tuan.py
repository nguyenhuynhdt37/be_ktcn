import asyncio
from scripts.crawler_base import run_crawler

if __name__ == "__main__":
    asyncio.run(run_crawler(
        category_slug="lich-tuan",
        category_name_vi="Lịch tuần",
        category_name_en="Weekly Calendar",
        url_base="https://vienktcn.vinhuni.edu.vn/lich-tuan",
        url_keyword="/lich-tuan/",
        max_pages=8,
        max_articles=40
    ))
