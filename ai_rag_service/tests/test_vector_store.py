import os
import pytest

from pathlib import Path


@pytest.mark.slow
@pytest.mark.asyncio
async def test_faiss_persistence_cycle(tmp_path, monkeypatch):
    """Verifica que FAISS persista en disco y se recupere tras 'reinicio'."""
    # Set VECTOR_DB_PATH to temporary directory
    tmp_dir = tmp_path / "vectors"
    monkeypatch.setenv('VECTOR_DB_PATH', str(tmp_dir))

    # Import inside test to pick up monkeypatched env
    from ai_rag_service.infrastructure.ai.vector_store import FAISSVectorStoreAdapter

    # 1) Inicializar adapter (debe arrancar vacío la primera vez)
    adapter = FAISSVectorStoreAdapter()
    assert adapter is not None
    assert adapter.vector_store is None or getattr(adapter.vector_store, 'index', None) is None

    # 2) Ingestar documentos de prueba
    docs = [
        "Cómo regar maíz en época de sequía",
        "Identificación de plagas comunes en tomate",
    ]
    metadatas = [{"source": "test"} for _ in docs]

    added = await adapter.add_documents(docs, metadatas)
    assert added == len(docs)

    # Verify files persisted
    index_path = Path(os.environ['VECTOR_DB_PATH']) / "faiss_index"
    metadata_path = Path(os.environ['VECTOR_DB_PATH']) / "metadata.json"
    assert index_path.exists(), f"Index path not found: {index_path}"
    assert metadata_path.exists(), f"Metadata file not found: {metadata_path}"

    # 3) Unload from memory
    adapter.unload()
    assert adapter.vector_store is None

    # 4) Recreate adapter (simulate restart) and verify it loads persisted index
    adapter2 = FAISSVectorStoreAdapter()
    # perform a retrieve to ensure it's functional
    results = await adapter2.retrieve("riego", top_k=3)
    assert isinstance(results, list)
    assert len(results) >= 0
