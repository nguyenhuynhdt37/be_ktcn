# OmniRoute Integration & Operations Guide

Thư mục này chứa cấu hình Docker Compose độc lập và tài liệu liên quan để vận hành **OmniRoute** làm AI Gateway cho dự án.

---

## 1. Giới thiệu

**OmniRoute** (được triển khai bằng LiteLLM) đóng vai trò là một AI Router/Gateway trung gian. Nó cho phép backend của dự án giao tiếp qua một giao thức chuẩn duy nhất (OpenAI-compatible API) và tự động định tuyến đến các nhà cung cấp khác nhau như OpenAI, Gemini, Anthropic, Ollama, v.v.

Ưu điểm:
- Thay đổi cấu hình định tuyến, API Key của các AI provider trực tiếp trên OmniRoute mà không cần restart hay sửa đổi code backend.
- Hỗ trợ Load Balancing, Fallback, và Tracking lượng Token sử dụng.

---

## 2. Cách khởi chạy OmniRoute

### Bước 1: Thiết lập biến môi trường (Optional)
Nếu bạn định tuyến tới các dịch vụ Cloud như OpenAI, Gemini hay Anthropic, hãy export API Key tương ứng trước khi chạy docker-compose:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Bước 2: Khởi chạy docker-compose
Chạy lệnh sau tại thư mục này (`deployment/omniroute/`):

```bash
docker-compose up -d
```

OmniRoute sẽ chạy tại cổng `8090` của local machine.

---

## 3. Cấu hình Backend Kết Nối OmniRoute

Để chuyển hệ thống backend sang sử dụng OmniRoute, hãy cấu hình các biến môi trường sau trong file `.env` của backend:

```env
AI_PROVIDER="omniroute"
AI_BASE_URL="http://localhost:8090"
AI_API_KEY="sk-omniroute-secret-key"
AI_DEFAULT_MODEL="gpt-4o"
```

Khi cấu hình này được kích hoạt, mọi yêu cầu từ `AIService` trong dự án sẽ được chuyển tiếp qua cổng `8090` của OmniRoute để định tuyến thông minh.
