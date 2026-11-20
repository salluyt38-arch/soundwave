"""
Lightweight, Zero-Dependency Multipart/Form-Data Parser for Image Uploads.
Enables high-efficiency binary image streaming without 33% Base64 expansion overhead.
"""

from typing import Any, Dict, Optional, Tuple


def parse_multipart_form(content_type: str, raw_body: bytes) -> Dict[str, Any]:
    """
    Parses multipart/form-data body into a dictionary containing form fields and file bytes.
    Returns:
      {
        "field_name": "string_value",
        "image_bytes": b"binary_jpeg_or_png_data",
        "filename": "original_filename.jpg",
        "content_type": "image/jpeg"
      }
    """
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("boundary="):
            boundary = part.split("=", 1)[1].strip("\"'").encode("utf-8")
            break

    if not boundary or not raw_body:
        return {}

    delimiter = b"--" + boundary
    parts = raw_body.split(delimiter)
    result: Dict[str, Any] = {}

    for p in parts:
        p = p.strip()
        if not p or p == b"--":
            continue

        if b"\r\n\r\n" not in p:
            continue

        raw_headers, body = p.split(b"\r\n\r\n", 1)
        body = body.rstrip(b"\r\n")

        headers_str = raw_headers.decode("utf-8", errors="ignore")
        name = None
        filename = None
        part_content_type = None

        for line in headers_str.split("\r\n"):
            line = line.strip()
            if line.lower().startswith("content-disposition:"):
                for token in line.split(";"):
                    token = token.strip()
                    if token.lower().startswith("name="):
                        name = token.split("=", 1)[1].strip("\"'")
                    elif token.lower().startswith("filename="):
                        filename = token.split("=", 1)[1].strip("\"'")
            elif line.lower().startswith("content-type:"):
                part_content_type = line.split(":", 1)[1].strip()

        if name:
            if filename:
                result["image_bytes"] = body
                result["filename"] = filename
                result["file_content_type"] = part_content_type
            else:
                result[name] = body.decode("utf-8", errors="ignore")

    return result
