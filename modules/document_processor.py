from pypdf import PdfReader


def extract_pdf_pages(uploaded_file):
    reader = PdfReader(uploaded_file)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if text and text.strip():
            pages.append({
                "page": page_number,
                "text": text.strip()
            })

    return pages


def create_chunks(pages, source, chunk_size=700, overlap=120):
    chunks = []
    chunk_number = 0

    for page in pages:
        text = page["text"]
        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "source": source,
                    "page": page["page"],
                    "chunk": chunk_number
                })

                chunk_number += 1

            start += chunk_size - overlap

    return chunks