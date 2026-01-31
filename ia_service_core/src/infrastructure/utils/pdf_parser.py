import fitz  # PyMuPDF

class PDFParser:
    @staticmethod
    def extract_text(file_bytes: bytes) -> str:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error leyendo PDF: {e}")

    @staticmethod
    def create_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
            
        return chunks