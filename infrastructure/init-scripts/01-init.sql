-- Mole AI v2.0 - PostgreSQL Initialization
-- Executed on container startup

-- Create extension for UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create diagnosticos table
CREATE TABLE IF NOT EXISTS diagnosticos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID,
    estado VARCHAR(50) NOT NULL,
    confianza FLOAT NOT NULL CHECK (confianza >= 0 AND confianza <= 1),
    especie VARCHAR(100),
    sintomas TEXT,
    diagnostico TEXT NOT NULL,
    recomendaciones TEXT,
    fuentes TEXT,
    sensores JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient queries
CREATE INDEX idx_diagnosticos_plant_id ON diagnosticos(plant_id);
CREATE INDEX idx_diagnosticos_created_at ON diagnosticos(created_at DESC);
CREATE INDEX idx_diagnosticos_estado ON diagnosticos(estado);

-- Create audit table for RAG uploads
CREATE TABLE IF NOT EXISTS rag_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    chunks INT DEFAULT 0,
    pages INT DEFAULT 0,
    file_size BIGINT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_rag_sources_uploaded ON rag_sources(uploaded_at DESC);

-- Create view for statistics
CREATE OR REPLACE VIEW diagnosticos_stats AS
SELECT 
    DATE(created_at) as fecha,
    estado,
    COUNT(*) as total,
    AVG(confianza) as confianza_promedio,
    MIN(confianza) as confianza_minima,
    MAX(confianza) as confianza_maxima
FROM diagnosticos
GROUP BY DATE(created_at), estado
ORDER BY fecha DESC, estado;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON diagnosticos TO mole_user;
GRANT SELECT, INSERT, UPDATE ON rag_sources TO mole_user;
GRANT SELECT ON diagnosticos_stats TO mole_user;

-- Log initialization
SELECT 'Mole AI v2.0 - PostgreSQL initialized successfully' as status;
