"""
ai_engine/tests/test_pdf.py

Unit tests for `loaders/pdf_loader.py`.

These tests avoid depending on a real PDF-parsing backend by monkey-
patching `PyPDFLoader` itself - the goal is to verify OUR logic (path
validation, metadata enrichment, error handling), not re-test
LangChain's/pypdf's PDF parsing, which is out of scope for this engine's
own test suite.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from ai_engine.loaders.pdf_loader import PDFLoadError, PDFLoader


def test_can_handle_accepts_existing_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "notes.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")

    assert PDFLoader.can_handle(str(pdf_path)) is True


def test_can_handle_rejects_wrong_extension(tmp_path: Path) -> None:
    txt_path = tmp_path / "notes.txt"
    txt_path.write_text("hello")

    assert PDFLoader.can_handle(str(txt_path)) is False


def test_can_handle_rejects_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "does_not_exist.pdf"

    assert PDFLoader.can_handle(str(missing_path)) is False


def test_load_raises_on_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.pdf"
    loader = PDFLoader(str(missing_path))

    with pytest.raises(PDFLoadError):
        loader.load()


@patch("ai_engine.loaders.pdf_loader.PyPDFLoader")
def test_load_enriches_metadata(mock_pypdf_loader_cls: MagicMock, tmp_path: Path) -> None:
    pdf_path = tmp_path / "handbook.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")

    fake_page = Document(page_content="Chapter 1 content", metadata={"page": 0})
    mock_loader_instance = MagicMock()
    mock_loader_instance.load.return_value = [fake_page]
    mock_pypdf_loader_cls.return_value = mock_loader_instance

    loader = PDFLoader(str(pdf_path))
    result = loader.load()

    assert len(result) == 1
    assert result[0].metadata["source_type"] == "pdf"
    assert result[0].metadata["source"] == "handbook.pdf"
    assert "ingested_at" in result[0].metadata


@patch("ai_engine.loaders.pdf_loader.PyPDFLoader")
def test_load_raises_on_zero_pages(mock_pypdf_loader_cls: MagicMock, tmp_path: Path) -> None:
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")

    mock_loader_instance = MagicMock()
    mock_loader_instance.load.return_value = []
    mock_pypdf_loader_cls.return_value = mock_loader_instance

    loader = PDFLoader(str(pdf_path))
    with pytest.raises(PDFLoadError):
        loader.load()


@patch("ai_engine.loaders.pdf_loader.PyPDFLoader")
def test_load_wraps_parser_exceptions(mock_pypdf_loader_cls: MagicMock, tmp_path: Path) -> None:
    pdf_path = tmp_path / "corrupted.pdf"
    pdf_path.write_bytes(b"not actually a pdf")

    mock_pypdf_loader_cls.side_effect = RuntimeError("corrupted stream")

    loader = PDFLoader(str(pdf_path))
    with pytest.raises(PDFLoadError):
        loader.load()