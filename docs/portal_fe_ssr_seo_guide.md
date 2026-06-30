# Hướng dẫn tối ưu hóa SSR & SEO cho Front-end (Next.js App Router)

Tài liệu này hướng dẫn chi tiết các kỹ thuật tối ưu hóa Server-Side Rendering (SSR) và SEO khi gọi APIs bài viết Portal từ backend.

---

## 1. Nguyên tắc cốt lõi của SEO & SSR
Để tối ưu hóa SEO "cực gắt", bot tìm kiếm (Google, Facebook, Zalo...) **không được phép chờ đợi** Javascript render dữ liệu ở Client. HTML tải về ban đầu từ Server bắt buộc phải chứa sẵn:
1. **Các thẻ Meta Tags cơ bản:** `<title>`, `<meta name="description">`, `<meta name="robots">`.
2. **Các thẻ OpenGraph (Mạng xã hội):** `<meta property="og:title">`, `og:description`, `og:image`.
3. **Canonical Link:** `<link rel="canonical" href="...">` nhằm tránh trùng lặp nội dung.
4. **Structured Data (JSON-LD):** Cấu trúc dữ liệu bài viết để hiển thị Rich Snippets trên trang kết quả Google.

---

## 2. Chiến lược Fetching dữ liệu tối ưu trên Server

Đối với Next.js App Router, chúng ta gọi API trực tiếp trong Server Components và sử dụng hàm `generateMetadata` chạy trên Server.

### Kỹ thuật 1: Tránh gọi trùng lặp API (Request Deduping)
Next.js tự động tối ưu hóa (dedupe) các request `fetch` giống nhau trong cùng một chu kỳ render. Nghĩa là nếu bạn call cùng một URL trong `generateMetadata` và trong Component Page, Next.js **chỉ gửi duy nhất 1 request** đến backend.

### Kỹ thuật 2: Sử dụng Incremental Static Regeneration (ISR)
Chi tiết bài viết hiếm khi thay đổi nội dung liên tục. Nếu mỗi request từ người dùng đều bắt Server gọi Database backend (Pure SSR) sẽ khiến trang tải chậm và quá tải Database.
* **Giải pháp:** Sử dụng `revalidate` để cache trang trên Server trong một khoảng thời gian (ví dụ 60 giây).

---

## 3. Code mẫu tối ưu hóa hoàn chỉnh (Next.js App Router)

Dưới đây là cách triển khai tối ưu SEO và hiệu năng cho file `app/articles/[slug]/page.tsx`:

