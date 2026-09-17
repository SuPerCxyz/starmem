"""Structure-aware chunks used only for retrieval and embeddings."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkText:
    content: str
    chunk_type: str
    start_offset: int
    end_offset: int
    token_count: int
    metadata: dict[str, object]


@dataclass(frozen=True)
class _Block:
    start: int
    end: int
    kind: str


_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|\[[ xX]\]\s+)")
_TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\)|^\w+(?:Error|Exception):", re.I)
_LOG_RE = re.compile(
    r"(?:^|\s)(?:\d{4}-\d{2}-\d{2}[T ]|\d{2}:\d{2}:\d{2}|\b(?:ERROR|WARN|WARNING|INFO|DEBUG)\b)"
)


def estimate_tokens(text: str) -> int:
    """Approximate tokens without adding a tokenizer dependency."""
    words = re.findall(r"[A-Za-z0-9_]+|[^\s]", text, flags=re.UNICODE)
    return max(1, len(words))


def _line_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        end = cursor + len(line)
        spans.append((cursor, end, line))
        cursor = end
    if cursor < len(text):
        spans.append((cursor, len(text), text[cursor:]))
    return spans


def _kind_for_block(text: str, content_format: str) -> str:
    stripped = text.strip()
    if _HEADING_RE.match(stripped):
        return "heading"
    lines = [line for line in stripped.splitlines() if line.strip()]
    if lines and all(_LIST_RE.match(line) for line in lines):
        return "list"
    if len(lines) >= 2 and sum("|" in line for line in lines) >= 2:
        return "table"
    if _TRACEBACK_RE.search(stripped) or _LOG_RE.search(stripped):
        return "log"
    if content_format.lower() == "json" or stripped[:1] in "[{":
        try:
            json.loads(stripped)
            return "json"
        except (TypeError, ValueError):
            pass
    if content_format.lower() in {"yaml", "yml"} or re.search(r"^\s*[A-Za-z0-9_.-]+:\s*", stripped):
        return "yaml"
    return "prose"


def _blocks(text: str, content_format: str) -> list[_Block]:
    lines = _line_spans(text)
    if not lines:
        return []
    blocks: list[_Block] = []
    paragraph_start: int | None = None
    paragraph_end: int | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph_start, paragraph_end
        if paragraph_start is not None and paragraph_end is not None:
            raw = text[paragraph_start:paragraph_end]
            if raw.strip():
                blocks.append(
                    _Block(paragraph_start, paragraph_end, _kind_for_block(raw, content_format))
                )
        paragraph_start = None
        paragraph_end = None

    index = 0
    while index < len(lines):
        start, end, line = lines[index]
        fence = _FENCE_RE.match(line)
        if fence:
            flush_paragraph()
            marker = fence.group(1)
            block_end = end
            index += 1
            while index < len(lines):
                _, candidate_end, candidate = lines[index]
                block_end = candidate_end
                index += 1
                if re.match(rf"^\s*{re.escape(marker)}", candidate):
                    break
            blocks.append(_Block(start, block_end, "code"))
            continue
        if not line.strip():
            flush_paragraph()
            index += 1
            continue
        if paragraph_start is None:
            paragraph_start = start
        paragraph_end = end
        index += 1
    flush_paragraph()
    return blocks


def _split_large_block(
    text: str, block: _Block, max_tokens: int, overlap_tokens: int
) -> list[_Block]:
    spans = _line_spans(text[block.start : block.end])
    if len(spans) == 1 and block.kind not in {"code", "log"}:
        result: list[_Block] = []
        start = block.start
        while start < block.end:
            remaining = text[start : block.end]
            if estimate_tokens(remaining) <= max_tokens:
                result.append(_Block(start, block.end, block.kind))
                break
            token_count = 0
            target = start
            for position, character in enumerate(remaining, start=start):
                token_count += estimate_tokens(character)
                target = position + 1
                if token_count >= max_tokens:
                    break
            relative_target = target - start
            split_at = max(
                remaining.rfind(" ", 0, relative_target),
                remaining.rfind("\t", 0, relative_target),
                remaining.rfind("。", 0, relative_target),
                remaining.rfind(".", 0, relative_target),
                remaining.rfind("！", 0, relative_target),
                remaining.rfind("!", 0, relative_target),
                remaining.rfind("？", 0, relative_target),
                remaining.rfind("?", 0, relative_target),
            )
            if split_at <= 0:
                split_at = relative_target
            end = start + split_at
            result.append(_Block(start, end, block.kind))
            start = end
        return result
    result: list[_Block] = []
    index = 0
    while index < len(spans):
        local_start = spans[index][0]
        local_end = local_start
        token_count = 0
        end_index = index
        while end_index < len(spans):
            next_tokens = estimate_tokens(
                text[block.start + spans[end_index][0] : block.start + spans[end_index][1]]
            )
            if end_index > index and token_count + next_tokens > max_tokens:
                break
            local_end = spans[end_index][1]
            token_count += next_tokens
            end_index += 1
            if token_count >= max_tokens:
                break
        if end_index == index:
            end_index += 1
            local_end = spans[index][1]
        result.append(_Block(block.start + local_start, block.start + local_end, block.kind))
        if end_index >= len(spans):
            break
        overlap_start = end_index - 1
        overlap_count = 0
        while overlap_start > index and overlap_count < overlap_tokens:
            overlap_count += estimate_tokens(
                text[block.start + spans[overlap_start][0] : block.start + spans[overlap_start][1]]
            )
            overlap_start -= 1
        index = max(index + 1, overlap_start + 1)
    return result


def chunk_text(
    text: str,
    *,
    content_format: str = "markdown",
    min_tokens: int = 300,
    max_tokens: int = 800,
    overlap_tokens: int = 80,
) -> list[ChunkText]:
    """Split by content structure, only falling back to line boundaries when needed."""
    if not text:
        return []
    blocks = _blocks(text, content_format)
    expanded: list[_Block] = []
    for block in blocks:
        if estimate_tokens(text[block.start : block.end]) > max_tokens:
            expanded.extend(_split_large_block(text, block, max_tokens, overlap_tokens))
        else:
            expanded.append(block)

    chunks: list[ChunkText] = []
    pending: list[_Block] = []
    pending_tokens = 0

    def flush() -> None:
        nonlocal pending, pending_tokens
        if not pending:
            return
        start = pending[0].start
        end = pending[-1].end
        content = text[start:end]
        chunks.append(
            ChunkText(
                content=content,
                chunk_type=pending[0].kind
                if len({item.kind for item in pending}) == 1
                else "mixed",
                start_offset=start,
                end_offset=end,
                token_count=estimate_tokens(content),
                metadata={"block_types": list(dict.fromkeys(item.kind for item in pending))},
            )
        )
        pending = []
        pending_tokens = 0

    for block in expanded:
        block_tokens = estimate_tokens(text[block.start : block.end])
        if pending and pending_tokens + block_tokens > max_tokens and pending_tokens >= min_tokens:
            flush()
        pending.append(block)
        pending_tokens += block_tokens
        if pending_tokens >= max_tokens:
            flush()
    flush()
    return chunks
