import pytest

from app.domain.ingestion.extractor import extract_pdf


def test_extract_pdf_rejects_non_pdf_suffix(tmp_path):
    text_path = tmp_path / "source.txt"
    text_path.write_text("not a pdf")

    with pytest.raises(ValueError, match="Only PDF files are supported"):
        extract_pdf(text_path)
