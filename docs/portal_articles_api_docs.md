# Hướng dẫn tích hợp API Portal Articles cho Front-end (FE)

Tài liệu này hướng dẫn cách gọi API lấy danh sách bài viết theo danh mục và chi tiết bài viết cho Portal Client, cấu hình SEO Meta, xử lý phân trang và tích hợp dữ liệu cấu trúc Schema.org.

---

## 1. API 1: Lấy danh sách bài viết theo danh mục (Public)

* **Endpoint:** `GET /api/v1/categories/{category_slug}/articles`
* **Xác thực:** Không (Public API)
* **Phương thức:** `GET`
* **Query Parameters:**
  * `page` (`int`, mặc định `1`): Số trang cần lấy.
  * `page_size` (`int`, mặc định `10`): Số lượng bài viết trên trang.
* **Đặc điểm:** Mảng `items` trả về đã được sắp xếp: bài ghim (`is_pinned = true`) lên đầu, sau đó đến thời gian xuất bản giảm dần (`publish_at DESC`).

---

## 2. API 2: Lấy chi tiết bài viết theo Slug (Public & Tối ưu SEO cực gắt)

* **Endpoint:** `GET /api/v1/articles/portal/{slug}`
* **Xác thực:** Không (Public API)
* **Phương thức:** `GET`
* **Mục đích:** Lấy toàn bộ nội dung chi tiết bài viết cùng với dữ liệu cấu trúc SEO & OpenGraph đã được backend tối ưu hóa tối đa.

### Cấu trúc Response Chi tiết bài viết (`PortalArticleDetailResponse`):
```typescript
interface PortalArticleDetail {
  id: string;                    // UUID
  title: string;                 // Tiêu đề
  slug: string;                  // Đường dẫn thân thiện
  excerpt: string | null;        // Tóm tắt ngắn
  content: string;               // Nội dung HTML chi tiết
  thumbnail_url: string | null;  // URL tuyệt đối ảnh thumbnail
  cover_url: string | null;      // URL tuyệt đối ảnh bìa
  category: {
    id: string;
    name: string;
    slug: string;
  } | null;
  tags: Array<{
    id: string;
    name: string;
    slug: string;
    color: string | null;
  }>;
  author: {
    id: string;
    username: string;
    full_name: string;
    avatar_url: string | null;
  } | null;
  view_count: number;            // Tổng lượt xem (Tự động tăng 1 đơn vị sau mỗi lần FE gọi API này)
  word_count: number;            // Số lượng từ của bài viết
  reading_time: number;          // Thời gian đọc ước tính (phút)
  publish_at: string | null;     
  published_at: string | null;   
  created_at: string;
  updated_at: string | null;
  
  // SEO & OpenGraph Meta (Được backend xử lý fallback tự động)
  seo_title: string;             // Tiêu đề SEO (nếu rỗng sẽ tự lấy title)
  seo_description: string;       // Mô tả SEO (nếu rỗng sẽ tự bóc tách text từ content)
  canonical_url: string;         // URL canonical chính thống (tự sinh dạng: {fe_url}/articles/{slug})
  robots: string;                // Chỉ thị robot (mặc định: "index, follow")
  og_title: string;              
  og_description: string;        
  og_image_url: string | null;   // URL ảnh OpenGraph tuyệt đối (fallback qua thumbnail hoặc cover)
  
  // JSON-LD Structured Data
  json_ld: {
    "@context": "https://schema.org";
    "@type": "NewsArticle";
    "headline": string;
    "image": string[];
    "datePublished": string;
    "dateModified": string;
    "author": {
      "@type": "Person";
      "name": string;
    };
    "publisher": {
      "@type": "Organization";
      "name": "Viện Kỹ thuật và Công nghệ - Đại học Vinh";
      "logo": {
        "@type": "ImageObject";
        "url": string;
      }
    };
    "description": string;
  };
}
```

---

## 3. Hướng dẫn Tích hợp & Tối ưu SEO cho Front-end (Next.js SSR)

Khi người dùng click xem chi tiết bài viết, FE sử dụng Next.js Server-Side Rendering (hoặc Server Component) để gọi API và chèn thẻ Meta, kèm theo chèn dữ liệu cấu trúc `json_ld` để tối ưu SEO.

### Ví dụ code React / Next.js (`app/articles/[slug]/page.tsx`):
```tsx
import { Metadata } from 'next';
import React from 'react';

// 1. Cấu hình các thẻ Meta SEO từ API (Next.js generateMetadata)
export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const res = await fetch(`http://localhost:8000/api/v1/articles/portal/${params.slug}`, {
    next: { revalidate: 60 } // Cache và ISR trong 60 giây
  });
  
  if (!res.ok) return { title: 'Không tìm thấy bài viết' };
  
  const article = await res.json();

  return {
    title: article.seo_title,
    description: article.seo_description,
    alternates: {
      canonical: article.canonical_url,
    },
    robots: article.robots,
    openGraph: {
      title: article.og_title,
      description: article.og_description,
      images: article.og_image_url ? [{ url: article.og_image_url }] : [],
      type: 'article',
      publishedTime: article.publish_at || article.created_at,
      modifiedTime: article.updated_at || article.created_at,
      authors: [article.author?.full_name || 'Viện Kỹ thuật và Công nghệ'],
    },
  };
}

// 2. Component Render nội dung & Structured Data
export default async function ArticleDetailPage({ params }: { params: { slug: string } }) {
  const res = await fetch(`http://localhost:8000/api/v1/articles/portal/${params.slug}`, {
    next: { revalidate: 60 }
  });
  
  if (!res.ok) {
    return <div className="text-center py-20 text-red-500 font-semibold">Không tìm thấy bài viết!</div>;
  }
  
  const article = await res.json();

  return (
    <article className="max-w-4xl mx-auto px-4 py-8">
      {/* CHÈN SCHEMA JSON-LD STRUCTURED DATA CHO GOOGLE BOT */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(article.json_ld) }}
      />

      {/* Hiển thị nội dung bài viết */}
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-4">{article.title}</h1>
        <div className="flex items-center text-sm text-gray-500 space-x-4">
          <span>Tác giả: <strong>{article.author?.full_name}</strong></span>
          <span>•</span>
          <span>Ngày đăng: {new Date(article.publish_at).toLocaleDateString('vi-VN')}</span>
          <span>•</span>
          <span>Lượt xem: {article.view_count}</span>
          <span>•</span>
          <span>Thời gian đọc: {article.reading_time} phút</span>
        </div>
      </header>

      {article.cover_url && (
        <img
          src={article.cover_url}
          alt={article.title}
          className="w-full h-auto rounded-lg mb-8 shadow-md"
        />
      )}

      {/* Render HTML Content an toàn */}
      <div 
        className="prose prose-lg max-w-none text-gray-800"
        dangerouslySetInnerHTML={{ __html: article.content }}
      />
    </article>
  );
}
```
