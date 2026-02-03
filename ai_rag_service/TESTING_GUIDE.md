# 🧪 TESTING GUIDE - RAG SERVICE (SWAGGER UI)

## 🚀 Quick Start

### 1. Start Service
```bash
cd c:\Users\pipog\OneDrive\Desktop\Mole-AI
docker-compose up --build
```

### 2. Open Swagger UI
```
http://localhost:8002/docs
```

---

## 📋 TEST SCENARIOS

### Test 1: Upload PDF (Foundation)

**Endpoint:** `POST /rag/admin/upload-pdf`

**What to do:**
1. Click on `POST /rag/admin/upload-pdf`
2. Click "Try it out"
3. Upload a PDF file (botanical diseases, agronomic guide, etc.)
4. Execute

**Expected Response:**
```json
{
  "status": "success",
  "message": "PDF filename.pdf inyectado",
  "chunks": 42
}
```

**What it does:**
- ✅ Extracts text from PDF
- ✅ Creates chunks (1000 chars each)
- ✅ Generates embeddings (sentence-transformers)
- ✅ Stores in FAISS vector DB
- ✅ Persists metadata.json
- ✅ Saves to `storage/vectors/`

**Validation:** 
- ✅ Check response status = "success"
- ✅ Check chunks > 0
- ✅ Verify file appears in `/rag/admin/sources`

---

### Test 2: List Sources (Knowledge Base)

**Endpoint:** `GET /rag/admin/sources`

**What to do:**
1. Click on `GET /rag/admin/sources`
2. Click "Try it out"
3. Execute

**Expected Response:**
```json
{
  "sources": [
    {
      "name": "herbolaria.pdf",
      "chunks": 42,
      "category": "uploaded",
      "timestamp": "2024-12-19T10:15:00"
    }
  ],
  "total": 1,
  "timestamp": "2024-12-19T10:30:00"
}
```

**What it does:**
- ✅ Reads metadata.json from vector store
- ✅ Lists all loaded PDFs
- ✅ Shows chunk count per source
- ✅ Shows upload timestamp

**Validation:**
- ✅ List contains your uploaded PDF
- ✅ Chunks count matches step 1
- ✅ Timestamp is recent

---

### Test 3: Generate Diagnosis (RAG + Phi-3.5)

**Endpoint:** `POST /rag/diagnose`

**What to do:**
1. Click on `POST /rag/diagnose`
2. Click "Try it out"
3. Copy-paste this example:

```json
{
  "vision_output": {
    "estado": "Atención",
    "confianza": 0.85,
    "especie_probable": "Solanum lycopersicum",
    "sintomas": ["Manchas oscuras", "Defoliación"],
    "análisis_visual": "Síntomas de tizón tardío en hojas inferiores"
  },
  "sensores": {
    "ph": 6.5,
    "humedad": 75.0,
    "temp": 22.5,
    "uv": 0.6
  }
}
```

4. Execute

**Expected Response:**
```json
{
  "id": "a3f5e2c1-8d2b-4c7a-9b1e-f3c5d8a2b4e6",
  "timestamp": "2024-12-19T10:35:00",
  "diagnostico": "Planta de tomate con síntomas consistentes con tizón tardío (Phytophthora infestans). Las manchas oscuras y la defoliación, combinadas con alta humedad (75%) y temperatura moderada (22.5°C), son indicadores típicos. El pH del suelo es apropiado para el crecimiento de Phytophthora en estas condiciones.",
  "recomendaciones": [
    "Aplicar fungicida a base de cobre o mancozeb inmediatamente",
    "Mejorar ventilación y reducir humedad mediante riego por goteo",
    "Remover hojas infectadas para evitar dispersión",
    "Reducir riego vespertino para secar foliaje"
  ],
  "fuentes_consultadas": ["herbolaria.pdf"],
  "confianza_final": 0.87,
  "requiere_accion_humana": false
}
```

**What it does:**
1. **Retrieve Phase** (RAG)
   - Constructs query: "Síntomas: Manchas oscuras, Defoliación..."
   - Searches FAISS vector store
   - Retrieves top 3 similar chunks from PDFs
   
2. **Reasoning Phase** (Phi-3.5)
   - Sends to Phi-3.5 Vision-Instruct Q4:
     * Vision analysis + sensor data + retrieved context
     * Generates structured JSON diagnosis
     * Phi-3.5 evaluates confidence
     
