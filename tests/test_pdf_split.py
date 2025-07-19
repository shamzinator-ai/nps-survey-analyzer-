import os
import sys
import base64
from pathlib import Path
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from vision import pdf_to_images


def test_pdf_to_images():
    pdf_b64 = Path('examples/sample.pdf.b64').read_text()
    pdf_bytes = base64.b64decode(pdf_b64)
    try:
        images = pdf_to_images(pdf_bytes)
    except Exception:
        pytest.skip("poppler not installed")
    assert len(images) >= 1
