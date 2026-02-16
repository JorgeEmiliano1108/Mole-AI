"""
Infrastructure Adapter - PDF/Text Ingestion
"""
import logging
import io
from typing import List, Tuple, Dict
from domain.ports import KnowledgeIngestionPort

logger = logging.getLogger(__name__)

class PDFIngestionAdapter(KnowledgeIngestionPort):
    """Adapter for parsing files using PyPDF2 or standard text processing"""
    
    async def parse_file(self, file_content: bytes, filename: str) -> Tuple[List[str], List[Dict]]:
        """Parse file content into chunks and metadata"""
        try:
            text = ""
            if filename.lower().endswith('.pdf'):
                text = self._parse_pdf(file_content)
            else:
                text = file_content.decode('utf-8', errors='ignore')
            
            if not text:
                return [], []
            
            # Simple chunking strategy (can be improved with LangChain TextSplitters later)
            chunks = self._chunk_text(text)
            
            metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]
            
            return chunks, metadatas
            
        except Exception as e:
            logger.error(f"Error parsing file {filename}: {str(e)}")
            raise

    def _parse_pdf(self, content: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            import pypdf
            pdf_file = io.BytesIO(content)
            reader = pypdf.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.error("pypdf not installed. Please install it: pip install pypdf")
            # Fallback or error
            return ""
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Simple overlapping chunker"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            
        return chunks