3. **Response**
   - Returns diagnosis with:
     * Detailed agronomic analysis
     * Specific recommendations
     * Source attribution
     * Confidence score
     * Human escalation flag

**Validation:**
- ✅ Response time < 30 seconds
- ✅ diagnostico is not empty
- ✅ recomendaciones has 3+ items
- ✅ fuentes_consultadas matches sources
- ✅ confianza_final between 0.0-1.0
- ✅ requiere_accion_humana is boolean

---

## 🔧 ADVANCED TESTING

### Test 4: Test with Different Crops

**Scenario:** Query for different plant species

**Request:**
```json
{
  "vision_output": {
    "estado": "Peligro",
    "confianza": 0.92,
    "especie_probable": "Capsicum annuum",
    "sintomas": ["Lesiones circulares", "Anillo rojo", "Podredumbre"],
    "análisis_visual": "Síntomas de mancha bacteriana severa"
  },
  "sensores": {
    "ph": 7.0,
    "humedad": 85.0,
    "temp": 28.0,
    "uv": 1.2
  }
}
```

**Expected:** Phi-3.5 consults PDFs for capsicum diseases specific to high humidity/temp

---

### Test 5: Test Multiple PDFs (Knowledge Expansion)

**Workflow:**
1. Upload `plant_diseases.pdf` (Test 1)
2. Upload `agronomic_guide.pdf` (new)
3. Query in Test 3 diagnosis
4. Verify both appear in `/rag/admin/sources`
5. Diagnosis should cite both sources

---

### Test 6: Health Check

**Endpoint:** `GET /rag/health`

**What to do:**
1. Click on `GET /rag/health`
2. Click "Try it out"
3. Execute

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-19T10:40:00"
}
```

**Validation:**
- ✅ Status = "healthy"
- ✅ Timestamp is current

---

## 📊 ARCHITECTURE FLOW (VISUAL)

```
┌─────────────────────────────────────────────────────────┐
│               SWAGGER UI (Browser)                      │
│           http://localhost:8002/docs                    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   Upload PDF    List Sources  Diagnose
        │            │            │
        └────────────┼────────────┘
                     │
                ┌────▼────┐
                │ FastAPI │  (Adapter Inbound)
                │ Router  │
                └────┬────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    Upload      Retrieve    Diagnose
    Use Case    Knowledge   Use Case
         │           │           │
         └───────────┼───────────┘
                     │
              ┌──────▼──────┐
              │  Domain     │  (Pure Logic)
              │  Models     │
              └──────┬──────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
      Vector      Reasoning    (Others)
      Store Port  Model Port
         │           │
         └───────────┼───────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
      FAISS      Phi-3.5    (Adapters
     Adapter    Adapter      Outbound)
         │           │
         └───────────┼───────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
 Storage/      HuggingFace      Torch Model
 Vectors       Embeddings       (GPU/CPU)
```

---

## 🐛 TROUBLESHOOTING

### Issue: "Model not ready"
**Solution:** Wait 2-3 minutes for Phi-3.5 to download (~2.6GB)
```bash
# Check container logs
docker logs mole_ai_rag -f
```

### Issue: "Vector store empty"
**Solution:** Upload a PDF first (Test 1)

### Issue: "PDF upload fails"
**Causes:**
- File not a valid PDF
- File size too large
- Disk space issues
- Check logs: `docker logs mole_ai_rag`

### Issue: Diagnosis takes > 30 seconds
**Reason:** First inference loads Phi-3.5 (expected)
**Next requests:** < 5 seconds

---

## ✅ COMPLETE TEST CHECKLIST

- [ ] Docker service running (`docker ps` shows mole_ai_rag UP)
- [ ] Swagger UI accessible (http://localhost:8002/docs, HTTP 200)
- [ ] Health check passes
- [ ] Upload PDF successful (chunks > 0)
- [ ] Sources list shows uploaded PDF
- [ ] Diagnosis works with example JSON
- [ ] Response includes all required fields
- [ ] Confidence score between 0-1
- [ ] Sources cited in diagnosis
- [ ] No error logs in container

---

## 📝 NOTES

- **First inference:** ~30s (model loading)
- **Subsequent:** ~5-10s (inference only)
- **Phi-3.5 loading:** ~2.6GB
- **Vector store:** Persists in `/ai_rag_service/storage/vectors/`
- **Max PDF size:** Limited by memory
- **Chunk size:** 1000 characters

---

**Status:** ✅ Production-Ready for Testing

Test from Swagger UI. No CLI commands needed.
