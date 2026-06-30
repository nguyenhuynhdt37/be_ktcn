import httpx
import json

# URL API của Backend Portal
url = "http://localhost:8000/api/v1/articles/portal"

def test_portal_api():
    print("=== BẮT ĐẦU KIỂM THỬ API PORTAL CLIENT ===")
    
    # 1. Test trường hợp mặc định không truyền tham số
    try:
        r = httpx.get(url, params={"page": 1, "page_size": 5})
        print(f"1. Lấy tin mặc định: Status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   -> Tổng số tin: {data.get('total_items')}")
            print(f"   -> Số tin trả về: {len(data.get('items', []))}")
            if data.get('items'):
                first_item = data['items'][0]
                print(f"   -> Tiêu đề tin đầu: '{first_item.get('title')}'")
                print(f"   -> Ghim trang chủ (is_pinned): {first_item.get('is_pinned')}")
                print(f"   -> Nổi bật (is_featured): {first_item.get('is_featured')}")
        else:
            print(f"   -> Thất bại: {r.text}")
    except Exception as e:
        print(f"   -> Lỗi kết nối: {e}")

    # 2. Test bộ lọc kết hợp phức tạp (Tìm kiếm + cờ nổi bật)
    try:
        params = {
            "search": "Hội nghị",
            "is_featured": True,
            "page": 1,
            "page_size": 10
        }
        r = httpx.get(url, params=params)
        print(f"\n2. Lọc phức tạp (Tìm kiếm 'Hội nghị' + Nổi bật=True): Status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   -> Tìm thấy: {data.get('total_items')} bài")
            for item in data.get('items', []):
                print(f"      - [Nổi bật={item.get('is_featured')}] {item.get('title')[:60]}...")
        else:
            print(f"   -> Thất bại: {r.text}")
    except Exception as e:
        print(f"   -> Lỗi: {e}")

    # 3. Test lọc theo category_slug và tag_slug
    try:
        # Lấy thử một vài danh mục
        params = {
            "category_slug": "tin-tuc-va-su-kien",
            "page_size": 3
        }
        r = httpx.get(url, params=params)
        print(f"\n3. Lọc theo category_slug 'tin-tuc-va-su-kien': Status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   -> Lấy được: {len(data.get('items', []))} bài thuộc chuyên mục")
        else:
            print(f"   -> Thất bại: {r.text}")
    except Exception as e:
        print(f"   -> Lỗi: {e}")

    # 4. Test sắp xếp thủ công theo lượt xem (Custom Sort Override)
    try:
        params = {
            "sort_by": "view_count",
            "sort_dir": "desc",
            "page_size": 3
        }
        r = httpx.get(url, params=params)
        print(f"\n4. Sắp xếp thủ công theo lượt xem (view_count desc): Status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            for item in data.get('items', []):
                print(f"      - [Lượt xem: {item.get('view_count')}] {item.get('title')[:60]}...")
        else:
            print(f"   -> Thất bại: {r.text}")
    except Exception as e:
        print(f"   -> Lỗi: {e}")

if __name__ == "__main__":
    test_portal_api()
