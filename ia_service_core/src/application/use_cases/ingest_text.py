from src.application.ports.output import VectorRepository, LLMService
from src.infrastructure.utils.pdf_parser import PDFParser  # Reutilizamos la lógica de chunks

class IngestTextUseCase:
    def __init__(self, db: VectorRepository, llm: LLMService):
        self.db = db
        self.llm = llm

    async def run(self, text: str, source: str = "Entrada Manual") -> dict:
        # 1. Usamos la utilidad existente para cortar el texto en trozos manejables
        chunks = PDFParser.create_chunks(text)
        
        saved_count = 0
        
        # 2. Procesamos cada trozo
        for chunk in chunks:
            vector = await self.llm.get_embedding(chunk)
            
            if vector:
                # Formato estándar para saber de dónde vino
                text_to_save = f"[Fuente: {source}]\n{chunk}"
                
                await self.db.save_document(
                    content=text_to_save, 
                    vector=vector, 
                    metadata={"source": source}
                )
                saved_count += 1
                
        return {"source": source, "chunks_saved": saved_count}