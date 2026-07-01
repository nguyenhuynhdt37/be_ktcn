import httpx
import json

def test_category_endpoints():
    base_url = "http://localhost:8000/api/v1/categories"
    
    print("🚀 1. Gửi request lấy danh sách categories...")
    try:
        response = httpx.get(base_url, timeout=10.0)
    except Exception as e:
        print(f"❌ Lỗi kết nối server: {str(e)}")
        print("Đảm bảo uvicorn đang chạy trên cổng 8000.")
        return
        
    if response.status_code != 200:
        print(f"❌ Lỗi lấy danh sách, status code: {response.status_code}")
        return
        
    categories = response.json()
    print(f"✅ Đã nhận {len(categories)} danh mục từ server.")
    
    if not categories:
        print("⚠️ Không có danh mục nào trong database để test.")
        return
        
    # Lấy ID của danh mục đầu tiên
    first_cat = categories[0]
    cat_id = first_cat["id"]
    cat_name = first_cat.get("translations", {}).get("vi", {}).get("name", "Không có tên")
    print(f"\n📂 Chọn danh mục mẫu: Name='{cat_name}', ID={cat_id}")
    
    # 2. Gửi request lấy chi tiết
    detail_url = f"{base_url}/{cat_id}"
    print(f"🚀 2. Gửi request lấy chi tiết: GET {detail_url}")
    detail_res = httpx.get(detail_url, timeout=10.0)
    
    if detail_res.status_code != 200:
        print(f"❌ Lỗi lấy chi tiết, status code: {detail_res.status_code}")
        print(detail_res.text)
        return
        
    detail_data = detail_res.json()
    print("✅ Lấy chi tiết thành công! Phản hồi JSON nhận được:")
    print(json.dumps(detail_data, indent=2, ensure_ascii=False))
    
    # Kiểm tra sự tồn tại của translations
    if "translations" in detail_data:
        print("\n🎉 XÁC THỰC THÀNH CÔNG: API phản hồi có chứa trường 'translations'!")
        translations = detail_data["translations"]
        if translations:
            print("✨ Các ngôn ngữ có bản dịch:")
            for lang, trans_data in translations.items():
                print(f"  - [{lang}]: Tên='{trans_data.get('name')}', Slug='{trans_data.get('slug')}'")
        else:
            print("⚠️ Trường translations có dạng rỗng.")
    else:
        print("❌ LỖI: Không tìm thấy trường 'translations' trong response detail!")

    # 3. Gửi request lấy Tree
    tree_url = f"http://localhost:8000/api/v1/categories/tree"
    print(f"\n🚀 3. Gửi request lấy cấu trúc cây: GET {tree_url}")
    tree_res = httpx.get(tree_url, timeout=10.0)
    
    if tree_res.status_code != 200:
        print(f"❌ Lỗi lấy cây danh mục, status code: {tree_res.status_code}")
        print(tree_res.text)
        return
        
    tree_data = tree_res.json()
    print(f"✅ Lấy cây danh mục thành công! Số lượng root nodes: {len(tree_data)}")
    if tree_data:
        print("🎄 Node đầu tiên trên cây:")
        print(json.dumps(tree_data[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_category_endpoints()
