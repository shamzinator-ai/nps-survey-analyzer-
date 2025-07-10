import pandas as pd
import app


def test_save_pdf_standard_pivot():
    pivot = pd.DataFrame({
        "Response": ["Yes", "No"],
        "Count": [3, 2],
        "Percent": [60.0, 40.0],
    })
    buf = app.save_pdf("Intro", {"Q1": pivot})
    data = buf.getvalue()
    assert data.startswith(b"%PDF")
    assert len(data) > 100


def test_save_pdf_rating_pivot():
    pivot = pd.DataFrame({
        "Aspect": ["A", "A", "B", "B"],
        "Rating": ["Good", "Bad", "Good", "Bad"],
        "Count": [3, 1, 4, 2],
        "Percent": [75.0, 25.0, 66.7, 33.3],
    })
    buf = app.save_pdf("Intro", {"Q2": pivot})
    data = buf.getvalue()
    assert data.startswith(b"%PDF")
    assert len(data) > 100
