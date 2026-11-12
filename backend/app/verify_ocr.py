"""Run a real Tesseract smoke check in the API/worker image.

Usage: `docker compose exec worker python -m app.verify_ocr`
The command creates synthetic in-memory fixtures only and stores no user data.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import hashlib

import fitz
from PIL import Image, ImageDraw, ImageFont

from . import worker
from .extract import extract
from .worker import read_uploaded_text, region_location
from .private_storage import decode_upload_encryption_key, write_private_upload


def _fixture_image() -> Image.Image:
    image = Image.new("RGB", (1600, 180), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(size=48)
    except TypeError:  # Pillow versions without the scalable default-font option.
        font = ImageFont.load_default()
        image = Image.new("RGB", (1600, 500), "white")
        draw = ImageDraw.Draw(image)
    draw.text((30, 30), "Recruitment contact +919876543210", fill="black", font=font, stroke_width=1)
    return image


def verify() -> dict[str, str]:
    image = _fixture_image()
    text, regions = worker.ocr_image(image, "image")
    phone = next((item for item in extract(text) if item.kind == "phone"), None)
    if phone is None:
        raise RuntimeError(f"Tesseract did not yield the synthetic phone identifier; OCR text length={len(text)}")
    image_location = region_location(regions, phone.start_char, phone.end_char, "image")
    if not image_location:
        raise RuntimeError("Tesseract phone extraction did not map to an image region")

    with TemporaryDirectory(prefix="rsaicdp-ocr-check-") as directory:
        # The worker accepts only application-generated private upload names.
        pdf_path = Path(directory) / ("f" * 48 + ".pdf")
        pdf = fitz.open()
        page = pdf.new_page(width=800, height=250)
        page.insert_image(fitz.Rect(0, 0, 800, 250), stream=_image_bytes(image))
        pdf_bytes = pdf.tobytes()
        pdf.close()
        encryption_key = decode_upload_encryption_key(worker.settings.upload_encryption_key)
        write_private_upload(pdf_path, pdf_bytes, encryption_key)
        evidence = SimpleNamespace(details={
            "stored_name": pdf_path.name,
            "media_type": "application/pdf",
            "sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        })
        original_upload_dir = worker.settings.upload_dir
        try:
            worker.settings.upload_dir = Path(directory)
            document = read_uploaded_text(evidence)
        finally:
            worker.settings.upload_dir = original_upload_dir

    pdf_phone = next((item for item in extract(document.text) if item.kind == "phone"), None)
    if pdf_phone is None:
        raise RuntimeError("Scanned-PDF OCR did not yield the synthetic phone identifier")
    page_region = region_location(document.regions, pdf_phone.start_char, pdf_phone.end_char, "pdf_page_1")
    if not page_region:
        raise RuntimeError("Scanned-PDF phone extraction did not map to a page region")
    if not page_region.startswith("pdf_page_1_ocrpx_"):
        raise RuntimeError("Scanned-PDF OCR region is missing its page reference")
    return {"image_region": image_location, "pdf_region": page_region}


def _image_bytes(image: Image.Image) -> bytes:
    from io import BytesIO
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


if __name__ == "__main__":
    result = verify()
    print("Real Tesseract OCR verification passed")
    print(f"Image location: {result['image_region']}")
    print(f"Scanned PDF location: {result['pdf_region']}")
