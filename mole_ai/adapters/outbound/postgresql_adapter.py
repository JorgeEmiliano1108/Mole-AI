import os
import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from ...domain.ports import SensorDataPort, DiagnosticPersistencePort
from ...domain.models.plant import SensorData, PlantDiagnosis, DiagnosticFilter
from ...domain.exceptions import (
    DatabaseConnectionError, 
    PersistenceError, 
    InvalidSensorDataError
)

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(SensorDataPort, DiagnosticPersistencePort):
    """Adaptador PostgreSQL para persistencia de datos"""
    
    def __init__(self):
        self.connection_params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "mole_ai_db"),
            "user": os.getenv("POSTGRES_USER", "mole_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "mole_pass_2026"),
            "cursor_factory": RealDictCursor
        }
        self._connection = None

    async def initialize(self):
        """Inicializa la conexión a PostgreSQL"""
        try:
            await self._ensure_connection()
            await self._create_tables_if_not_exist()
            logger.info("✅ PostgreSQL Adapter inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando PostgreSQL: {str(e)}")
            raise DatabaseConnectionError(f"Error conexión DB: {str(e)}")

    async def _ensure_connection(self):
        """Asegura que hay una conexión activa"""
        try:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg2.connect(**self.connection_params)
                self._connection.autocommit = False
                logger.info("✅ Conexión a PostgreSQL establecida")
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {str(e)}")
            raise DatabaseConnectionError(f"Error conexión: {str(e)}")

    async def _create_tables_if_not_exist(self):
        """Crea tablas si no existen"""
        await self._ensure_connection()
        
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS plantas (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                nombre VARCHAR(100) NOT NULL,
                especie VARCHAR(100),
                ubicacion VARCHAR(200),
                fecha_plantacion DATE,
                activa BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sensores (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                planta_id UUID REFERENCES plantas(id) ON DELETE CASCADE,
                ph FLOAT NOT NULL CHECK (ph >= 0 AND ph <= 14),
                humedad FLOAT NOT NULL CHECK (humedad >= 0 AND humedad <= 100),
                temperatura FLOAT NOT NULL CHECK (temperatura >= -50 AND temperatura <= 60),
                uv FLOAT NOT NULL CHECK (uv >= 0 AND uv <= 15),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS diagnosticos (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                planta_id UUID REFERENCES plantas(id) ON DELETE CASCADE,
                imagen_url VARCHAR(500),
                estado VARCHAR(50) NOT NULL CHECK (estado IN ('Sana', 'Atención', 'Peligro')),
                confianza FLOAT NOT NULL CHECK (confianza >= 0 AND confianza <= 1),
                especie VARCHAR(100),
                sintomas TEXT,
                diagnostico TEXT NOT NULL,
                recomendaciones TEXT,
                fuentes TEXT,
                sensor_data JSONB,
                modelo_utilizado VARCHAR(100) NOT NULL,
                tiempo_inferencia FLOAT,
                requiere_accion_humana BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_sensores_planta_timestamp 
            ON sensores(planta_id, timestamp DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_diagnosticos_planta_created 
            ON diagnosticos(planta_id, created_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_diagnosticos_estado 
            ON diagnosticos(estado, created_at DESC)
            """
        ]
        
        try:
            with self._connection.cursor() as cursor:
                for sql in tables_sql:
                    cursor.execute(sql)
                self._connection.commit()
                logger.info("✅ Tablas verificadas/creadas correctamente")
        except Exception as e:
            logger.error(f"Error creando tablas: {str(e)}")
            self._connection.rollback()
            raise PersistenceError(f"Error creación tablas: {str(e)}")

    # Métodos de SensorDataPort
    async def get_latest_sensor_data(
        self, 
        plant_id: Optional[str] = None
    ) -> SensorData:
        """Obtiene datos más recientes de sensores"""
        try:
            await self._ensure_connection()
            
            with self._connection.cursor() as cursor:
                if plant_id:
                    cursor.execute("""
                        SELECT ph, humedad, temperatura as temp, uv, timestamp, 
                               planta_id as plant_id
                        FROM sensores 
                        WHERE planta_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (plant_id,))
                else:
                    cursor.execute("""
                        SELECT ph, humedad, temperatura as temp, uv, timestamp,
                               planta_id as plant_id
                        FROM sensores 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """)
                
                result = cursor.fetchone()
                if result:
                    return SensorData(
                        ph=result['ph'],
                        humedad=result['humedad'],
                        temp=result['temp'],
                        uv=result['uv'],
                        timestamp=result['timestamp'],
                        plant_id=str(result['plant_id']) if result['plant_id'] else None
                    )
                else:
                    # Retornar datos por defecto si no hay registros
                    return SensorData(
                        ph=6.5,
                        humedad=65.0,
                        temp=22.0,
                        uv=0.5,
                        plant_id=plant_id
                    )
                    
        except Exception as e:
            logger.error(f"Error obteniendo datos sensores: {str(e)}")
            raise InvalidSensorDataError(f"Error sensores: {str(e)}")

    async def save_sensor_data(
        self, 
        sensor_data: SensorData
    ) -> bool:
        """Persiste datos de sensores"""
        try:
            await self._ensure_connection()
            
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sensores (planta_id, ph, humedad, temperatura, uv, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    sensor_data.plant_id,
                    sensor_data.ph,
                    sensor_data.humedad,
                    sensor_data.temp,
                    sensor_data.uv,
                    sensor_data.timestamp or datetime.now()
                ))
                
                result = cursor.fetchone()
                self._connection.commit()
                
                if result:
                    logger.info(f"✅ Datos sensores guardados: ID {result['id']}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error guardando datos sensores: {str(e)}")
            self._connection.rollback()
            raise PersistenceError(f"Error save sensores: {str(e)}")

    # Métodos de DiagnosticPersistencePort
    async def save_diagnosis(
        self, 
        diagnosis: PlantDiagnosis
    ) -> str:
        """Guarda diagnóstico completo"""
        try:
            await self._ensure_connection()
            
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO diagnosticos (
                        planta_id, imagen_url, estado, confianza, especie,
                        sintomas, diagnostico, recomendaciones, fuentes,
                        sensor_data, modelo_utilizado, tiempo_inferencia,
                        requiere_accion_humana
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    diagnosis.plant_id,
                    diagnosis.imagen.filename if diagnosis.imagen else None,
                    diagnosis.estado.value,
                    diagnosis.confianza,
                    diagnosis.especie,
                    json.dumps(diagnosis.sintomas) if diagnosis.sintomas else None,
                    diagnosis.diagnostico,
                    json.dumps(diagnosis.recomendaciones) if diagnosis.recomendaciones else None,
                    json.dumps(diagnosis.fuentes) if diagnosis.fuentes else None,
                    Json({
                        "ph": diagnosis.sensores.ph,
                        "humedad": diagnosis.sensores.humedad,
                        "temp": diagnosis.sensores.temp,
                        "uv": diagnosis.sensores.uv,
                        "timestamp": diagnosis.sensores.timestamp.isoformat() if diagnosis.sensores.timestamp else None
                    }),
                    diagnosis.modelo_utilizado,
                    diagnosis.tiempo_inferencia,
                    diagnosis.requiere_accion_humana
                ))
                
                result = cursor.fetchone()
                self._connection.commit()
                
                if result:
                    diagnosis.id = str(result['id'])
                    logger.info(f"✅ Diagnóstico guardado: ID {diagnosis.id}")
                    return diagnosis.id
                else:
                    raise PersistenceError("No se pudo guardar diagnóstico")
                    
        except Exception as e:
            logger.error(f"Error guardando diagnóstico: {str(e)}")
            self._connection.rollback()
            raise PersistenceError(f"Error save diagnóstico: {str(e)}")

    async def get_diagnosis_history(
        self, 
        plant_id: str, 
        limit: int = 10
    ) -> List[PlantDiagnosis]:
        """Obtiene historial de diagnósticos"""
        try:
            await self._ensure_connection()
            
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, planta_id, estado, confianza, especie, sintomas,
                           diagnostico, recomendaciones, fuentes, sensor_data,
                           modelo_utilizado, tiempo_inferencia, requiere_accion_humana,
                           created_at
                    FROM diagnosticos 
                    WHERE planta_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (plant_id, limit))
                
                results = cursor.fetchall()
                diagnoses = []
                
                for result in results:
                    sensor_data_dict = result['sensor_data']
                    sensores = SensorData(
                        ph=sensor_data_dict.get('ph', 0),
                        humedad=sensor_data_dict.get('humedad', 0),
                        temp=sensor_data_dict.get('temp', 0),
                        uv=sensor_data_dict.get('uv', 0),
                        timestamp=datetime.fromisoformat(sensor_data_dict['timestamp']) if sensor_data_dict.get('timestamp') else None
                    )
                    
                    diagnosis = PlantDiagnosis(
                        id=str(result['id']),
                        planta_id=str(result['planta_id']),
                        estado=result['estado'],
                        confianza=result['confianza'],
                        especie=result['especie'],
                        sintomas=json.loads(result['sintomas']) if result['sintomas'] else [],
                        diagnostico=result['diagnostico'],
                        recomendaciones=json.loads(result['recomendaciones']) if result['recomendaciones'] else [],
                        fuentes=json.loads(result['fuentes']) if result['fuentes'] else [],
                        sensores=sensores,
                        modelo_utilizado=result['modelo_utilizado'],
                        tiempo_inferencia=result['tiempo_inferencia'],
                        requiere_accion_humana=result['requiere_accion_humana'],
                        created_at=result['created_at']
                    )
                    
                    diagnoses.append(diagnosis)
                
                logger.info(f"✅ Recuperados {len(diagnoses)} diagnósticos para planta {plant_id}")
                return diagnoses
                
        except Exception as e:
            logger.error(f"Error obteniendo historial diagnósticos: {str(e)}")
            raise PersistenceError(f"Error get historial: {str(e)}")

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema"""
        try:
            await self._ensure_connection()
            
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_diagnosticos,
                        COUNT(CASE WHEN created_at >= CURRENT_DATE THEN 1 END) as diagnosticos_hoy,
                        AVG(confianza) as promedio_confianza,
                        COUNT(DISTINCT planta_id) as plantas_activas
                    FROM diagnosticos
                """)
                
                metrics = cursor.fetchone()
                
                cursor.execute("""
                    SELECT modelo_utilizado 
                    FROM diagnosticos 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                
                model_result = cursor.fetchone()
                
                return {
                    "total_diagnosticos": metrics['total_diagnosticos'] or 0,
                    "diagnosticos_hoy": metrics['diagnosticos_hoy'] or 0,
                    "promedio_confianza": float(metrics['promedio_confianza'] or 0),
                    "plantas_activas": metrics['plantas_activas'] or 0,
                    "modelo_actual": model_result['modelo_utilizado'] if model_result else "Desconocido"
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {str(e)}")
            return {}

    async def close(self):
        """Cierra la conexión a la base de datos"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("🔌 Conexión PostgreSQL cerrada")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()