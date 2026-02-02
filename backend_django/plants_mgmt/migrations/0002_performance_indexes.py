"""
Enterprise-grade performance indexes migration for Mole AI
Creates critical indexes for optimal query performance
"""

from django.db import migrations, models
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('plants_mgmt', '0001_initial'),
    ]

    operations = [
        # ===== PLANT TABLE INDEXES =====
        
        # Performance index for owner-based queries (most common)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plant_owner_created "
            "ON plants_mgmt_plant (owner_id, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_plant_owner_created;"
        ),
        
        # Index for plant type filtering (frequent in analytics)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plant_type_status "
            "ON plants_mgmt_plant (plant_type, status, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_plant_type_status;"
        ),
        
        # Partial index for active plants only
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plant_active "
            "ON plants_mgmt_plant (created_at DESC) "
            "WHERE status IN ('healthy', 'stress_water', 'pest_detection');",
            reverse_sql="DROP INDEX IF EXISTS idx_plant_active;"
        ),
        
        # ===== SENSOR DATA TABLE INDEXES =====
        
        # Time-series index for recent data (IoT workloads)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sensor_recent "
            "ON plants_mgmt_sensordata (timestamp DESC, plant_id) "
            "WHERE timestamp > NOW() - INTERVAL '30 days';",
            reverse_sql="DROP INDEX IF EXISTS idx_sensor_recent;"
        ),
        
        # Index for device-based queries (ESP32 monitoring)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sensor_device_time "
            "ON plants_mgmt_sensordata (device_id, timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_sensor_device_time;"
        ),
        
        # Partial index for alert conditions
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sensor_alerts "
            "ON plants_mgmt_sensordata (plant_id, timestamp DESC) "
            "WHERE humidity < 30 OR temperature > 35 OR soil_moisture < 20 OR ph < 5.5 OR ph > 7.5;",
            reverse_sql="DROP INDEX IF EXISTS idx_sensor_alerts;"
        ),
        
        # ===== DIAGNOSIS TABLE INDEXES =====
        
        # Critical index for urgent diagnoses (medical workload)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_urgent "
            "ON plants_mgmt_diagnosis (urgency_level, created_at DESC) "
            "WHERE urgency_level IN ('high', 'critical');",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_urgent;"
        ),
        
        # Index for plant diagnosis history (common query)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_plant_time "
            "ON plants_mgmt_diagnosis (plant_id, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_plant_time;"
        ),
        
        # Performance index for high-confidence diagnoses
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_confidence "
            "ON plants_mgmt_diagnosis (confidence DESC, created_at DESC) "
            "WHERE confidence > 0.8;",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_confidence;"
        ),
        
        # ===== GIN INDEXES FOR JSON FIELDS =====
        
        # GIN index for vision analysis (contains detection objects, bounding boxes, etc.)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_vision_gin "
            "ON plants_mgmt_diagnosis USING GIN (vision_analysis);",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_vision_gin;"
        ),
        
        # GIN index for RAG context (contains document IDs, relevance scores)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_rag_gin "
            "ON plants_mgmt_diagnosis USING GIN (rag_context);",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_rag_gin;"
        ),
        
        # GIN index for treatment plans (contains recommendations, medications, etc.)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_treatment_gin "
            "ON plants_mgmt_diagnosis USING GIN (treatment_plan);",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_treatment_gin;"
        ),
        
        # ===== KNOWLEDGE DOCUMENT INDEXES =====
        
        # Full-text search index for content
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_content_fts "
            "ON plants_mgmt_knowledgedocument USING GIN (to_tsvector('spanish', title || ' ' || content));",
            reverse_sql="DROP INDEX IF EXISTS idx_knowledge_content_fts;"
        ),
        
        # Index for active documents with plant type filtering
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_active_plants "
            "ON plants_mgmt_knowledgedocument (is_active, plant_types, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_knowledge_active_plants;"
        ),
        
        # GIN index for metadata and tags
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_metadata_gin "
            "ON plants_mgmt_knowledgedocument USING GIN (metadata, tags);",
            reverse_sql="DROP INDEX IF EXISTS idx_knowledge_metadata_gin;"
        ),
        
        # ===== PLANT IMAGE INDEXES =====
        
        # Index for plant images with type filtering
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_image_plant_type_time "
            "ON plants_mgmt_plantimage (plant_id, image_type, uploaded_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_image_plant_type_time;"
        ),
        
        # Partial index for recent images (performance for mobile apps)
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_image_recent "
            "ON plants_mgmt_plantimage (uploaded_at DESC) "
            "WHERE uploaded_at > NOW() - INTERVAL '7 days';",
            reverse_sql="DROP INDEX IF EXISTS idx_image_recent;"
        ),
        
        # ===== COMPOSITE INDEXES FOR COMMON QUERIES =====
        
        # Dashboard query: plants with latest diagnosis
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plant_dashboard "
            "ON plants_mgmt_plant (owner_id, status, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_plant_dashboard;"
        ),
        
        # Analytics query: sensor data with diagnosis correlation
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sensor_analysis "
            "ON plants_mgmt_sensordata (plant_id, timestamp DESC, humidity, temperature);",
            reverse_sql="DROP INDEX IF EXISTS idx_sensor_analysis;"
        ),
        
        # ===== PERFORMANCE MONITORING INDEXES =====
        
        # Index for slow query monitoring
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_performance "
            "ON plants_mgmt_diagnosis (processing_time DESC, created_at DESC) "
            "WHERE processing_time IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_performance;"
        ),
        
        # Index for AI model version tracking
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_model_version "
            "ON plants_mgmt_diagnosis (ai_model_version, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_diagnosis_model_version;"
        ),
        
        # ===== STATISTICS UPDATE =====
        
        # Update table statistics for query planner
        migrations.RunSQL(
            "ANALYZE plants_mgmt_plant;",
            reverse_sql=""
        ),
        migrations.RunSQL(
            "ANALYZE plants_mgmt_sensordata;",
            reverse_sql=""
        ),
        migrations.RunSQL(
            "ANALYZE plants_mgmt_diagnosis;",
            reverse_sql=""
        ),
        migrations.RunSQL(
            "ANALYZE plants_mgmt_knowledgedocument;",
            reverse_sql=""
        ),
        migrations.RunSQL(
            "ANALYZE plants_mgmt_plantimage;",
            reverse_sql=""
        ),
    ]


# Helper functions for index management
def create_index_name(table_name, index_type, fields):
    """Generate consistent index names"""
    field_suffix = '_'.join(fields).replace('_', '')
    return f"idx_{table_name}_{index_type}_{field_suffix}"


def drop_index_safely(index_name):
    """Safely drop index if it exists"""
    return f"DROP INDEX CONCURRENTLY IF EXISTS {index_name};"


def create_partial_index(table_name, fields, condition, index_name=None):
    """Create a partial index for performance optimization"""
    if not index_name:
        index_name = create_index_name(table_name, 'partial', fields)
    
    fields_str = ', '.join(fields)
    return f"""
        CREATE INDEX CONCURRENTLY {index_name}
        ON {table_name} ({fields_str})
        WHERE {condition};
    """


def create_gin_index(table_name, field, index_name=None):
    """Create a GIN index for JSON/text search"""
    if not index_name:
        index_name = f"idx_{table_name}_gin_{field}"
    
    return f"""
        CREATE INDEX CONCURRENTLY {index_name}
        ON {table_name} USING GIN ({field});
    """