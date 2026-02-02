import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import json

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import chromadb
from chromadb.config import Settings

from ...domain.ports import KnowledgeRetrievalPort
from ...domain.exceptions import KnowledgeRetrievalError, ConfigurationError

logger = logging.getLogger(__name__)


class UnifiedRAGAdapter(KnowledgeRetrievalPort):
    """Adaptador unificado para RAG con FAISS y ChromaDB"""
    
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.documents = []
        self.use_chroma = os.getenv("USE_CHROMA", "false").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        self.vector_db_path = Path(os.getenv("VECTOR_DB_PATH", "storage/vectors"))
        self.document_path = Path(os.getenv("DOCUMENT_STORAGE_PATH", "storage/documents"))
        
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.document_path.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Inicializa el adaptador RAG"""
        try:
            logger.info("Inicializando RAG Adapter unificado...")
            
            await self._setup_embeddings()
            await self._load_or_create_documents()
            
            if self.use_chroma:
                await self._setup_chroma()
            else:
                await self._setup_faiss()
                
            logger.info("✅ RAG Adapter unificado inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando RAG Adapter: {str(e)}")
            await self._create_fallback_data()
            raise KnowledgeRetrievalError(f"Error inicialización RAG: {str(e)}")

    async def _setup_embeddings(self):
        """Configura modelo de embeddings"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info(f"✅ Embeddings configurados: {self.embedding_model}")
        except Exception as e:
            logger.error(f"Error configurando embeddings: {str(e)}")
            raise ConfigurationError(f"Error embeddings: {str(e)}")

    async def _load_or_create_documents(self):
        """Carga o crea documentos del conocimiento"""
        try:
            pdf_files = list(self.document_path.glob("*.pdf"))
            
            if not pdf_files:
                logger.warning("No se encontraron PDFs. Usando datos mock agronómicos...")
                await self._create_mock_documents()
            else:
                logger.info(f"Procesando {len(pdf_files)} archivos PDF...")
                for pdf_file in pdf_files:
                    await self._process_pdf(pdf_file)
                    
        except Exception as e:
            logger.error(f"Error cargando documentos: {str(e)}")
            await self._create_mock_documents()

    async def _create_mock_documents(self):
        """Crea documentos mock de conocimiento agronómico"""
        mock_data = [
            {
                "content": """El mildiú polvoroso (Oidium spp.) es una enfermedad fúngica común 
                en plantas de clima cálido y seco. Los síntomas incluyen manchas blancas polvorientas 
                en el haz de las hojas, que pueden progresar a necrosis. El tratamiento recomendado 
                incluye fungicidas sistémicos como azoxystrobin y mejora de la ventilación 
                del cultivo. Prevención con aplicaciones preventivas en condiciones de alto riesgo.""",
                "metadata": {"source": "manual_herbolaria_mexicana", "topic": "enfermedades_fungicas", "region": "mexico"}
            },
            {
                "content": """La clorosis férrica se manifiesta con hojas amarillas entre las nervaduras 
                mientras que las venas permanecen verdes. Es común en suelos alcalinos con pH > 7.5 
                y en suelos calcáreos. El tratamiento incluye quelatos de hierro como Fe-EDDHA, 
                acidificación del suelo con azufre elemental, y aplicación de materia orgánica. 
                En Capsicum spp. es frecuente en áreas de riego con agua alcalina.""",
                "metadata": {"source": "agronomia_mexicana", "topic": "deficiencias_nutricionales", "crop": "capsicum"}
            },
            {
                "content": """El picudo del chile (Anthonomus eugenii) causa daños significativos 
                en flores y frutos de Capsicum annuum. Los síntomas incluyen perforaciones en frutos 
                y caída prematura de flores. El manejo integrado incluye control químico con 
                insecticidas específicos, eliminación de residuos de cosecha, y monitoreo con 
                trampas de feromonas. En México es una plaga principal en estados productores.""",
                "metadata": {"source": "control_plagas_mexico", "topic": "insectos_plagas", "crop": "chile"}
            },
            {
                "content": """La marchitez bacteriana (Ralstonia solanacearum) provoca marchitez súbita 
                y muerte de la planta. Los síntomas comienzan con marchitez foliar durante el día 
                que se recupera por la noche, progresando a marchitez permanente. No existe tratamiento 
                curativo. Prevención con uso de semillas certificadas, rotación de cultivos, 
                solarización del suelo, y variedades resistentes. Altamente destructiva en solanáceas.""",
                "metadata": {"source": "patologia_vegetal", "topic": "enfermedades_bacterianas", "severity": "alta"}
            },
            {
                "content": """Capsicum annuum (chile) es susceptible al tizón tardío (Phytophthora infestans) 
                en condiciones de alta humedad relativa (>85%) y temperaturas moderadas (15-25°C). 
                Los síntomas incluyen manchas oscuras irregulares en hojas y lesiones pardas en frutos 
                con halo clorótico. Manejo con fungicidas preventivos (metalaxil, clonazone), 
                manejo de humedad, y eliminación de tejido afectado. Cultivo importante en México.""",
                "metadata": {"source": "cultivo_chile_mexicano", "topic": "enfermedades_fungicas", "crop": "capsicum_annuum"}
            },
            {
                "content": """La nutrición nitrogenada es crucial para Capsicum spp. Deficiencias causan 
                amarillamiento de hojas viejas, crecimiento retardado, y menor producción. Exceso 
                provoca crecimiento vegetativo excesivo y susceptibilidad a enfermedades. Recomendación 
                es 150-200 kg N/ha dividido en 3-4 aplicaciones. Fuentes: urea, nitrato de amonio, 
                fuentes orgánicas. Monitoreo con análisis foliar cada 30 días en cultivo establecido.""",
                "metadata": {"source": "nutricion_capsicum", "topic": "fertilizacion_nitrogenada", "crop": "chile"}
            },
            {
                "content": """El estrés hídrico en Capsicum se manifiesta primero con cierre estomático 
                y reducción fotosintética. Síntomas visuales: hojas marchitas durante el día, 
                recuperación nocturna inicial, luego marchitez permanente. Caída de flores y frutos 
                pequeños. Manejo: riego por goteo con 2-3 L/planta/día, mulching para conservar humedad, 
                monitoreo con tensiómetros. El riego excesivo causa problemas radiculares.""",
                "metadata": {"source": "manejo_hídrico", "topic": "estres_hidrico", "irrigation": "drip"}
            }
        ]
        
        self.documents = [
            Document(page_content=doc["content"], metadata=doc["metadata"])
            for doc in mock_data
        ]
        
        logger.info(f"✅ Creados {len(self.documents)} documentos mock de conocimiento agronómico")

    async def _process_pdf(self, pdf_path: Path):
        """Procesa archivos PDF del conocimiento"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PDFReader(file)
                text_content = ""
                
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
            
            if text_content.strip():
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                
                chunks = text_splitter.split_text(text_content)
                
                for i, chunk in enumerate(chunks):
                    self.documents.append(
                        Document(
                            page_content=chunk,
                            metadata={
                                "source": pdf_path.name,
                                "page": i // 3,
                                "total_pages": len(reader.pages),
                                "document_type": "pdf"
                            }
                        )
                    )
                
                logger.info(f"✅ Procesado {pdf_path.name}: {len(chunks)} chunks")
                
        except Exception as e:
            logger.error(f"Error procesando PDF {pdf_path}: {str(e)}")

    async def _setup_faiss(self):
        """Configura vector store FAISS"""
        try:
            if not self.documents:
                await self._create_mock_documents()
            
            self.vector_store = FAISS.from_documents(
                documents=self.documents,
                embedding=self.embeddings
            )
            
            faiss_path = self.vector_db_path / "faiss_index"
            self.vector_store.save_local(str(faiss_path))
            
            logger.info(f"✅ Vector store FAISS creado con {len(self.documents)} documentos")
            
        except Exception as e:
            logger.error(f"Error configurando FAISS: {str(e)}")
            raise KnowledgeRetrievalError(f"Error FAISS: {str(e)}")

    async def _setup_chroma(self):
        """Configura vector store ChromaDB"""
        try:
            client = chromadb.PersistentClient(
                path=str(self.vector_db_path / "chroma")
            )
            
            collection_name = "mole_ai_knowledge"
            
            try:
                client.delete_collection(name=collection_name)
            except:
                pass
            
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            if self.documents:
                texts = [doc.page_content for doc in self.documents]
                metadatas = [doc.metadata for doc in self.documents]
                ids = [f"doc_{i}" for i in range(len(texts))]
                
                embeddings = self.embeddings.embed_documents(texts)
                
                collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            
            self.vector_store = collection
            logger.info(f"✅ Vector store ChromaDB creado con {len(self.documents)} documentos")
            
        except Exception as e:
            logger.error(f"Error configurando ChromaDB: {str(e)}")
            raise KnowledgeRetrievalError(f"Error ChromaDB: {str(e)}")

    async def get_relevant_knowledge(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Recupera conocimiento relevante"""
        try:
            if not self.vector_store:
                logger.warning("Vector store no inicializado")
                return await self._get_fallback_knowledge(top_k)
            
            if self.use_chroma:
                results = self.vector_store.query(
                    query_texts=[query],
                    n_results=top_k,
                    where=filters if filters else None
                )
                
                context = []
                for i in range(len(results['documents'][0])):
                    context.append({
                        "documentos": [results['documents'][0][i]],
                        "fuentes": [results['metadatas'][0][i].get('source', 'Unknown')],
                        "scores_relevancia": [results['distances'][0][i]] if 'distances' in results else [1.0],
                        "tema_principal": results['metadatas'][0][i].get('topic', 'general')
                    })
                return context
            else:
                docs = self.vector_store.similarity_search_with_score(
                    query, 
                    k=top_k,
                    filter=filters if filters else None
                )
                
                context = []
                for doc, score in docs:
                    context.append({
                        "documentos": [doc.page_content],
                        "fuentes": [doc.metadata.get('source', 'Unknown')],
                        "scores_relevancia": [float(score)],
                        "tema_principal": doc.metadata.get('topic', 'general')
                    })
                return context
                
        except Exception as e:
            logger.error(f"Error obteniendo conocimiento relevante: {str(e)}")
            return await self._get_fallback_knowledge(top_k)

    async def _get_fallback_knowledge(self, top_k: int) -> List[Dict[str, Any]]:
        """Retorna conocimiento de respaldo"""
        fallback_docs = [
            "Información básica sobre diagnóstico de plantas endémicas mexicanas.",
            "Principales enfermedades fúngicas en cultivos de clima cálido.",
            "Recomendaciones generales para manejo integrado de plagas."
        ][:top_k]
        
        return [{
            "documentos": [doc],
            "fuentes": ["conocimiento_general"],
            "scores_relevancia": [0.5],
            "tema_principal": "general"
        } for doc in fallback_docs]

    async def add_knowledge(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Agrega nuevo conocimiento al sistema"""
        try:
            doc = Document(page_content=content, metadata=metadata or {})
            self.documents.append(doc)
            
            if self.embeddings and self.use_chroma:
                embedding = self.embeddings.embed_documents([content])[0]
                self.vector_store.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata or {}],
                    ids=[f"doc_{len(self.documents)}"]
                )
            elif self.embeddings:
                self.vector_store.add_documents([doc])
                # Guardar vector store actualizado
                faiss_path = self.vector_db_path / "faiss_index"
                self.vector_store.save_local(str(faiss_path))
            
            logger.info("✅ Nuevo conocimiento agregado al sistema RAG")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando conocimiento: {str(e)}")
            return False

    async def _create_fallback_data(self):
        """Crea datos de respaldo mínimos"""
        try:
            self.documents = [
                Document(
                    page_content="Sistema de diagnóstico de plantas endémicas mexicanas.",
                    metadata={"source": "fallback", "priority": 1, "topic": "general"}
                )
            ]
            
            if self.embeddings and self.use_chroma:
                await self._setup_chroma()
            elif self.embeddings:
                await self._setup_faiss()
                
            logger.info("✅ Datos fallback creados para RAG")
            
        except Exception as e:
            logger.error(f"Error creando fallback RAG: {str(e)}")