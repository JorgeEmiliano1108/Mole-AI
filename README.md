# 🌿 Mole AI - Microservicios de IA con Arquitectura Hexagonal

**Microservicios independientes de IA** para diagnóstico de plantas usando **Phi-3.5 Vision-Instruct Q4** como modelo único.

✅ **Arquitectura Hexagonal** | ✅ **Solo Phi-3.5** | ✅ **Probables vía Swagger UI** | ✅ **100% Ejecutables**

---

## 🎯 Objetivo

Crear **ÚNICAMENTE** microservicios de IA auto-contenidos, modulares y auditables:
- Sin backend general
- Sin frontend
- Sin orquestadores externos
- Sin lógica fuera del alcance de IA

---

## 🧠 Microservicios

### 1️⃣ **Vision Service** (Puerto 8001)
Análisis visual de plantas → Swagger: http://localhost:8001/docs

### 2️⃣ **RAG Service** (Puerto 8002)
Razonamiento + Conocimiento → Swagger: http://localhost:8002/docs

---

## 🚀 Quick Start

```bash
# 1. Docker Compose (Recomendado)
cd infrastructure
docker-compose up -d

# 2. Espera 90-120s (Phi-3.5 es pesado)
docker logs -f mole_ai_vision_service

# 3. Accede a Swagger
# Vision: http://localhost:8001/docs
# RAG:    http://localhost:8002/docs
```

---

## 📂 Estructura

```
ai_vision_service/    ← Análisis visual (Hexagonal)
ai_rag_service/       ← RAG + Razonamiento (Hexagonal)
infrastructure/       ← Docker Compose
README.md            ← Este archivo
```

Cada servicio tiene su propia arquitectura hexagonal completa.

---

## 📖 Documentación

- [Vision Service README](ai_vision_service/README.md)
- [RAG Service README](ai_rag_service/README.md)

---

**Versión:** 1.0.0 | **Status:** Production Ready ✅ | **Modelo:** Phi-3.5 Vision-Instruct Q4
