import re

def find_ids():
    sql_path = "articles_export.sql"
    ids_to_find = [
        "a3318bc5-d830-4ee4-81b4-632f6c73c5b1",
        "374642e4-6d03-4edc-9c24-5f2a2faef54b"
    ]
    
    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    for i in ids_to_find:
        if i in content:
            print(f"✅ Found ID {i} in SQL file!")
            # Trích xuất dòng chứa ID này
            lines = content.split("\n")
            for idx, line in enumerate(lines):
                if i in line:
                    print(f"  Line {idx+1}: {line[:200]}...")
        else:
            print(f"❌ ID {i} NOT found in SQL file.")

if __name__ == "__main__":
    find_ids()
