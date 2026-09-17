"""Bounded, local parsers for P1 URL and attachment imports."""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from ipaddress import ip_address
from urllib.parse import urljoin, urlparse

import httpx

from app.config import get_settings
from app.providers import OCRProvider, ProviderUnavailable


class ImportParseError(RuntimeError):
    """A safe, user-facing import failure with a stable error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ParsedUnit:
    content: str
    unit_type: str
    sequence: int
    metadata: dict[str, object]


@dataclass(frozen=True)
class FetchedPage:
    original_url: str
    final_url: str
    title: str | None
    text: str
    snapshot: bytes
    media_type: str


FILE_FORMATS: dict[str, tuple[str, str]] = {
    ".txt": ("text", "text"),
    ".md": ("markdown", "text"),
    ".markdown": ("markdown", "text"),
    ".json": ("json", "text"),
    ".yaml": ("yaml", "text"),
    ".yml": ("yaml", "text"),
    ".log": ("log", "text"),
    ".pdf": ("pdf", "pdf"),
    ".png": ("image", "image"),
    ".jpg": ("image", "image"),
    ".jpeg": ("image", "image"),
    ".webp": ("image", "image"),
    ".gif": ("image", "image"),
    ".bmp": ("image", "image"),
    ".tif": ("image", "image"),
    ".tiff": ("image", "image"),
}

MIME_FORMATS: dict[str, tuple[str, str]] = {
    "text/plain": ("text", "text"),
    "text/markdown": ("markdown", "text"),
    "application/json": ("json", "text"),
    "application/yaml": ("yaml", "text"),
    "text/yaml": ("yaml", "text"),
    "text/x-log": ("log", "text"),
    "application/pdf": ("pdf", "pdf"),
}


def detect_file_format(filename: str, media_type: str | None) -> tuple[str, str]:
    extension = filename.lower().rsplit(".", maxsplit=1)
    suffix = f".{extension[-1]}" if len(extension) == 2 else ""
    if suffix in FILE_FORMATS:
        return FILE_FORMATS[suffix]
    normalized = (media_type or "").split(";", maxsplit=1)[0].strip().lower()
    if normalized in MIME_FORMATS:
        return MIME_FORMATS[normalized]
    if normalized.startswith("image/"):
        return "image", "image"
    raise ImportParseError("unsupported_media_type", "Unsupported file type")


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_file(
    data: bytes,
    *,
    filename: str,
    media_type: str | None,
    ocr_provider: OCRProvider | None = None,
) -> tuple[str, str, list[ParsedUnit], dict[str, object]]:
    content_format, kind = detect_file_format(filename, media_type)
    if kind == "text":
        return (
            content_format,
            "document",
            [
                ParsedUnit(
                    content=decode_text(data),
                    unit_type="file_text",
                    sequence=0,
                    metadata={"filename": filename, "format": content_format},
                )
            ],
            {},
        )
    if kind == "pdf":
        units = parse_pdf(data, filename=filename, ocr_provider=ocr_provider)
        return content_format, "pdf", units, {"page_count": len(units)}
    if kind == "image":
        if ocr_provider is None:
            raise ImportParseError("ocr_unavailable", "Local OCR provider is unavailable")
        try:
            text = ocr_provider.extract(
                data,
                language=get_settings().ocr_lang,
                timeout_seconds=get_settings().ocr_timeout_seconds,
            )
        except ProviderUnavailable as exc:
            raise ImportParseError("ocr_failed", str(exc)) from exc
        return (
            "ocr",
            "image",
            [
                ParsedUnit(
                    content=text,
                    unit_type="image_ocr",
                    sequence=0,
                    metadata={
                        "filename": filename,
                        "ocr_provider": ocr_provider.name,
                        "ocr_model": ocr_provider.model,
                        "ocr_language": get_settings().ocr_lang,
                        "ocr_empty": not bool(text),
                    },
                )
            ],
            {},
        )
    raise ImportParseError("unsupported_media_type", "Unsupported file type")


def parse_pdf(
    data: bytes,
    *,
    filename: str,
    ocr_provider: OCRProvider | None = None,
) -> list[ParsedUnit]:
    try:
        import fitz

        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ImportParseError("pdf_parse_failed", "PDF could not be parsed") from exc

    settings = get_settings()
    if document.page_count > settings.max_pdf_pages:
        document.close()
        raise ImportParseError("pdf_too_many_pages", "PDF page count exceeds the configured limit")

    units: list[ParsedUnit] = []
    try:
        for page_number, page in enumerate(document, start=1):
            content = page.get_text("text").strip()
            unit_type = "pdf_page"
            metadata: dict[str, object] = {
                "filename": filename,
                "page_number": page_number,
                "extraction": "text",
            }
            if not content and ocr_provider is not None:
                try:
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                    image_bytes = pixmap.tobytes("png")
                    content = ocr_provider.extract(
                        image_bytes,
                        language=settings.ocr_lang,
                        timeout_seconds=settings.ocr_timeout_seconds,
                    )
                    unit_type = "pdf_page_ocr"
                    metadata.update(
                        {
                            "extraction": "ocr",
                            "ocr_provider": ocr_provider.name,
                            "ocr_model": ocr_provider.model,
                            "ocr_language": settings.ocr_lang,
                        }
                    )
                except ProviderUnavailable as exc:
                    raise ImportParseError("ocr_failed", str(exc)) from exc
            if not content:
                metadata["empty"] = True
            units.append(
                ParsedUnit(
                    content=content,
                    unit_type=unit_type,
                    sequence=page_number - 1,
                    metadata=metadata,
                )
            )
    except ImportParseError:
        raise
    except Exception as exc:
        raise ImportParseError("pdf_parse_failed", "PDF page extraction failed") from exc
    finally:
        document.close()
    if units and not any(unit.content for unit in units) and ocr_provider is None:
        raise ImportParseError("ocr_unavailable", "PDF has no text and local OCR is unavailable")
    return units


class _HtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.body_parts: list[str] = []
        self._title_depth = 0
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "title":
            self._title_depth += 1
        if tag in {"script", "style", "noscript", "template", "svg"}:
            self._skip_depth += 1
        if self._skip_depth == 0 and tag in {
            "br",
            "p",
            "div",
            "li",
            "pre",
            "h1",
            "h2",
            "h3",
            "h4",
            "tr",
        }:
            self.body_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in {"script", "style", "noscript", "template", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if self._skip_depth == 0 and tag in {"p", "div", "li", "pre", "h1", "h2", "h3", "h4", "tr"}:
            self.body_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = data.strip()
        if not value:
            return
        if self._title_depth:
            self.title_parts.append(value)
        else:
            self.body_parts.append(value)
            self.body_parts.append(" ")


def extract_html(data: bytes, url: str) -> tuple[str | None, str]:
    parser = _HtmlTextParser()
    try:
        parser.feed(decode_text(data))
        parser.close()
    except Exception as exc:
        raise ImportParseError("html_parse_failed", "Web page content could not be parsed") from exc
    title = " ".join(parser.title_parts).strip() or None
    text = "".join(parser.body_parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not title:
        title = urlparse(url).netloc or None
    return title[:10_000] if title else None, text


def _blocked_ip(value: str) -> bool:
    address = ip_address(value)
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_reserved,
            address.is_multicast,
            address.is_unspecified,
        )
    )


def validate_url_target(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ImportParseError("unsafe_url", "Only HTTP and HTTPS URLs are allowed")
    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme.lower() == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except (OSError, ValueError) as exc:
        raise ImportParseError("url_dns_failed", "URL host could not be resolved") from exc
    if not addresses or any(_blocked_ip(address[4][0]) for address in addresses):
        raise ImportParseError("unsafe_url", "URL target is not publicly routable")


def validate_url_syntax(url: str) -> None:
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ImportParseError("unsafe_url", "Only HTTP and HTTPS URLs are allowed")


def fetch_url(url: str, *, client_factory=httpx.Client) -> FetchedPage:
    settings = get_settings()
    current_url = url.strip()
    for _redirect_count in range(settings.url_max_redirects + 1):
        validate_url_target(current_url)
        try:
            with client_factory(
                follow_redirects=False,
                timeout=settings.url_timeout_seconds,
                headers={"User-Agent": "StarMem/0.1 URL importer"},
            ) as client:
                with client.stream("GET", current_url) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise ImportParseError("url_redirect_invalid", "Redirect has no target")
                        current_url = urljoin(current_url, location)
                        continue
                    response.raise_for_status()
                    media_type = (
                        response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    )
                    if media_type and media_type not in {
                        "text/html",
                        "application/xhtml+xml",
                        "text/plain",
                    }:
                        raise ImportParseError("url_media_type", "URL did not return text content")
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > settings.max_url_bytes:
                            raise ImportParseError(
                                "url_too_large", "Web page exceeds the configured size limit"
                            )
                        chunks.append(chunk)
                    snapshot = b"".join(chunks)
        except ImportParseError:
            raise
        except httpx.HTTPStatusError as exc:
            raise ImportParseError(
                "url_http_error", "Web page returned an unacceptable status"
            ) from exc
        except httpx.HTTPError as exc:
            raise ImportParseError("url_fetch_failed", "Web page request failed") from exc
        title, text = extract_html(snapshot, current_url)
        return FetchedPage(
            original_url=url,
            final_url=current_url,
            title=title,
            text=text,
            snapshot=snapshot,
            media_type=media_type or "text/html",
        )
    raise ImportParseError("url_redirect_limit", "Web page exceeded the redirect limit")
