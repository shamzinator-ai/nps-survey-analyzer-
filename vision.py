"""PDF and image processing helpers."""

import base64
from io import BytesIO
from typing import List
from pdf2image import convert_from_bytes
from PIL import Image
import openai


# ------------------------ Image and Vision Utilities -----------------------

def pdf_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert PDF bytes into a list of page images."""
    # UPDATED: each PDF page becomes an image for vision analysis
    return convert_from_bytes(pdf_bytes)


def image_to_data_uri(img: Image.Image) -> str:
    """Return base64 data URI for the given image."""
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def analyze_images(prompt: str, images: List[Image.Image]) -> str:
    """Run OpenAI Vision on a list of images with ``prompt``."""
    content = [{"type": "text", "text": prompt}]
    for img in images:
        content.append({"type": "image_url", "image_url": image_to_data_uri(img)})
    response = openai.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content.strip()

