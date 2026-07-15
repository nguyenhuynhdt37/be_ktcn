from bs4 import BeautifulSoup

from scripts.crawl_legacy_programs_raw import (
    _resolved_document_url,
    _response_asset_name,
    content_asset_urls,
    extract_elements,
    visible_text,
)

SAMPLE_HTML = r"""
<html>
  <head><meta name="description" content="Trang thử"></head>
  <body>
    <nav><a href="/home">Trang chủ</a></nav>
    <div class="post-content">
      <p>Mã ngành: 7489999</p>
      <table><tr><th>Thuộc tính</th><th>Giá trị</th></tr>
      <tr><td>Tùy ý</td><td>Dữ liệu gốc</td></tr></table>
      <a href="/files/source.pdf" data-id="7">Tệp nguồn</a>
      <a href="\DATA\documents\legacy.pdf">Tệp đường dẫn cũ</a>
      <img src="/images/source.png" alt="Ảnh nguồn">
    </div>
  </body>
</html>
"""


def test_raw_extractor_keeps_generic_page_data_without_domain_mapping() -> None:
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    content = soup.select_one(".post-content")
    assert content is not None

    result = extract_elements(content, "https://example.edu/program")

    assert "fields" not in result
    assert result["links"][0]["url"] == "https://example.edu/files/source.pdf"
    assert result["links"][0]["attributes"]["data-id"] == "7"
    assert result["links"][1]["url"] == (
        "https://example.edu/DATA/documents/legacy.pdf"
    )
    assert result["images"][0]["url"] == "https://example.edu/images/source.png"
    assert result["tables"][0]["rows"] == [
        ["Thuộc tính", "Giá trị"],
        ["Tùy ý", "Dữ liệu gốc"],
    ]
    assert "Mã ngành: 7489999" in visible_text(content)


def test_external_document_links_are_kept_as_asset_candidates() -> None:
    soup = BeautifulSoup(
        '<div><a href="https://cutt.ly/0ny10kU">K60</a>'
        '<a href="https://example.edu/article">Bài viết</a></div>',
        "html.parser",
    )

    elements = extract_elements(soup, "https://example.edu/program")

    assert content_asset_urls(elements) == ["https://cutt.ly/0ny10kU"]


def test_verified_short_link_becomes_direct_google_drive_download() -> None:
    resolved_url, download_url = _resolved_document_url(
        "https://cutt.ly/0ny10kU"
    )

    assert resolved_url == (
        "https://drive.google.com/file/d/1s0T3v0DD3ceQ1OWGjONWuGMmbdFBVBB3/"
        "view?usp=sharing"
    )
    assert download_url == (
        "https://drive.usercontent.google.com/download"
        "?id=1s0T3v0DD3ceQ1OWGjONWuGMmbdFBVBB3"
        "&export=download&authuser=0&confirm=t"
    )


def test_content_disposition_filename_repairs_legacy_utf8_header() -> None:
    class Response:
        headers = {
            "Content-Disposition": (
                'attachment; filename="Báº£n mÃ´ táº£ chÆ°Æ¡ng trÃ¬nh.pdf"'
            )
        }
        url = "https://example.edu/download"

    assert _response_asset_name(Response(), Response.url, 1) == (
        "001_Bản mô tả chương trình.pdf"
    )
