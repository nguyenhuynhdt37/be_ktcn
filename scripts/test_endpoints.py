import urllib.request
import json
import sys

def main():
    print("Bắt đầu gọi API để kiểm tra...")
    
    # 1. Test Menu Tree API
    menu_url = "http://localhost:8000/api/v1/portal/menus/header/tree?lang=vi"
    print(f"Fetching Menu Tree from: {menu_url}")
    try:
        req = urllib.request.Request(menu_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("Kết nối thành công tới Menu Tree API!")
            
            # Print the header root items
            items = data.get("items", [])
            print(f"Số lượng menu gốc: {len(items)}")
            for item in items:
                title = item.get("title")
                item_id = item.get("id")
                children_count = len(item.get("children", []))
                print(f"Root Menu: {title} (ID: {item_id}) | Children: {children_count}")
                
                # Check children of "Giới thiệu"
                if "giới thiệu" in title.lower():
                    for child in item.get("children", []):
                        child_title = child.get("title")
                        sub_children_count = len(child.get("children", []))
                        target_type = child.get("target_type")
                        target_id = child.get("target_id")
                        print(f"  ├─ {child_title} (Target: {target_type}, TargetID: {target_id}) | Children: {sub_children_count}")
                        
                        # Print sub-children
                        for sub_child in child.get("children", []):
                            print(f"    ├─ {sub_child.get('title')} (Target: {sub_child.get('target_type')})")
    except Exception as e:
        print(f"Lỗi khi gọi Menu Tree API: {e}")
        
    # 2. Test Category Tree API
    cat_url = "http://localhost:8000/api/v1/portal/categories/tree?lang=vi"
    print(f"\nFetching Category Tree from: {cat_url}")
    try:
        req = urllib.request.Request(cat_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("Kết nối thành công tới Category Tree API!")
            
            # Print the category root items
            print(f"Số lượng category gốc: {len(data)}")
            for item in data:
                name = item.get("name")
                item_id = item.get("id")
                children_count = len(item.get("children", []))
                print(f"Root Category: {name} (ID: {item_id}) | Children: {children_count}")
                
                # Check children of "Giới thiệu"
                if "giới thiệu" in name.lower():
                    for child in item.get("children", []):
                        child_name = child.get("name")
                        sub_children_count = len(child.get("children", []))
                        print(f"  ├─ {child_name} | Children: {sub_children_count}")
                        
                        # Print sub-children
                        for sub_child in child.get("children", []):
                            print(f"    ├─ {sub_child.get('name')}")
    except Exception as e:
        print(f"Lỗi khi gọi Category Tree API: {e}")

    # 3. Test Staff List API for Department
    depts_to_test = ["khoa-cong-nghe-thong-tin", "van-phong-truong"]
    for slug in depts_to_test:
        staff_url = f"http://localhost:8000/api/v1/portal/staffs?department_slug={slug}&lang=vi"
        print(f"\nFetching Staffs for Department slug '{slug}' from: {staff_url}")
        try:
            req = urllib.request.Request(staff_url)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                print(f"Kết nối thành công tới Staff List API cho khoa: {slug}!")
                print(f"Số lượng giảng viên/cán bộ: {len(data)}")
                for s in data:
                    name = s.get("full_name")
                    pos = s.get("position", {}).get("name") if s.get("position") else "No Position"
                    deg = s.get("degree") or ""
                    title = s.get("academic_title") or ""
                    # Combine academic title and degree
                    title_deg = ", ".join(filter(None, [title, deg]))
                    print(f"  - Staff: {name} | Chức danh: {pos} | Học hàm/học vị: {title_deg} | Slug: {s.get('slug')}")
        except Exception as e:
            print(f"Lỗi khi gọi Staff List API cho khoa {slug}: {e}")

if __name__ == "__main__":
    main()

