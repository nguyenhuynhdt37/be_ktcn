import httpx
from bs4 import BeautifulSoup

url = "https://vienktcn.vinhuni.edu.vn/tin-tuc-va-su-kien/seo/vien-ky-thuat-va-cong-nghe-to-chuc-thanh-cong-dai-hoi-cong-doan-bo-phan-nhiem-ky-2025-2030-143132"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = httpx.get(url, headers=headers, verify=False, timeout=30.0)
soup = BeautifulSoup(response.content, "html.parser")

print("TITLE:", soup.find("title").text.strip() if soup.find("title") else "None")

# Tìm div.post-content hoặc div.detail-post
detail_post = soup.find(class_="detail-post")
if not detail_post:
    detail_post = soup.find(class_="post-content")

if detail_post:
    print("\n--- DETAIL POST FOUND ---")
    
    # Tìm tiêu đề trong detail-post (thường là h1 hoặc h2, hoặc h3)
    h1 = detail_post.find("h1")
    if h1:
        print("Detail H1 Title:", h1.text.strip())
        
    # Tìm ngày đăng: thường có text dạng dd/mm/yyyy hoặc các class liên quan đến date, time, calendar
    # Hãy tìm tất cả các thẻ span, p xem có text chứa ngày/tháng/năm không
    print("\n--- POTENTIAL DATE/TIME TAGS ---")
    for tag in detail_post.find_all(["span", "p", "div", "i"]):
        text = tag.text.strip()
        if any(char.isdigit() for char in text) and ("/" in text or ":" in text) and len(text) < 100:
            print(f"Tag: <{tag.name} class={tag.get('class')}> -> '{text}'")
            
    # Tìm các ảnh trong detail_post
    print("\n--- IMAGES IN DETAIL POST ---")
    imgs = detail_post.find_all("img")
    print(f"Total images: {len(imgs)}")
    for idx, img in enumerate(imgs):
        src = img.get("src", "")
        # Nếu là base64 thì chỉ in độ dài
        if src.startswith("data:image"):
            print(f"Img {idx}: [Base64 Image, length={len(src)}], alt={img.get('alt')}")
        else:
            print(f"Img {idx}: src={src}, alt={img.get('alt')}")
            
    # Xem cấu trúc text của detail_post
    print("\n--- TEXT PREVIEW (FIRST 500 CHARS) ---")
    print(detail_post.text.strip()[:500] + "...")
else:
    print("No detail-post or post-content class found.")
