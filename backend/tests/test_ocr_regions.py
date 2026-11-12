import unittest
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from app import worker
from app.worker import OCRRegion, ocr_image, region_location
from app.verify_ocr import verify as verify_ocr_smoke_fixture


class OCRRegionTests(unittest.TestCase):
    def test_ocr_word_data_builds_text_offsets_and_bounding_boxes(self):
        import pytesseract
        synthetic_data = {
            "text": ["Contact", "", "+919876543210"],
            "left": [10, 0, 90], "top": [20, 0, 22],
            "width": [60, 0, 110], "height": [14, 0, 14],
        }
        with patch.object(pytesseract, "image_to_data", return_value=synthetic_data) as call:
            text, regions = ocr_image(object(), "image")
        self.assertEqual(text, "Contact +919876543210")
        self.assertEqual(regions, (OCRRegion(0, 7, 10, 20, 60, 14), OCRRegion(8, 21, 90, 22, 110, 14)))
        self.assertEqual(region_location(regions, 8, 21, "image"), "image_ocrpx_90_22_110_14")
        self.assertEqual(call.call_args.kwargs["timeout"], 30)

    def test_maps_extracted_span_to_union_of_overlapping_word_boxes(self):
        regions = (
            OCRRegion(0, 4, 10, 20, 30, 12),
            OCRRegion(5, 10, 45, 18, 22, 14),
            OCRRegion(11, 18, 5, 60, 20, 10),
        )
        self.assertEqual(region_location(regions, 2, 9, "image"), "image_ocrpx_10_18_57_14")

    def test_returns_none_when_no_ocr_word_overlaps_span(self):
        self.assertIsNone(region_location((OCRRegion(0, 3, 1, 2, 3, 4),), 4, 7, "image"))

    def test_region_location_fits_database_column(self):
        location = region_location((OCRRegion(0, 2, 123456, 234567, 345678, 456789),), 0, 2, "pdf_page_123456")
        self.assertIsNotNone(location)
        self.assertLessEqual(len(location), 80)

    def test_scanned_pdf_regions_keep_global_offsets_and_page_prefix(self):
        import fitz
        with TemporaryDirectory() as directory:
            path = Path(directory) / ("e" * 48 + ".pdf")
            pdf = fitz.open()
            first = pdf.new_page()
            first.insert_text((72, 72), "Text page")
            pdf.new_page()  # Empty text page takes the OCR path.
            pdf.save(path)
            pdf.close()
            evidence = SimpleNamespace(details={
                "stored_name": path.name,
                "media_type": "application/pdf",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
            page_ocr = (OCRRegion(5, 18, 90, 22, 110, 14),)
            with patch.object(worker.settings, "upload_dir", Path(directory)), patch.object(
                worker, "ocr_image", return_value=("Call +919876543210", page_ocr)
            ):
                document = worker.read_uploaded_text(evidence)
        self.assertEqual([segment.source_location for segment in document.segments], ["pdf_page_1", "pdf_page_2"])
        second_page = document.segments[1]
        self.assertEqual(document.text[second_page.start_char:second_page.end_char], "Call +919876543210")
        shifted = document.regions[0]
        self.assertEqual((shifted.start_char, shifted.end_char), (second_page.start_char + 5, second_page.start_char + 18))
        self.assertEqual(region_location(document.regions, shifted.start_char, shifted.end_char, "pdf_page_2"), "pdf_page_2_ocrpx_90_22_110_14")

    def test_container_smoke_fixture_uses_worker_accepted_upload_name(self):
        text = "Recruitment contact +919876543210"
        region = OCRRegion(0, len(text), 10, 20, 300, 60)
        with patch.object(worker, "ocr_image", return_value=(text, (region,))):
            result = verify_ocr_smoke_fixture()
        self.assertTrue(result["image_region"].startswith("image_ocrpx_"))
        self.assertTrue(result["pdf_region"].startswith("pdf_page_1_ocrpx_"))


if __name__ == "__main__":
    unittest.main()
