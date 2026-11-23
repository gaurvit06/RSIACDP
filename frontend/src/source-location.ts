export function formatSourceLocation(location: string): string {
  const region = /^(image(?:_ocr_text)?|pdf_page_(\d+))_ocrpx_(\d+)_(\d+)_(\d+)_(\d+)$/.exec(location);
  if (region) {
    const source = region[2] ? `PDF page ${region[2]} OCR` : 'Image OCR';
    return `${source} region · x ${region[3]}, y ${region[4]}, width ${region[5]}, height ${region[6]} px`;
  }
  if (location === 'image_ocr_text') return 'Image OCR text';
  if (location === 'submitted_text') return 'Submitted text';
  const page = /^pdf_page_(\d+)$/.exec(location);
  return page ? `PDF page ${page[1]}` : location;
}
