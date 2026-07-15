from scripts.crawl_legacy_programs import parse_program_page, table_to_rows

SAMPLE_HTML = """
<html><body>
  <div class="detail-post">
    <span>08:01 23/03/2022</span>
    <h1 class="post-title">Chương trình đào tạo thử nghiệm</h1>
    <div class="post-content">
      <table>
        <tr><td>Tên chương trình:</td><td>KỸ THUẬT THỬ NGHIỆM</td></tr>
        <tr><td>Mã ngành:</td><td>7489999</td></tr>
        <tr><td>Trình độ đào tạo:</td><td>Đại học</td></tr>
        <tr><td>Thời gian đào tạo:</td><td>4,5 năm</td></tr>
        <tr><td>Số tín chỉ:</td><td>150</td></tr>
      </table>
      <h2>Khung chương trình</h2>
      <table>
        <tr><th rowspan="2">TT</th><th colspan="2">Học phần</th></tr>
        <tr><th>Mã</th><th>Tên</th></tr>
        <tr><td>1</td><td>TST10001</td><td>Nhập môn</td></tr>
      </table>
      <a href="/files/program.pdf">Tải chương trình</a>
      <img src="/images/program.jpg" alt="Ảnh chương trình">
      <script>alert('removed')</script>
    </div>
  </div>
</body></html>
"""


def test_parse_program_page_extracts_structured_data() -> None:
    result = parse_program_page(SAMPLE_HTML, "https://example.edu/program")

    assert result["title"] == "Chương trình đào tạo thử nghiệm"
    assert result["published_at_local"] == "2022-03-23T08:01"
    assert result["fields"]["program_name"] == "KỸ THUẬT THỬ NGHIỆM"
    assert result["fields"]["program_code"] == "7489999"
    assert result["fields"]["total_credits"] == "150"
    assert len(result["tables"]) == 2
    assert result["links"][0]["url"] == "https://example.edu/files/program.pdf"
    assert result["documents"][0]["url"] == "https://example.edu/files/program.pdf"
    assert result["images"][0]["url"] == "https://example.edu/images/program.jpg"
    assert "<script" not in result["content_html"]
    assert len(result["content_hash"]) == 64


def test_table_to_rows_expands_rowspan_and_colspan() -> None:
    soup = __import__("bs4").BeautifulSoup(SAMPLE_HTML, "html.parser")
    rows = table_to_rows(soup.select("table")[1])

    assert rows == [
        ["TT", "Học phần", "Học phần"],
        ["TT", "Mã", "Tên"],
        ["1", "TST10001", "Nhập môn"],
    ]