```tsx
import { Metadata } from 'next';
import React from 'react';
import { notFound } from 'next/navigation';

// Cấu hình URL API Backend (đọc từ biến môi trường của FE)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Props {
  params: { slug: string };
}

// ==========================================
// 1. TỐI ƯU SEO: RENDER META TAGS TRÊN SERVER
// ==========================================
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = params;

  try {
    // Gọi API chi tiết bài viết (Public API) trên Server
    const res = await fetch(`${API_URL}/api/v1/articles/portal/${slug}`, {
      next: { revalidate: 60 } // ISR: Cache trang 60 giây để tối ưu tốc độ phản hồi
    });

    if (!res.ok) {
      return { title: 'Không tìm thấy bài viết | Viện Kỹ thuật và Công nghệ' };
    }

    const article = await res.json();

    return {
      title: article.seo_title,
      description: article.seo_description,
      alternates: {
        canonical: article.canonical_url || undefined,
      },
      robots: article.robots || "index, follow",
      openGraph: {
        title: article.og_title || article.seo_title,
        description: article.og_description || article.seo_description,
        images: article.og_image_url ? [{ url: article.og_image_url, alt: article.title }] : [],
        type: 'article',
        publishedTime: article.publish_at || article.created_at,
        modifiedTime: article.updated_at || article.created_at,
        authors: [article.author?.full_name || 'Viện Kỹ thuật và Công nghệ'],
      },
      twitter: {
        card: 'summary_large_image',
        title: article.og_title || article.seo_title,
        description: article.og_description || article.seo_description,
        images: article.og_image_url ? [article.og_image_url] : [],
      }
    };
  } catch (error) {
    return { title: 'Lỗi tải trang | Viện Kỹ thuật và Công nghệ' };
  }
}

// ==========================================
// 2. COMPONENT CHÍNH: RENDER NỘI DUNG & STRUCTURED DATA
// ==========================================
export default async function ArticleDetailPage({ params }: Props) {
  const { slug } = params;

  // Gọi API (Next.js sẽ dedupe với request trong generateMetadata ở trên nên không lo bị gọi 2 lần)
  const res = await fetch(`${API_URL}/api/v1/articles/portal/${slug}`, {
    next: { revalidate: 60 } // Đồng bộ thời gian cache
  });

  if (!res.ok) {
    if (res.status === 404) {
      notFound(); // Trả về trang 404 chuẩn của Next.js
    }
    throw new Error('Lỗi tải dữ liệu bài viết');
  }

  const article = await res.json();

  return (
    <article className="max-w-4xl mx-auto px-4 py-8">
      {/* 2.1 CHÈN JSON-LD STRUCTURED DATA ĐÃ DỰNG SẴN TỪ BACKEND ĐỂ GOOGLE BOT ĐỌC LẬP TỨC */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(article.json_ld) }}
      />

      <header className="mb-8 border-b pb-6">
        {article.category && (
          <span className="text-blue-600 font-bold text-sm uppercase tracking-wider">
            {article.category.name}
          </span>
        )}
        
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 mb-4 leading-tight">
          {article.title}
        </h1>

        <div className="flex flex-wrap items-center text-sm text-gray-500 gap-4">
          <div className="flex items-center space-x-2">
            {article.author?.avatar_url && (
              <img 
                src={article.author.avatar_url} 
                alt={article.author.full_name} 
                className="w-6 h-6 rounded-full object-cover"
              />
            )}
            <span className="font-semibold text-gray-700">{article.author?.full_name}</span>
          </div>
          <span>•</span>
          <span>Đăng lúc: {new Date(article.publish_at || article.created_at).toLocaleDateString('vi-VN')}</span>
          <span>•</span>
          <span>Thời gian đọc: ~{article.reading_time} phút</span>
        </div>
      </header>

      {article.cover_url && (
        <div className="mb-8 overflow-hidden rounded-xl shadow-lg aspect-video relative">
          <img
            src={article.cover_url}
            alt={article.title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* 2.2 RENDER NỘI DUNG HTML CHỮA PROSE CSS ĐỂ ĐẸP TỰ NHIÊN */}
      <div 
        className="prose prose-lg max-w-none text-gray-800 leading-relaxed font-serif"
        dangerouslySetInnerHTML={{ __html: article.content }}
      />

      {/* Tag liên kết */}
      {article.tags && article.tags.length > 0 && (
        <div className="mt-12 pt-6 border-t flex flex-wrap gap-2">
          {article.tags.map((tag: any) => (
            <span 
              key={tag.id}
              className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-full cursor-pointer transition-colors"
              style={{ borderLeft: `3px solid ${tag.color || '#ccc'}` }}
            >
              #{tag.name}
            </span>
          ))}
        </div>
      )}

      {/* 2.3 TRÁNH CACHE ẢNH HƯỞNG VIEW COUNT: GỌI NGHẦM CLIENT-SIDE ĐỂ ĐẾM VIEW THỰC */}
      <ViewCounterTrigger slug={slug} />
    </article>
  );
}

// ==========================================
// 3. COMPONENT CON TRIGGER VIEW_COUNT (CLIENT-SIDE)
// ==========================================
// Đặt file client trigger nhỏ này để tăng view thực mà không làm mất hiệu năng cache của server.
'use client';
import { useEffect } from 'react';

function ViewCounterTrigger({ slug }: { slug: string }) {
  useEffect(() => {
    // Gọi ngầm lên api portal lúc client render xong để backend ghi nhận view_count tăng lên
    // Dùng headers cache control no-cache để đảm bảo browser không cache request này
    fetch(`${API_URL}/api/v1/articles/portal/${slug}`, {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    }).catch((err) => console.log("Silent view trigger error:", err));
  }, [slug]);

  return null;
}
