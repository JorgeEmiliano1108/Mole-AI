from src.application.ports.output import LLMService
from src.domain.prompts import PromptTemplates
from src.domain.models import DatosSensores, AnalisisSensores

class SensorAnalysisUseCase:
    def __init__(self, llm: LLMService):
        self.llm = llm

    async def run(self, sensor_data: DatosSensores) -> AnalisisSensores:
        """
        Analiza datos de sensores ambientales para agricultura.
        
        Args:
            sensor_data: Datos de humedad, temperatura, pH, UV
        
        Returns:
            AnalisisSensores con diagnóstico y recomendaciones
        """
        
        # 1. Validar datos y generar alertas iniciales
        alertas = self._check_alerts(sensor_data)
        
        # 2. Generar prompt de análisis
        datos_dict = {
            "humedad": f"{sensor_data.humedad}%" if sensor_data.humedad else "No disponible",
            "temperatura": f"{sensor_data.temperatura}°C" if sensor_data.temperatura else "No disponible",
            "ph": sensor_data.ph if sensor_data.ph else "No disponible",
            "uv": sensor_data.uv if sensor_data.uv else "No disponible"
        }
        
        full_prompt = PromptTemplates.get_sensor_prompt(datos_dict)
        
        # 3. Obtener análisis del LLM
        analysis = await self.llm.generate_response(full_prompt)
        
        # 4. Determinar estado de salud general
        estado_salud = self._determine_health_status(sensor_data, alertas)
        
        # 5. Extraer recomendaciones del análisis
        recomendaciones = self._extract_recommendations(analysis)
        
        return AnalisisSensores(
            datos=sensor_data,
            diagnostico=analysis,
            recomendaciones=recomendaciones,
            estado_salud=estado_salud,
            alertas=alertas
        )
    
    def _check_alerts(self, data: DatosSensores) -> list:
        alertas = []
        
        if data.humedad is not None:
            if data.humedad < 30:
                alertas.append("Humedad crítica: Riego inmediato necesario")
            elif data.humedad < 40:
                alertas.append("Humedad baja: Considerar riego pronto")
            elif data.humedad > 80:
                alertas.append("Humedad excesiva: Riesgo de hongos")
        
        if data.temperatura is not None:
            if data.temperatura > 35:
                alertas.append("Temperatura alta: Proporcionar sombra")
            elif data.temperatura < 5:
                alertas.append("Temperatura baja: Proteger plantas")
        
        if data.ph is not None:
            if data.ph < 5.5:
                alertas.append("Suelo muy ácido: Aplicar cal o compost")
            elif data.ph > 7.5:
                alertas.append("Suelo muy alcalino: Aplicar materia orgánica ácida")
        
        if data.uv is not None and data.uv > 8:
            alertas.append("Índice UV alto: Proteger plantas sensibles")
        
        return alertas
    
    def _determine_health_status(self, data: DatosSensores, alertas: list) -> str:
        if len(alertas) == 0:
            return "Óptimo"
        elif len(alertas) == 1:
            return "Bueno - Requiere atención"
        elif len(alertas) <= 3:
            return "Regular - Requiere intervención"
        else:
            return "Crítico - Requiere acción inmediata"
    
    def _extract_recommendations(self, analysis: str) -> list:
        recomendaciones = []
        lines = analysis.split('\n')
        
        keywords = ['recomienda', 'sugiere', 'aplica', 'usa', 'debe', 'considera']
        
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('RECOMENDACIONES'):
                    recomendaciones.append(clean_line)
        
        return recomendaciones[:7] if recomendaciones else [
            "Monitorea constantemente las condiciones",
            "Ajusta riego según condiciones climáticas",
            "Considera métodos orgánicos para correcciones"
        ]