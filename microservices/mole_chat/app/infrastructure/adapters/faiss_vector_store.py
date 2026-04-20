"""
FAISS Vector Store Adapter
Maneja la ingesta, búsqueda y eliminación selectiva de documentos.
"""
import os
import uuid
from typing import List, Tuple
import structlog
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings 

logger = structlog.get_logger()

class FAISSVectorStore:
    def __init__(self, index_path: str = "/app/storage/vectors/faiss_index"):
        self.index_path = index_path
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 
        self.vectorstore = self._load_or_create_index()

    def _load_or_create_index(self) -> FAISS:
        """Carga el índice existente o crea uno nuevo en memoria."""
        if os.path.exists(self.index_path):
            try:
                return FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                logger.error("error_loading_faiss", error=str(e))
        
        # Crea un índice vacío temporal
        return FAISS.from_texts(["Mole.AI Inicializado"], self.embeddings)

    async def asearch(self, query: str, k: int = 3) -> Tuple[str, List[dict]]:
        """Busca en el índice y devuelve el contexto y las fuentes."""
        docs = self.vectorstore.similarity_search(query, k=k)
        if not docs:
            return "", []
        
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = [{"source": doc.metadata.get("source", "Unknown")} for doc in docs]
        return context, sources

    async def ingest_pdf(self, file_path: str, filename: str) -> str:
        """Ingesta un PDF, le asigna un DOC_ID único y guarda los vectores."""
        doc_id = str(uuid.uuid4())
        
        loader = PyPDFLoader(file_path)
        raw_docs = loader.load()
        
        # Cortamos el PDF en pedazos procesables
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(raw_docs)
        
        # Inyectamos el ID y el nombre del archivo en cada pedazo
        ids = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            ids.append(chunk_id)
            chunk.metadata["doc_id"] = doc_id
            chunk.metadata["source"] = filename

        # Agregamos los vectores al índice y lo guardamos en disco
        self.vectorstore.add_documents(documents=chunks, ids=ids)
        self.vectorstore.save_local(self.index_path)
        
        logger.info("pdf_ingested", filename=filename, doc_id=doc_id, chunks=len(chunks))
        return doc_id

    async def delete_pdf_by_id(self, doc_id: str) -> bool:
        """Busca y elimina todos los vectores asociados a un DOC_ID."""
        try:
            ids_to_delete = []
            docstore_dict = getattr(self.vectorstore.docstore, "_dict", {})
            
            for _id, doc in docstore_dict.items():
                if doc.metadata.get("doc_id") == doc_id:
                    ids_to_delete.append(_id)
            
            if not ids_to_delete:
                return False
                
            self.vectorstore.delete(ids_to_delete)
            self.vectorstore.save_local(self.index_path)
            logger.info("pdf_deleted", doc_id=doc_id, chunks_deleted=len(ids_to_delete))
            return True
        except Exception as e:
            logger.error("error_deleting_pdf", error=str(e), doc_id=doc_id)
            return False