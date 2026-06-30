from bs4 import BeautifulSoup

with open("/tmp/homepage.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

vinhmenu = soup.find(class_="vinhmenuhome")
if vinhmenu:
    print("--- VINHMENUHOME HTML ---")
    print(vinhmenu.prettify())
else:
    print("No class vinhmenuhome found!")


