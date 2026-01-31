import os
import pickle
from typing import List, Dict, Any, Optional
from src.infrastructure.config.settings import settings

class VectorStore:
    """Servicio de almacenamiento vectorial usando FAISS para RAG local."""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index_file = "data/vector_store.faiss"
        self.metadata_file = "data/vector_metadata.pkl"
        
        os.makedirs("data", exist_ok=True)
        
        # Importaciones dinámicas
        try:
            import numpy as np
            import faiss
        except ImportError:
            raise ImportError("Instale las dependencias: pip install numpy faiss-cpu")
        
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            self.load()
        else:
            self.index = faiss.IndexFlatL2(dimension)
            self.metadata = []
    
    def add_vectors(self, vectors, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None):
        """Agrega vectores al índice FAISS."""
        import numpy as np
        import faiss
        
        if metadata is None:
            metadata = [{} for _ in texts]
            
        vectors = vectors.astype('float32')
        
        start_idx = self.index.ntotal
        self.index.add(vectors)
        
        for i, (text, meta) in enumerate(zip(texts, metadata)):
            self.metadata.append({
                "text": text,
                "id": start_idx + i,
                **meta
            })
    
    def search(self, query_vector, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Busca los vectores más similares."""
        import numpy as np
        import faiss
        
        if k is None:
            k = settings.RAG_TOP_K
            
        query_vector = query_vector.astype('float32').reshape(1, -1)
        
        if self.index.ntotal == 0:
            return []
        
        distances, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                result = {
                    "text": self.metadata[idx]["text"],
                    "score": float(1.0 / (1.0 + distances[0][i])),
                    "id": int(idx),
                    **{k: v for k, v in self.metadata[idx].items() if k not in ["text", "id"]}
                }
                results.append(result)
        
        return results
    
    def save(self):
        """Guarda el índice y metadatos a disco."""
        import faiss
        faiss.write_index(self.index, self.index_file)
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load(self):
        """Carga el índice y metadatos desde disco."""
        import faiss
        self.index = faiss.read_index(self.index_file)
        with open(self.metadata_file, 'rb') as f:
            self.metadata = pickle.load(f)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del almacén vectorial."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": "FAISS IndexFlatL2"
        }

vector_store = VectorStore()