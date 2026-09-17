from app.providers import FastEmbedProvider, MockEmbeddingProvider, ProviderUnavailable
from app.services.chunking import chunk_text


def test_chunker_preserves_markdown_code_and_splits_long_prose():
    code = "```bash\niscsiadm -m node \\\n-T iqn.example \\\n-o delete\n```"
    prose = "这是一个需要保留原始边界的说明。" * 1_200
    content = f"# 清理记录\n\n{code}\n\n{prose}"
    chunks = chunk_text(content)

    assert len(chunks) > 1
    assert any(code in chunk.content and chunk.chunk_type in {"code", "mixed"} for chunk in chunks)
    assert all(content[chunk.start_offset : chunk.end_offset] == chunk.content for chunk in chunks)
    assert any(chunk.start_offset == 0 for chunk in chunks)


def test_chunker_classifies_logs_json_yaml_lists_and_tables():
    samples = [
        ("2026-09-15 10:00:00 ERROR disk failed\n", "log"),
        ('{"service": "api", "port": 8000}', "json"),
        ("service:\n  port: 8000\n", "yaml"),
        ("- first\n- second\n", "list"),
        ("| key | value |\n| --- | --- |\n", "table"),
    ]
    for content, expected_type in samples:
        chunks = chunk_text(
            content, content_format="json" if expected_type == "json" else "markdown"
        )
        assert chunks[0].chunk_type == expected_type


def test_mock_embedding_is_deterministic_and_dimensioned():
    provider = MockEmbeddingProvider(dimensions=8)
    first = provider.embed(["旧连接没有清理"])
    second = provider.embed(["旧连接没有清理"])
    assert first == second
    assert len(first) == 1
    assert len(first[0]) == 8


def test_fastembed_dimension_mismatch_is_explicit():
    class WrongModel:
        def embed(self, texts):
            return [[0.0, 1.0] for _ in texts]

    provider = FastEmbedProvider("test", dimensions=3)
    provider._model = WrongModel()
    try:
        provider.embed(["text"])
    except ProviderUnavailable as exc:
        assert "dimension" in str(exc).lower()
    else:
        raise AssertionError("dimension mismatch must fail")
