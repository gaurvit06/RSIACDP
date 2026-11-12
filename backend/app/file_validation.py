SIGNATURES = {
    "application/pdf": lambda content: content.startswith(b"%PDF-"),
    "image/png": lambda content: content.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": lambda content: content.startswith(b"\xff\xd8\xff"),
    "image/webp": lambda content: len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP",
}


def content_matches_type(content: bytes, media_type: str) -> bool:
    """Check a small file signature rather than trusting the browser MIME header."""
    checker = SIGNATURES.get(media_type)
    return bool(checker and checker(content))
