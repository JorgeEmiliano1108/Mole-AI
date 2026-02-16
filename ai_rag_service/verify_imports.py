"""
Verification Script — Tests all corrected imports across the project
"""
import sys
sys.path.insert(0, '.')

results = []

def test_import(name, import_fn):
    try:
        import_fn()
        results.append(f"✅ {name}")
        return True
    except Exception as e:
        results.append(f"❌ {name}: {e}")
        return False

# Domain Layer
test_import("domain.models", lambda: __import__('domain.models'))
test_import("domain.interfaces", lambda: __import__('domain.interfaces'))
test_import("domain.services.citation_manager", lambda: __import__('domain.services.citation_manager'))
test_import("domain.services.cross_validator", lambda: __import__('domain.services.cross_validator'))
test_import("domain.services.mole_ai_agricultural_core", lambda: __import__('domain.services.mole_ai_agricultural_core'))
test_import("domain.services.mole_ai_agricultural_service", lambda: __import__('domain.services.mole_ai_agricultural_service'))

# Application Layer
test_import("application.common", lambda: __import__('application.common'))
test_import("application.use_cases", lambda: __import__('application.use_cases'))
test_import("application.use_cases.mole_ai_chat_use_case", lambda: __import__('application.use_cases.mole_ai_chat_use_case'))
test_import("application.use_cases.ingest_knowledge_use_case", lambda: __import__('application.use_cases.ingest_knowledge_use_case'))

# Infrastructure Layer
test_import("infrastructure.ai.mock_llm", lambda: __import__('infrastructure.ai.mock_llm'))
test_import("infrastructure.ai.mock_embeddings", lambda: __import__('infrastructure.ai.mock_embeddings'))
test_import("infrastructure.ai.mock_model_manager", lambda: __import__('infrastructure.ai.mock_model_manager'))
test_import("infrastructure.ai.auth", lambda: __import__('infrastructure.ai.auth'))

# Field-level checks
def check_fields():
    from domain.models import UserRole, RAGChunk, SensorData, User
    
    # Check AGRICULTOR exists
    assert hasattr(UserRole, 'AGRICULTOR'), "UserRole missing AGRICULTOR"
    
    # Check RAGChunk fields
    chunk = RAGChunk(id="test", content="test content", metadata={"source": "test"}, score=0.9)
    assert chunk.content == "test content", "RAGChunk.content failed"
    assert chunk.metadata.get("source") == "test", "RAGChunk.metadata failed"
    assert chunk.score == 0.9, "RAGChunk.score failed"
    
    # Check SensorData fields
    sd = SensorData(humidity=60.0, temperature=25.0, ph_level=6.5)
    assert sd.ph_level == 6.5, "SensorData.ph_level failed"
    assert sd.humidity == 60.0, "SensorData.humidity failed"
    assert sd.temperature == 25.0, "SensorData.temperature failed"
    
    # Check User can be constructed with id
    user = User(id="test_id", username="test_user", role=UserRole.AGRICULTOR)
    assert user.id == "test_id", "User.id failed"
    assert user.role == UserRole.AGRICULTOR, "User.role failed"

test_import("Field-level checks", check_fields)

# Print results
print("\n" + "="*50)
print("VERIFICATION RESULTS")
print("="*50)
for r in results:
    print(r)

passed = sum(1 for r in results if r.startswith("✅"))
failed = sum(1 for r in results if r.startswith("❌"))
print(f"\n{passed}/{passed+failed} tests passed")
if failed > 0:
    sys.exit(1)
