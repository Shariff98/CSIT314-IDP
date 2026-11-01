"""Tiny PDF writer (text only, no extra library) used by ExportReportController."""


def _escape(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def simple_pdf(title, lines, lines_per_page=45):
    """Builds a valid multi-page A4 PDF with a title and one line of text per entry."""
    pages = [lines[i:i + lines_per_page] for i in range(0, max(len(lines), 1), lines_per_page)] or [[]]
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", None,
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    page_ids = []
    for page_lines in pages:
        text = [f"BT /F1 16 Tf 50 790 Td ({_escape(title)}) Tj ET"]
        y = 760
        for line in page_lines:
            text.append(f"BT /F1 10 Tf 50 {y} Td ({_escape(line)}) Tj ET")
            y -= 16
        stream = "\n".join(text)
        objects.append(f"<< /Length {len(stream.encode('latin-1', 'replace'))} >>\nstream\n{stream}\nendstream")
        content_id = len(objects)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                       f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>")
        page_ids.append(len(objects))
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] /Count {len(page_ids)} >>"
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n{body}\nendobj\n".encode("latin-1", "replace")
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)
