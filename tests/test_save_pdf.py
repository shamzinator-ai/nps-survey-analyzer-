import pandas as pd
from io import BytesIO
from unittest.mock import MagicMock
import base64
import app

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+lk18AAAAASUVORK5CYII="
)


def test_save_pdf_standard(monkeypatch):
    pivot = pd.DataFrame({
        "Response": ["Yes", "No"],
        "Count": [10, 5],
        "Percent": [66.7, 33.3],
    })
    chart_buf = BytesIO(PNG)
    cp = MagicMock(return_value=chart_buf)
    sb = MagicMock(return_value=BytesIO(PNG))
    monkeypatch.setattr(app, "chart_png", cp)
    monkeypatch.setattr(app, "stacked_bar_chart", sb)
    pdf = app.save_pdf("Intro", {"Q1": pivot})
    cp.assert_called_once()
    sb.assert_not_called()
    assert isinstance(pdf, BytesIO)
    assert pdf.getbuffer().nbytes > 0


def test_save_pdf_rating(monkeypatch):
    pivot = pd.DataFrame({
        "Aspect": ["A", "A", "B", "B"],
        "Rating": ["Good", "Bad", "Good", "Bad"],
        "Count": [5, 5, 3, 7],
        "Percent": [50, 50, 30, 70],
    })
    chart_buf = BytesIO(PNG)
    sb = MagicMock(return_value=chart_buf)
    cp = MagicMock(return_value=BytesIO(PNG))
    monkeypatch.setattr(app, "stacked_bar_chart", sb)
    monkeypatch.setattr(app, "chart_png", cp)
    pdf = app.save_pdf("Intro", {"Q2": pivot})
    sb.assert_called_once()
    cp.assert_not_called()
    assert isinstance(pdf, BytesIO)
    assert pdf.getbuffer().nbytes > 0
