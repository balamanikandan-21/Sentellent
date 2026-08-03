from app.ingestion.processors.chunker import chunk_text, count_tokens
from app.ingestion.processors.dedup import compute_content_hash


class TestContentHash:
    def test_deterministic(self):
        assert compute_content_hash("Hello World") == compute_content_hash("Hello World")

    def test_whitespace_and_case_normalized(self):
        # Same article syndicated with different formatting must dedupe.
        a = compute_content_hash("Reliance  posts record\nprofit")
        b = compute_content_hash("reliance posts record profit")
        assert a == b

    def test_different_content_differs(self):
        assert compute_content_hash("TCS Q1 results") != compute_content_hash("Infosys Q1 results")


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunks = chunk_text("Short news blurb.", chunk_size=512, chunk_overlap=64)
        assert len(chunks) == 1
        assert chunks[0].index == 0
        assert chunks[0].content == "Short news blurb."

    def test_long_text_multiple_chunks_with_overlap(self):
        text = "market " * 2000  # well over 512 tokens
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=64)
        assert len(chunks) > 1
        assert all(c.token_count <= 512 for c in chunks)
        # consecutive indices
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_chunking_is_deterministic(self):
        text = "The Nifty 50 index rose today. " * 200
        first = chunk_text(text, chunk_size=128, chunk_overlap=16)
        second = chunk_text(text, chunk_size=128, chunk_overlap=16)
        assert [c.content for c in first] == [c.content for c in second]

    def test_count_tokens_positive(self):
        assert count_tokens("Reliance Industries") > 0
