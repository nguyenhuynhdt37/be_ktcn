from bs4 import BeautifulSoup

with open("/tmp/bm_dieu_khien_tu_dong.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

pblist = soup.find(class_="pblist")
if pblist:
    print("--- FIRST PBLIST BLOCK HTML ---")
    print(pblist.prettify())
else:
    print("No pblist class found!")


