"""Create lossless, raw-first snapshots of the eight legacy program pages.

This crawler deliberately avoids mapping legacy content to CMS/domain fields.
Each page is saved as original HTML plus generic DOM inventories so the content
team can decide the final presentation and data model after reviewing it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import UTC, datetime
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, Tag

try:
    from scripts.crawl_legacy_programs import (
        BASE_URL,
        PROGRAM_SOURCES,
        USER_AGENT,
        build_session,
        load_robots,
        normalize_space,
        table_to_rows,
    )
except ModuleNotFoundError:
    from crawl_legacy_programs import (  # type: ignore[no-redef]
        BASE_URL,
        PROGRAM_SOURCES,
        USER_AGENT,
        build_session,
        load_robots,
        normalize_space,
        table_to_rows,
    )

CONTENT_SELECTOR = ".post-content"
DOWNLOADABLE_EXTENSIONS = {
    ".csv",
    ".doc",
    ".docx",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".rar",
    ".svg",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}
EXTERNAL_DOCUMENT_HOSTS = {"bit.ly", "cutt.ly", "drive.google.com"}
LEGACY_EXTERNAL_DOCUMENT_TARGETS = {
    "http://bit.ly/3q7b7qO": (
        "https://drive.google.com/file/d/1N5NlPkLOzjW5R0x4GhWeonQxYtcGTsHd/"
        "view?usp=sharing"
    ),
    "https://cutt.ly/0ny10kU": (
        "https://drive.google.com/file/d/1s0T3v0DD3ceQ1OWGjONWuGMmbdFBVBB3/"
        "view?usp=sharing"
    ),
    "https://cutt.ly/Zny0yp5": (
        "https://drive.google.com/file/d/1rDt-t_CI1YxHxr4erbgr5IevpI9b4b3N/"
        "view?usp=sharing"
    ),
    "https://cutt.ly/Nny0opX": (
        "https://drive.google.com/file/d/1SxDieJ3wQyQHyZYooOMrfcP7D3tu8nu4/"
        "view?usp=sharing"
    ),
}
GOOGLE_DRIVE_FILE_PATTERN = re.compile(r"drive\.google\.com/file/d/([^/?#]+)")


def _json_attributes(tag: Tag) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in tag.attrs.items():
        if isinstance(value, list):
            result[key] = [str(item) for item in value]
        else:
            result[key] = str(value)
    return result


def _absolute_http_url(page_url: str, raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    # The legacy editor stored several root-relative file URLs with Windows
    # backslashes (for example ``\DATA\...``), which browsers tolerate poorly.
    normalized_url = raw_url.strip().replace("\\", "/")
    url = urljoin(page_url, normalized_url)
    return url if urlparse(url).scheme in {"http", "https"} else None


def extract_elements(scope: Tag | BeautifulSoup, page_url: str) -> dict[str, Any]:
    links = []
    for index, anchor in enumerate(scope.select("a[href]"), start=1):
        links.append(
            {
                "index": index,
                "text": normalize_space(anchor.get_text(" ", strip=True)),
                "raw_href": anchor.get("href"),
                "url": _absolute_http_url(page_url, anchor.get("href")),
                "attributes": _json_attributes(anchor),
            }
        )

    images = []
    for index, image in enumerate(scope.select("img"), start=1):
        images.append(
            {
                "index": index,
                "alt": normalize_space(image.get("alt", "")),
                "raw_src": image.get("src"),
                "url": _absolute_http_url(page_url, image.get("src")),
                "attributes": _json_attributes(image),
            }
        )

    tables = []
    for index, table in enumerate(scope.select("table"), start=1):
        rows = table_to_rows(table)
        tables.append(
            {
                "index": index,
                "attributes": _json_attributes(table),
                "row_count": len(rows),
                "column_count": max((len(row) for row in rows), default=0),
                "rows": rows,
                "raw_html": str(table),
            }
        )

    resources = []
    for index, element in enumerate(
        scope.select("script[src], link[href], source[src], video[src], audio[src]"),
        start=1,
    ):
        raw_url = element.get("src") or element.get("href")
        resources.append(
            {
                "index": index,
                "tag": element.name,
                "raw_url": raw_url,
                "url": _absolute_http_url(page_url, raw_url),
                "attributes": _json_attributes(element),
            }
        )

    return {
        "links": links,
        "images": images,
        "tables": tables,
        "resources": resources,
    }


def extract_meta(soup: BeautifulSoup) -> list[dict[str, Any]]:
    return [
        {"index": index, "attributes": _json_attributes(tag)}
        for index, tag in enumerate(soup.select("meta"), start=1)
    ]


def visible_text(scope: Tag | BeautifulSoup) -> str:
    lines = []
    for raw_line in scope.get_text("\n", strip=True).splitlines():
        line = normalize_space(raw_line)
        if line:
            lines.append(line)
    return "\n".join(lines) + "\n"


def content_asset_urls(content_elements: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for image in content_elements["images"]:
        url = image.get("url")
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    for link in content_elements["links"]:
        url = link.get("url")
        if not url or url in seen:
            continue
        extension = Path(urlparse(url).path).suffix.casefold()
        hostname = (urlparse(url).hostname or "").casefold()
        if (
            extension in DOWNLOADABLE_EXTENSIONS
            or hostname in EXTERNAL_DOCUMENT_HOSTS
        ):
            seen.add(url)
            urls.append(url)
    return urls


def _safe_asset_name(url: str, index: int) -> str:
    basename = unquote(Path(urlparse(url).path).name) or "resource"
    basename = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", basename).strip(" .")
    basename = basename[:140] or "resource"
    return f"{index:03d}_{basename}"


def _resolved_document_url(url: str) -> tuple[str, str]:
    resolved_url = LEGACY_EXTERNAL_DOCUMENT_TARGETS.get(url, url)
    drive_match = GOOGLE_DRIVE_FILE_PATTERN.search(resolved_url)
    if not drive_match:
        return resolved_url, resolved_url
    file_id = drive_match.group(1)
    download_url = (
        "https://drive.usercontent.google.com/download"
        f"?id={file_id}&export=download&authuser=0&confirm=t"
    )
    return resolved_url, download_url


def _response_asset_name(
    response: requests.Response, download_url: str, index: int
) -> str:
    disposition = response.headers.get("Content-Disposition")
    if disposition:
        message = Message()
        message["Content-Disposition"] = disposition
        filename = message.get_filename()
        if filename:
            try:
                filename = filename.encode("latin-1").decode("utf-8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass
            return _safe_asset_name(filename, index)
    return _safe_asset_name(response.url or download_url, index)


def download_asset(
    session: requests.Session,
    url: str,
    assets_dir: Path,
    index: int,
    timeout: float,
    max_bytes: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {"url": url, "status": "failed"}
    try:
        resolved_url, download_url = _resolved_document_url(url)
        if resolved_url != url:
            result["resolved_url"] = resolved_url
        response = session.get(
            download_url,
            timeout=timeout,
            stream=True,
            headers={"Accept": "*/*", "Referer": BASE_URL},
        )
        result.update(
            {
                "http_status": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("Content-Type"),
            }
        )
        response.raise_for_status()
        declared_size = int(response.headers.get("Content-Length", 0) or 0)
        if declared_size > max_bytes:
            return {
                **result,
                "status": "skipped",
                "reason": f"Content-Length vượt giới hạn {max_bytes} bytes",
            }

        chunks: list[bytes] = []
        downloaded_size = 0
        digest = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            downloaded_size += len(chunk)
            if downloaded_size > max_bytes:
                return {
                    **result,
                    "status": "skipped",
                    "reason": f"Dữ liệu vượt giới hạn {max_bytes} bytes",
                }
            digest.update(chunk)
            chunks.append(chunk)

        assets_dir.mkdir(parents=True, exist_ok=True)
        filename = _response_asset_name(response, download_url, index)
        target = assets_dir / filename
        target.write_bytes(b"".join(chunks))
        return {
            **result,
            "status": "success",
            "size_bytes": downloaded_size,
            "sha256": digest.hexdigest(),
            "local_file": str(Path("assets") / filename),
        }
    except (OSError, requests.RequestException, ValueError) as exc:
        return {**result, "error": f"{type(exc).__name__}: {exc}"}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def snapshot_page(
    session: requests.Session,
    robots: RobotFileParser | None,
    source: Any,
    page_dir: Path,
    timeout: float,
    max_asset_bytes: int,
) -> dict[str, Any]:
    started_at = datetime.now(UTC).isoformat()
    result: dict[str, Any] = {
        "key": source.key,
        "menu_label": source.expected_name,
        "menu_url": source.menu_url,
        "source_url": source.source_url,
        "status": "failed",
        "crawled_at": started_at,
    }
    try:
        if robots is not None and not robots.can_fetch(USER_AGENT, source.source_url):
            raise PermissionError("robots.txt không cho phép crawl URL này")
        response = session.get(source.source_url, timeout=timeout)
        result.update(
            {
                "http_status": response.status_code,
                "final_url": response.url,
                "encoding": response.encoding,
                "response_headers": dict(response.headers),
            }
        )
        response.raise_for_status()

        page_dir.mkdir(parents=True, exist_ok=True)
        raw_html_path = page_dir / "raw.html"
        raw_html_path.write_bytes(response.content)

        soup = BeautifulSoup(response.content, "html.parser")
        content = soup.select_one(CONTENT_SELECTOR)
        content_scope: Tag | BeautifulSoup = content or soup
        page_elements = extract_elements(soup, response.url)
        content_elements = extract_elements(content_scope, response.url)

        (page_dir / "content.html").write_text(str(content_scope), encoding="utf-8")
        (page_dir / "content.txt").write_text(
            visible_text(content_scope), encoding="utf-8"
        )
        write_json(page_dir / "page_elements.json", page_elements)
        write_json(page_dir / "content_elements.json", content_elements)
        write_json(page_dir / "meta.json", extract_meta(soup))

        asset_urls = content_asset_urls(content_elements)
        assets = [
            download_asset(
                session,
                url,
                page_dir / "assets",
                index,
                timeout,
                max_asset_bytes,
            )
            for index, url in enumerate(asset_urls, start=1)
        ]
        write_json(page_dir / "assets.json", assets)

        result.update(
            {
                "status": "success",
                "content_selector_found": content is not None,
                "raw_size_bytes": len(response.content),
                "raw_sha256": hashlib.sha256(response.content).hexdigest(),
                "html_title": normalize_space(soup.title.get_text())
                if soup.title
                else None,
                "counts": {
                    "page_links": len(page_elements["links"]),
                    "page_images": len(page_elements["images"]),
                    "page_tables": len(page_elements["tables"]),
                    "content_links": len(content_elements["links"]),
                    "content_images": len(content_elements["images"]),
                    "content_tables": len(content_elements["tables"]),
                    "asset_candidates": len(asset_urls),
                    "assets_downloaded": sum(
                        asset["status"] == "success" for asset in assets
                    ),
                },
                "local_files": {
                    "raw_html": "raw.html",
                    "content_html": "content.html",
                    "content_text": "content.txt",
                    "page_elements": "page_elements.json",
                    "content_elements": "content_elements.json",
                    "meta": "meta.json",
                    "assets": "assets.json",
                },
            }
        )
    except (OSError, PermissionError, requests.RequestException, ValueError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    page_dir.mkdir(parents=True, exist_ok=True)
    write_json(page_dir / "page.json", result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lưu snapshot nguyên trạng 8 trang chương trình cũ; không ánh xạ "
            "trường nghiệp vụ và không ghi database."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("scratch/legacy_programs_raw"),
    )
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-asset-mb", type=int, default=200)
    parser.add_argument(
        "--only",
        action="append",
        choices=[source.key for source in PROGRAM_SOURCES],
    )
    parser.add_argument("--skip-robots-check", action="store_true")
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parse_args()
    selected_keys = set(args.only or [])
    sources = [
        source
        for source in PROGRAM_SOURCES
        if not selected_keys or source.key in selected_keys
    ]
    session = build_session()
    robots = None if args.skip_robots_check else load_robots(session, args.timeout)
    max_asset_bytes = args.max_asset_mb * 1024 * 1024

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for index, source in enumerate(sources, start=1):
        print(f"[{index}/{len(sources)}] {source.expected_name}", flush=True)
        page_dir = args.output_dir / f"{index:02d}_{source.key}"
        pages.append(
            snapshot_page(
                session,
                robots,
                source,
                page_dir,
                args.timeout,
                max_asset_bytes,
            )
        )
        if index < len(sources) and args.delay > 0:
            time.sleep(args.delay)

    success_count = sum(page["status"] == "success" for page in pages)
    manifest = {
        "schema_version": 1,
        "mode": "raw_snapshot",
        "domain_fields_extracted": False,
        "database_writes": False,
        "source_site": BASE_URL,
        "generated_at": datetime.now(UTC).isoformat(),
        "requested_count": len(pages),
        "success_count": success_count,
        "failure_count": len(pages) - success_count,
        "pages": pages,
    }
    manifest_path = args.output_dir / "manifest.json"
    write_json(manifest_path, manifest)
    print(f"Hoàn tất: {success_count}/{len(pages)} trang", flush=True)
    print(f"Manifest: {manifest_path.resolve()}", flush=True)
    return 0 if success_count == len(pages) else 1


if __name__ == "__main__":
    raise SystemExit(main())
