from src.application.ports.output import VectorRepository, LLMService
from src.infrastructure.utils.pdf_parser import PDFParser

class IngestDocUseCase:
    def __init__(self, db: VectorRepository, llm: LLMService):
        self.db = db
        self.llm = llm

    async def run(self, file_bytes: bytes, filename: str) -> dict:
        # 1. Extraer texto del PDF
        full_text = PDFParser.extract_text(file_bytes)
        
        # 2. Dividir en chunks
        chunks = PDFParser.create_chunks(full_text)
        
        saved_count = 0
        
        # 3. Procesar cada chunk
        for chunk in chunks:
            # Generar embedding
            vector = await self.llm.get_embedding(chunk)
            
            if vector:
                # Guardar en BD
                await self.db.save_document(
                    content=chunk, 
                    vector=vector, 
                    metadata={"source": filename}
                )
                saved_count += 1
                
        return {"filename": filename, "chunks_saved": saved_count}