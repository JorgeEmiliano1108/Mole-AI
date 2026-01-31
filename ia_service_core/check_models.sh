#!/bin/bash

echo "=== Configuración de Modelos Ollama para Mole AI ==="
echo ""

echo "Modelos configurados en settings.py:"
echo "- LLM: llama3.1:8b-instruct"
echo "- Embeddings: nomic-embed-text"
echo ""

echo "Comandos para verificar/installar modelos (si Ollama está disponible):"
echo "ollama list                    # Listar modelos instalados"
echo "ollama pull llama3.1:8b-instruct     # Descargar LLM principal"
echo "ollama pull nomic-embed-text        # Descargar modelo de embeddings"
echo ""

echo "Endpoints RAG disponibles:"
echo "POST /api/rag/query    - Consultas con RAG"
echo "POST /api/rag/ingest   - Ingestión de documentos"
echo "GET /api/rag/stats     - Estadísticas del sistema"
echo ""

echo "Configuración de variables de entorno:"
echo "OLLAMA_BASE_URL=http://localhost:11434"
echo "LLM_MODEL=llama3.1:8b-instruct"
echo "EMBEDDING_MODEL=nomic-embed-text"
echo "RAG_TOP_K=5"