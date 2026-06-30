import os
from PIL import Image, ImageChops

def trim_white_borders(image_path, output_path):
    print(f"🖼️ Đang xử lý crop ảnh: {image_path}")
    if not os.path.exists(image_path):
        print(f"❌ File không tồn tại: {image_path}")
        return False
        
    im = Image.open(image_path)
    
    # Chuyển sang RGBA nếu chưa có
    if im.mode != "RGBA":
        im = im.convert("RGBA")
        
    # Lấy màu pixel góc trái trên làm màu nền (thường là màu trắng hoặc gần trắng)
    bg_pixel = im.getpixel((5, 5))
    
    # Tạo ảnh nền để so sánh
    bg = Image.new("RGBA", im.size, bg_pixel)
    
    # Tính toán sự khác biệt
    diff = ImageChops.difference(im, bg)
    
    # Chuyển về RGB để lấy bounding box chính xác hơn
    diff_rgb = diff.convert("RGB")
    bbox = diff_rgb.getbbox()
    
    if bbox:
        # Thêm một chút padding (ví dụ 2px) để tránh cắt lẹm vào chi tiết cờ
        left, top, right, bottom = bbox
        left = max(0, left - 2)
        top = max(0, top - 2)
        right = min(im.size[0], right + 2)
        bottom = min(im.size[1], bottom + 2)
        
        cropped_im = im.crop((left, top, right, bottom))
        
        # Save ảnh đã được crop
        cropped_im.save(output_path, "PNG")
        print(f"✅ Đã crop thành công và lưu tại: {output_path}")
        return True
    else:
        print("⚠️ Không tìm thấy bounding box phù hợp, lưu bản sao nguyên gốc.")
        im.save(output_path, "PNG")
        return False

if __name__ == "__main__":
    # Các ảnh cờ chuyên nghiệp đã sinh
    flags = [
        {
            "src": "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/vietnam_flag_professional_1782836782629.png",
            "dest": "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/vietnam_cropped.png"
        },
        {
            "src": "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/uk_flag_professional_1782836845194.png",
            "dest": "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/uk_cropped.png"
        },
        {
            "src": "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/laos_flag_professional_1782836830976.png",
            "dest": "/Users/huynh/.gemini/antigravity-ide/brain/15f2f8b1-8add-47de-b5b9-faa3ec9ec352/laos_cropped.png"
        }
    ]
    
    for flag in flags:
        trim_white_borders(flag["src"], flag["dest"])
