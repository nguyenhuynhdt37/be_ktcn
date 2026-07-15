"""Crawl the eight legacy undergraduate program pages without touching the DB.

The command writes a detailed JSON export and a compact CSV summary to
``scratch/legacy_programs`` by default. All imported URLs are kept absolute so
the result can be reviewed before a later CMS import step.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://vienktcn.vinhuni.edu.vn/"
ROBOTS_URL = urljoin(BASE_URL, "robots.txt")
USER_AGENT = "KTCN-Legacy-Migration/1.0"


@dataclass(frozen=True)
class ProgramSource:
    key: str
    expected_name: str
    menu_url: str
    source_url: str


PROGRAM_SOURCES = (
    ProgramSource(
        key="electronics_telecommunications",
        expected_name="Kỹ thuật Điện tử - Viễn thông",
        menu_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "ky-thuat-dien-tu-vien-thong-106157",
        ),
        source_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "ky-thuat-dien-tu-vien-thong-106157",
        ),
    ),
    ProgramSource(
        key="automation_control",
        expected_name="Kỹ thuật Điều khiển và Tự động hóa",
        menu_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "ky-thuat-dieu-khien-va-tu-dong-hoa-77323",
        ),
        source_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "ky-thuat-dieu-khien-va-tu-dong-hoa-77323",
        ),
    ),
    ProgramSource(
        key="electrical_electronics",
        expected_name="Công nghệ kỹ thuật Điện - Điện tử",
        menu_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "ky-thuat-dien-dien-tu-77327",
        ),
        source_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "ky-thuat-dien-dien-tu-77327",
        ),
    ),
    ProgramSource(
        key="information_technology",
        expected_name="Công nghệ thông tin",
        menu_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "cong-nghe-thong-tin-77317",
        ),
        source_url=urljoin(
            BASE_URL,
            "dao-tao/dao-tao-dai-hoc/seo/chuong-trinh-dao-tao-nganh-"
            "cong-nghe-thong-tin-77317",
        ),
    ),
    ProgramSource(
        key="information_technology_high_quality",
        expected_name="Công nghệ thông tin hệ Chất lượng cao",
        menu_url=urljoin(BASE_URL, "administration/update/admin/itemid/87044"),
        source_url=urljoin(
            BASE_URL,
            "tuyen-sinh/nganh-cong-nghe-thong-tin/seo/chuong-trinh-dao-tao-"
            "nganh-cong-nghe-thong-tin-he-chat-luong-cao-87044",
        ),
    ),
    ProgramSource(
        key="automotive_engineering_technology",
        expected_name="Công nghệ kỹ thuật Ô tô",
        menu_url=urljoin(BASE_URL, "tuyen-sinh/nganh-cong-nghe-ky-thuat-oto"),
        source_url=urljoin(
            BASE_URL,
            "dao-tao/seo/chuong-trinh-dao-tao-nganh-cong-nghe-ky-thuat-o-to-97093",
        ),
    ),
    ProgramSource(
        key="thermal_engineering_technology",
        expected_name="Công nghệ kỹ thuật Nhiệt (Nhiệt - Điện lạnh)",
        menu_url=urljoin(
            BASE_URL, "tuyen-sinh/nganh-cong-nghe-ky-thuat-nhiet-dien-lanh"
        ),
        source_url=urljoin(
            BASE_URL,
            "dao-tao/seo/muc-tieu-chuan-dau-ra-chuong-trinh-dao-tao-nganh-"
            "cong-nghe-ky-thuat-nhiet-109649",
        ),
    ),
    ProgramSource(
        key="electronics_informatics",
        expected_name="Kỹ thuật Điện tử và Tin học",
        menu_url=urljoin(
            BASE_URL,
            "dao-tao/seo/chuong-trinh-dao-tao-nganh-ky-thuat-dien-tu-va-"
            "tin-hoc-2021-106101",
        ),
        source_url=urljoin(
            BASE_URL,
            "dao-tao/seo/chuong-trinh-dao-tao-nganh-ky-thuat-dien-tu-va-"
            "tin-hoc-2021-106101",
        ),
    ),
)


FIELD_PATTERNS: dict[str, tuple[str, ...]] = {
    "program_name": (
        r"tên chương trình",
        r"tên ngành đào tạo",
        r"ngành đào tạo \(tiếng việt\)",
        r"ngành đào tạo",
        r"ngành",
    ),
    "english_name": (
        r"(?:tên chương trình )?\(?tiếng anh\)?",
        r"ngành (?:đào tạo )?\(?tiếng anh\)?",
    ),
    "program_code": (
        r"mã (?:số )?ngành(?: đào tạo)?",
        r"mã số",
        r"mã ngành thí điểm",
    ),
    "degree_level": (
        r"trình độ đào tạo",
        r"bậc học",
    ),
    "training_mode": (
        r"loại hình đào tạo",
        r"hình thức đào tạo",
    ),
    "duration": (r"thời gian(?: đào tạo)?",),
    "total_credits": (
        r"(?:tổng )?số tín chỉ(?: yêu cầu)?",
        r"khối lượng kiến thức toàn khóa",
    ),
    "degree_awarded": (
        r"văn bằng được cấp",
        r"tên văn bằng tốt nghiệp",
    ),
}

METADATA_LABEL_PATTERN = re.compile(
    r"(?:^|\s)(?:\d+[.)]\s*)?(?P<label>"
    r"tên chương trình|tên ngành đào tạo|chuyên ngành|"
    r"ngành đào tạo \(tiếng việt\)|ngành \(tiếng việt\)|"
    r"\(tiếng anh\)|ngành đào tạo|(?<!chuyên )\bngành\b|"
    r"mã số ngành đào tạo|mã ngành đào tạo|mã ngành thí điểm|mã số|mã ngành|"
    r"trình độ đào tạo|bậc học|loại hình đào tạo|hình thức đào tạo|"
    r"thời gian đào tạo|thời gian|khối lượng kiến thức toàn khóa|"
    r"tổng số tín chỉ|số tín chỉ yêu cầu|số tín chỉ|"
    r"văn bằng được cấp|tên văn bằng tốt nghiệp|"
    r"đơn vị được giao nhiệm vụ đào tạo|thang điểm|ngôn ngữ sử dụng|"
    r"ngày tháng ban hành|phiên bản chỉnh sửa|"
    r"mục tiêu chương trình đào tạo|mục tiêu tổng quát|mục tiêu chung"
    r")\s*:",
    flags=re.IGNORECASE,
)

DOCUMENT_EXTENSIONS = {
    ".doc",
    ".docx",
    ".pdf",
    ".ppt",
    ".pptx",
    ".rar",
    ".xls",
    ".xlsx",
    ".zip",
}


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def normalize_label(value: str) -> str:
    value = normalize_space(value).casefold().rstrip(":：")
    return re.sub(r"^[\-–—+\d.()\s]+", "", value).strip()


def build_session() -> requests.Session:
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=0.75,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "vi,en;q=0.8",
            "User-Agent": USER_AGENT,
        }
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def load_robots(session: requests.Session, timeout: float) -> RobotFileParser:
    response = session.get(ROBOTS_URL, timeout=timeout)
    response.raise_for_status()
    parser = RobotFileParser(ROBOTS_URL)
    parser.parse(response.text.splitlines())
    return parser


def _consume_rowspan(
    row: list[str], spans: dict[int, tuple[int, str]], column: int
) -> int:
    while column in spans:
        remaining, value = spans[column]
        row.append(value)
        if remaining <= 1:
            del spans[column]
        else:
            spans[column] = (remaining - 1, value)
        column += 1
    return column


def table_to_rows(table: Tag) -> list[list[str]]:
    """Expand basic rowspan/colspan values into a rectangular text grid."""
    rows: list[list[str]] = []
    spans: dict[int, tuple[int, str]] = {}

    for html_row in table.find_all("tr"):
        row: list[str] = []
        column = _consume_rowspan(row, spans, 0)
        for cell in html_row.find_all(["th", "td"], recursive=False):
            column = _consume_rowspan(row, spans, column)
            value = normalize_space(cell.get_text(" ", strip=True))
            colspan = max(int(cell.get("colspan", 1) or 1), 1)
            rowspan = max(int(cell.get("rowspan", 1) or 1), 1)
            for offset in range(colspan):
                row.append(value)
                if rowspan > 1:
                    spans[column + offset] = (rowspan - 1, value)
            column += colspan

        if spans:
            last_column = max(spans)
            while column <= last_column:
                if column in spans:
                    column = _consume_rowspan(row, spans, column)
                else:
                    row.append("")
                    column += 1
        if any(row):
            rows.append(row)

    width = max((len(row) for row in rows), default=0)
    return [row + [""] * (width - len(row)) for row in rows]


def _nearby_table_title(table: Tag) -> str | None:
    candidate = table.find_previous(["h2", "h3", "h4", "h5", "strong", "p"])
    if candidate is None:
        return None
    title = normalize_space(candidate.get_text(" ", strip=True))
    return title if 0 < len(title) <= 250 else None


def extract_tables(content: Tag) -> list[dict[str, Any]]:
    result = []
    for index, table in enumerate(content.find_all("table"), start=1):
        rows = table_to_rows(table)
        result.append(
            {
                "index": index,
                "title": _nearby_table_title(table),
                "row_count": len(rows),
                "column_count": max((len(row) for row in rows), default=0),
                "rows": rows,
            }
        )
    return result


def _field_candidates(
    content: Tag, tables: list[dict[str, Any]]
) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for table in tables:
        for row in table["rows"]:
            for index in range(len(row) - 1):
                candidates.append((row[index], row[index + 1]))

    text = normalize_space(content.get_text(" ", strip=True))[:5000]
    matches = list(METADATA_LABEL_PATTERN.finditer(text))
    for index, match in enumerate(matches):
        value_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(text)
        )
        value = normalize_space(text[match.end() : value_end])
        if value:
            candidates.append((match.group("label"), value))
    return candidates


def _clean_field_value(field: str, value: str) -> str | None:
    value = normalize_space(value).strip(" :：")
    if field == "program_code":
        match = re.search(r"\b\d[\d.]{4,}(?:\s*[A-Z]+)?(?:\s*\([^)]*\))?", value)
        return match.group(0) if match else None
    if field == "total_credits":
        match = re.search(r"\b\d{2,3}(?:\s*tín chỉ)?\b", value, re.IGNORECASE)
        return match.group(0) if match else None
    if field == "duration":
        match = re.search(
            r"\b\d+(?:[,.]\d+)?\s*năm(?:\s*\([^)]*\))?",
            value,
            re.IGNORECASE,
        )
        return match.group(0) if match else None
    if field == "degree_level":
        match = re.search(
            r"\b(?:đại học|sau đại học|thạc sĩ|thạc sỹ|tiến sĩ)\b",
            value,
            re.IGNORECASE,
        )
        return match.group(0) if match else None
    if field == "program_name":
        value = re.split(
            r"\s+(?:chuyên ngành|trình độ đào tạo|mã ngành|\(ban hành)",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
    return value or None


def _match_field(
    field: str, candidates: list[tuple[str, str]], patterns: tuple[str, ...]
) -> str | None:
    for label, value in candidates:
        normalized = normalize_label(label)
        if not any(re.fullmatch(pattern, normalized) for pattern in patterns):
            continue
        clean_value = _clean_field_value(field, value)
        if clean_value and normalize_label(clean_value) != normalized:
            return clean_value
    return None


def extract_fields(content: Tag, tables: list[dict[str, Any]]) -> dict[str, str]:
    candidates = _field_candidates(content, tables)

    fields: dict[str, str] = {}
    for field, patterns in FIELD_PATTERNS.items():
        value = _match_field(field, candidates, patterns)
        if value is not None:
            fields[field] = value
    return fields


def _absolute_url(page_url: str, raw_url: str | None) -> str | None:
    if not raw_url or raw_url.startswith(("data:", "javascript:", "mailto:")):
        return None
    return urljoin(page_url, raw_url.strip())


def clean_content(content: Tag, page_url: str) -> BeautifulSoup:
    cleaned = BeautifulSoup(str(content), "html.parser")
    root = cleaned.select_one(".post-content") or cleaned
    for unwanted in root.select("script, style, iframe, noscript, form"):
        unwanted.decompose()
    for tag in root.find_all(True):
        for attribute in tuple(tag.attrs):
            if attribute.casefold().startswith("on"):
                del tag.attrs[attribute]
    for anchor in root.select("a[href]"):
        absolute = _absolute_url(page_url, anchor.get("href"))
        if absolute:
            anchor["href"] = absolute
    for image in root.select("img[src]"):
        absolute = _absolute_url(page_url, image.get("src"))
        if absolute:
            image["src"] = absolute
        image.attrs.pop("srcset", None)
    return cleaned


def extract_documents(content: Tag, page_url: str) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in content.select("a[href]"):
        url = _absolute_url(page_url, anchor.get("href"))
        if not url or url in seen:
            continue
        extension = Path(urlparse(url).path).suffix.casefold()
        if extension in DOCUMENT_EXTENSIONS or "download" in url.casefold():
            seen.add(url)
            documents.append(
                {
                    "text": normalize_space(anchor.get_text(" ", strip=True)),
                    "url": url,
                    "extension": extension,
                }
            )
    return documents


def extract_links(content: Tag, page_url: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in content.select("a[href]"):
        url = _absolute_url(page_url, anchor.get("href"))
        if not url or url in seen:
            continue
        seen.add(url)
        links.append(
            {
                "text": normalize_space(anchor.get_text(" ", strip=True)),
                "url": url,
            }
        )

    for raw_url in re.findall(
        r"https?://[^\s<>\"]+", content.get_text(" ", strip=True)
    ):
        url = raw_url.rstrip(".,;:)")
        if url not in seen:
            seen.add(url)
            links.append({"text": "", "url": url})
    return links


def extract_images(content: Tag, page_url: str) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    seen: set[str] = set()
    for image in content.select("img[src]"):
        url = _absolute_url(page_url, image.get("src"))
        if not url or url in seen:
            continue
        seen.add(url)
        images.append(
            {
                "alt": normalize_space(image.get("alt", "")),
                "url": url,
            }
        )
    return images


def extract_published_at(detail: Tag) -> tuple[str | None, str | None]:
    text = detail.get_text(" ", strip=True)
    match = re.search(
        r"(?P<time>\d{1,2}:\d{2})\s+(?P<date>\d{1,2}/\d{1,2}/\d{4})", text
    )
    if not match:
        return None, None
    raw = match.group(0)
    parsed = datetime.strptime(raw, "%H:%M %d/%m/%Y")
    return raw, parsed.isoformat(timespec="minutes")


def parse_program_page(html: bytes | str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    detail = soup.select_one(".detail-post")
    title_node = soup.select_one("h1.post-title")
    content = soup.select_one(".post-content")
    if detail is None or title_node is None or content is None:
        raise ValueError(
            "Không tìm thấy .detail-post, h1.post-title hoặc .post-content"
        )

    tables = extract_tables(content)
    fields = extract_fields(content, tables)
    published_at_raw, published_at_local = extract_published_at(detail)
    cleaned = clean_content(content, page_url)
    cleaned_root = cleaned.select_one(".post-content") or cleaned
    content_html = cleaned_root.decode_contents().strip()
    content_text = normalize_space(content.get_text(" ", strip=True))

    warnings = []
    for key in ("program_name", "program_code", "degree_level", "duration"):
        if key not in fields:
            warnings.append(f"Không nhận diện được trường {key}")
    if not tables:
        warnings.append("Trang không có bảng dữ liệu")

    return {
        "title": normalize_space(title_node.get_text(" ", strip=True)),
        "published_at_raw": published_at_raw,
        "published_at_local": published_at_local,
        "fields": fields,
        "content_text": content_text,
        "content_html": content_html,
        "content_hash": hashlib.sha256(content_html.encode("utf-8")).hexdigest(),
        "tables": tables,
        "links": extract_links(content, page_url),
        "documents": extract_documents(content, page_url),
        "images": extract_images(content, page_url),
        "warnings": warnings,
    }


def crawl_source(
    session: requests.Session,
    robots: RobotFileParser | None,
    source: ProgramSource,
    timeout: float,
) -> dict[str, Any]:
    started_at = datetime.now(UTC).isoformat()
    base_result: dict[str, Any] = {
        **asdict(source),
        "status": "failed",
        "http_status": None,
        "final_url": None,
        "crawled_at": started_at,
    }
    try:
        if robots is not None and not robots.can_fetch(USER_AGENT, source.source_url):
            raise PermissionError("robots.txt không cho phép crawl URL này")
        response = session.get(source.source_url, timeout=timeout)
        base_result["http_status"] = response.status_code
        base_result["final_url"] = response.url
        response.raise_for_status()
        parsed = parse_program_page(response.content, response.url)
        return {**base_result, "status": "success", **parsed}
    except (requests.RequestException, PermissionError, ValueError) as exc:
        return {**base_result, "error": f"{type(exc).__name__}: {exc}"}


def write_outputs(payload: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "legacy_programs.json"
    csv_path = output_dir / "legacy_programs_summary.csv"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fieldnames = (
        "key",
        "expected_name",
        "status",
        "http_status",
        "title",
        "program_name",
        "program_code",
        "degree_level",
        "duration",
        "total_credits",
        "table_count",
        "document_count",
        "link_count",
        "image_count",
        "warning_count",
        "source_url",
        "content_hash",
        "error",
    )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for program in payload["programs"]:
            fields = program.get("fields", {})
            writer.writerow(
                {
                    "key": program["key"],
                    "expected_name": program["expected_name"],
                    "status": program["status"],
                    "http_status": program.get("http_status"),
                    "title": program.get("title"),
                    "program_name": fields.get("program_name"),
                    "program_code": fields.get("program_code"),
                    "degree_level": fields.get("degree_level"),
                    "duration": fields.get("duration"),
                    "total_credits": fields.get("total_credits"),
                    "table_count": len(program.get("tables", [])),
                    "document_count": len(program.get("documents", [])),
                    "link_count": len(program.get("links", [])),
                    "image_count": len(program.get("images", [])),
                    "warning_count": len(program.get("warnings", [])),
                    "source_url": program["source_url"],
                    "content_hash": program.get("content_hash"),
                    "error": program.get("error"),
                }
            )
    return json_path, csv_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl 8 trang chương trình đào tạo cũ, không ghi database."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scratch/legacy_programs"),
        help="Thư mục chứa JSON/CSV (mặc định: scratch/legacy_programs).",
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=[source.key for source in PROGRAM_SOURCES],
        help="Chỉ crawl key được chọn; có thể truyền nhiều lần.",
    )
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument(
        "--skip-robots-check",
        action="store_true",
        help="Bỏ kiểm tra robots.txt; chỉ dùng khi đã có cho phép riêng.",
    )
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parse_args()
    sources = [
        source
        for source in PROGRAM_SOURCES
        if not args.only or source.key in set(args.only)
    ]
    session = build_session()
    robots = None
    if not args.skip_robots_check:
        try:
            robots = load_robots(session, args.timeout)
        except requests.RequestException as exc:
            print(f"Không tải được robots.txt: {exc}", file=sys.stderr)
            return 2

    programs = []
    for index, source in enumerate(sources):
        print(f"[{index + 1}/{len(sources)}] {source.expected_name}", flush=True)
        programs.append(crawl_source(session, robots, source, args.timeout))
        if index + 1 < len(sources) and args.delay > 0:
            time.sleep(args.delay)

    success_count = sum(item["status"] == "success" for item in programs)
    payload = {
        "schema_version": 1,
        "dry_run": True,
        "source_site": BASE_URL,
        "crawler_user_agent": USER_AGENT,
        "generated_at": datetime.now(UTC).isoformat(),
        "requested_count": len(programs),
        "success_count": success_count,
        "failure_count": len(programs) - success_count,
        "programs": programs,
    }
    json_path, csv_path = write_outputs(payload, args.output_dir)
    print(f"Hoàn tất: {success_count}/{len(programs)} trang thành công", flush=True)
    print(f"JSON: {json_path.resolve()}", flush=True)
    print(f"CSV:  {csv_path.resolve()}", flush=True)
    return 0 if success_count == len(programs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
