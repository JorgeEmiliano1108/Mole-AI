# 14: RF-MS-02: NLP para Web Mining (stop-words, lematización, chunking)

Status: ready-for-human

## Requisito

- **ID:** RF-MS-02
- **Capa:** Microservicios y Web Mining
- **Tipo:** RF
- **Texto:** El microservicio de minería debe aplicar Procesamiento de Lenguaje Natural (NLP) para limpieza de stop-words, lematización y chunking semántico de los textos extraídos.

## Veredicto

⚠️ PARCIAL — Chunking implementado; stop-words y lematización ausentes. Pipeline asociado a ingest manual/S3, no a Web Mining.

## Evidencia

- Chunking: `microservices/mole_chat/app/infrastructure/adapters/rag_listener.py:156-162` (`RecursiveCharacterTextSplitter`).
- Endpoint ingest manual: `microservices/mole_chat/app/api/routers.py:165-169`.
- No se encontró stop-words, lematización, stemming ni librerías NLP (NLTK, spaCy).

## Delta (matriz ideal vs. estado implementado)

El chunking existe para documentos PDF subidos manualmente o desde S3, no provenientes de Web Mining.

## Nota normativa / riesgo

La ausencia de normalización lingüística puede reducir calidad de recuperación RAG y aumentar dependencia de coincidencias exactas.

## Siguiente paso sugerido

Decisión arquitectónica: si Web Mining se incorpora, diseñar pipeline completo con stop-words y lematización; si no, ajustar la matriz.
