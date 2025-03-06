import base64

MIME_TYPE_SIGNATURES = {
    b"%PDF": "application/pdf",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"PK\x03\x04": "application/zip",
    b"\x25\x21PS": "application/postscript",
    b"\x00\x00\x00\x0c\x6a\x50\x20\x20": "image/jp2",
    b"BM": "image/bmp",
    b"\x49\x49\x2a\x00": "image/tiff",  # Little-endian TIFF
    b"\x4d\x4d\x00\x2a": "image/tiff",  # Big-endian TIFF
}

MIME_TYPE_TEXT = "text"


def infer_file_type(base64_content: str) -> str:
    """Infer the file type from the content."""
    try:
        try:
            decoded_bytes = base64.b64decode(base64_content[:1024])
        except Exception:
            return MIME_TYPE_TEXT

        for signature, mime_type in MIME_TYPE_SIGNATURES.items():
            if decoded_bytes.startswith(signature):
                return mime_type

        return MIME_TYPE_TEXT
    except Exception:
        return MIME_TYPE_TEXT
