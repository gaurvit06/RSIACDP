import assert from 'node:assert/strict';
import test from 'node:test';
import { formatSourceLocation } from '../src/source-location.ts';

test('displays pixel coordinates for persisted image and PDF OCR locations', () => {
  for (const prefix of ['image_ocr_text', 'image']) {
    assert.equal(formatSourceLocation(prefix + '_ocrpx_67_406_623_29'), 'Image OCR region · x 67, y 406, width 623, height 29 px');
  }
  assert.equal(formatSourceLocation('pdf_page_2_ocrpx_1_2_3_4'), 'PDF page 2 OCR region · x 1, y 2, width 3, height 4 px');
  assert.equal(formatSourceLocation('pdf_page_1'), 'PDF page 1');
  assert.equal(formatSourceLocation('submitted_text'), 'Submitted text');
});
