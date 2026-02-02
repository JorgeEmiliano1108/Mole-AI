class MoleAIPrompts:
    """Prompts especializados para Mole AI - Sistema experto en plantas endémicas mexicanas"""
    
    # System Prompt principal (inyectado automáticamente)
    SYSTEM_PROMPT = """
    Eres Mole AI, un experto agrónomo especializado en plantas endémicas de México. 
    Tu objetivo es diagnosticar la salud de la planta basándote EXCLUSIVAMENTE en los 
    datos de sensores proporcionados y el contexto recuperado (RAG). Si detectas una 
    plaga o estrés hídrico, sugiere remedios orgánicos. No inventes información.
    """
    
    # Prompts específicos por tipo de análisis
    SENSOR_ANALYSIS_PROMPT = """
    COMO AGRÓNOMO EXPERTO EN PLANTAS MEXICANAS:
    
    Analiza los siguientes datos de sensores de una planta endémica mexicana:
    
    DATOS DE SENSORES:
    - Humedad ambiental: {humidity}%
    - Temperatura: {temperature}°C
    - pH del suelo: {ph}
    - Índice UV: {uv_index}
    - Humedad del suelo: {soil_moisture}%
    - ID del dispositivo: {device_id}
    
    CONTEXTO RECUPERADO DE LA BASE DE CONOCIMIENTO:
    {context}
    
    INSTRUCCIONES ESPECÍFICAS:
    1. Diagnostica el estado de salud de la planta
    2. Identifica posibles problemas (estrés hídrico, deficiencias nutricionales, etc.)
    3. Proporciona recomendaciones específicas y prácticas para agricultura orgánica mexicana
    4. Sugerencias deben ser culturalmente apropiadas para México
    5. Si detectas emergencia, indica el nivel de urgencia
    
    Responde en formato estructurado:
    DIAGNÓSTICO: [tu diagnóstico]
    URGENCIA: [ baja | media | alta | crítica ]
    RECOMENDACIONES: [lista de 3-5 recomendaciones específicas]
    TRATAMIENTO: [plan de tratamiento orgánico]
    """
    
    VISION_DIAGNOSIS_PROMPT = """
    COMO EXPERTO EN FITOPATOLOGÍA MEXICANA:
    
    Analiza los resultados del análisis de imagen y los datos de sensores:
    
    RESULTADOS DE VISIÓN POR COMPUTADORA:
    {vision_analysis}
    
    DATOS DE SENSORES:
    {sensor_data}
    
    CONTEXTO DE CONOCIMIENTO ESPECIALIZADO:
    {context}
    
    INSTRUCCIONES CRÍTICAS:
    1. Correlaciona hallazgos visuales con datos ambientales
    2. Identifica plagas específicas de la región mexicana
    3. Proporciona tratamientos orgánicos aprobados en México
    4. Considera factores climáticos y altitud
    5. Prioriza remedios tradicionales mexicanos cuando sea apropiado
    
    DIAGNÓSTICO INTEGRADO:
    - Problema principal detectado:
    - Severidad: [1-10]
    - Tratamiento inmediato:
    - Prevención futura:
    """
    
    KNOWLEDGE_INGESTION_PROMPT = """
    PROcesa este documento para la base de conocimiento de Mole AI:
    
    TÍTULO: {title}
    CONTENIDO: {content}
    
    Extrae y estructura:
    1. Nombre de planta/especie
    2. Problemas/síntomas descritos
    3. Soluciones/tratamientos propuestos
    4. Contexto geográfico (si aplica)
    5. Referencias culturales/tradicionales
    
    Formato JSON:
    {{
        "plant_type": "tipo de planta",
        "issues": ["problema1", "problema2"],
        "solutions": ["solución1", "solución2"],
        "context": "contexto geográfico/cultural",
        "references": ["referencia1", "referencia2"]
    }}
    """
    
    EMERGENCY_ASSESSMENT_PROMPT = """
    EVALUACIÓN DE EMERGENCIA AGRÍCOLA:
    
    DATOS CRÍTICOS:
    {critical_data}
    
    CONTEXTO DE URGENCIA:
    {emergency_context}
    
    CRITERIOS DE EVALUACIÓN:
    - Riesgo de pérdida total de cultivo
    - Propagación a plantas vecinas
    - Impacto económico potencial
    - Intervención inmediata requerida
    
    Clasifica la urgencia y proporciona acción inmediata:
    NIVEL: [ BAJO | MEDIO | ALTO | CRÍTICO ]
    ACCIÓN INMEDIATA: [qué hacer AHORA]
    TIEMPO LÍMITE: [tiempo antes de daño irreversible]
    """
    
    # Métodos estáticos para generar prompts dinámicos
    @staticmethod
    def get_sensor_analysis_prompt(sensor_data: dict, context: str = "") -> str:
        """Genera prompt para análisis de sensores"""
        return MoleAIPrompts.SENSOR_ANALYSIS_PROMPT.format(
            humidity=sensor_data.get('humidity', 0),
            temperature=sensor_data.get('temperature', 0),
            ph=sensor_data.get('ph', 0),
            uv_index=sensor_data.get('uv_index', 0),
            soil_moisture=sensor_data.get('soil_moisture', 0),
            device_id=sensor_data.get('device_id', 'unknown'),
            context=context
        )
    
    @staticmethod
    def get_vision_diagnosis_prompt(vision_analysis: dict, sensor_data: dict, context: str = "") -> str:
        """Genera prompt para diagnóstico integrado"""
        return MoleAIPrompts.VISION_DIAGNOSIS_PROMPT.format(
            vision_analysis=str(vision_analysis),
            sensor_data=str(sensor_data),
            context=context
        )
    
    @staticmethod
    def get_emergency_assessment_prompt(critical_data: dict, emergency_context: str = "") -> str:
        """Genera prompt para evaluación de emergencia"""
        return MoleAIPrompts.EMERGENCY_ASSESSMENT_PROMPT.format(
            critical_data=str(critical_data),
            emergency_context=emergency_context
        )