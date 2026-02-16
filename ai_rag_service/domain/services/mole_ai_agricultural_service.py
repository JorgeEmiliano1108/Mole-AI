"""
Domain Services - Mole-AI Agricultural Expert System
"""
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import logging

from domain.models import SensorData

logger = logging.getLogger(__name__)


@dataclass
class TacticalAlert:
    """Tactical alert for critical agricultural conditions"""
    severity: str  # CRITICAL, WARNING, INFO
    message: str
    immediate_action: str
    urgency_hours: int


@dataclass 
class AgriculturalRecipe:
    """Precise agricultural treatment recipe"""
    name: str
    ingredients: List[Dict[str, str]]  # ingredient: quantity
    preparation: str
    application_method: str
    frequency: str
    safety_notes: List[str]


@dataclass
class SoilAnalysis:
    """Soil chemistry analysis results"""
    ph: float
    nitrogen_ppm: Optional[float] = None
    phosphorus_ppm: Optional[float] = None
    potassium_ppm: Optional[float] = None
    organic_matter_percent: Optional[float] = None
    texture: Optional[str] = None  # sandy, clay, loam
    recommendations: List[str] = None


class MoleAIAgriculturalService:
    """Mole-AI expert system for Mexican agriculture"""
    
    def __init__(self):
        self.mexican_flora_database = {
            "maiz": {
                "common_name": "Maíz",
                "optimal_ph": (6.0, 7.5),
                "humidity_range": (60, 80),
                "temperature_range": (15, 30),
                "nutrients_needs": {"N": "high", "P": "medium", "K": "high"}
            },
            "chile": {
                "common_name": "Chile", 
                "optimal_ph": (6.5, 7.0),
                "humidity_range": (65, 75),
                "temperature_range": (20, 28),
                "nutrients_needs": {"N": "medium", "P": "high", "K": "medium"}
            },
            "frijol": {
                "common_name": "Frijol",
                "optimal_ph": (6.0, 6.8),
                "humidity_range": (55, 70),
                "temperature_range": (18, 25),
                "nutrients_needs": {"N": "low", "P": "medium", "K": "medium"}
            },
            "calabaza": {
                "common_name": "Calabaza",
                "optimal_ph": (6.0, 7.0),
                "humidity_range": (70, 85),
                "temperature_range": (18, 28),
                "nutrients_needs": {"N": "medium", "P": "high", "K": "high"}
            }
        }
        
        self.organic_treatments = {
            "pesticide_neem": AgriculturalRecipe(
                name="Pesticida de Neem Orgánico",
                ingredients=[
                    {"Hojas de Neem frescas": "500g"},
                    {"Agua": "5 litros"},
                    {"Jabón potásico líquido": "10ml"}
                ],
                preparation="Machacar hojas de neem, hervir en agua por 15 minutos, colar y agregar jabón potásico.",
                application_method="Asperjar por la mañana o tarde, cubriendo ambas caras de las hojas",
                frequency="Cada 7 días durante infestación",
                safety_notes=["No aplicar en floración", "Mantener alejado de abejas", "Usar guantes"]
            ),
            "fungicide_sulfur": AgriculturalRecipe(
                name="Fungida a Base de Azufre",
                ingredients=[
                    {"Azufre en polvo": "2 cucharadas soperas"},
                    {"Agua": "1 litro"},
                    {"Leche": "100ml"}
                ],
                preparation="Disolver azufre en agua tibia, agregar leche como adherente",
                application_method="Asperjar uniformemente sobre follaje",
                frequency="Cada 10-14 días",
                safety_notes=["No aplicar con temperaturas >30°C", "Usar mascarilla"]
            ),
            "fertilizer_compost_tea": AgriculturalRecipe(
                name="Lixiviado de Composta",
                ingredients=[
                    {"Composta madura": "2kg"},
                    {"Agua sin cloro": "10 litros"},
                    {"Melaza": "100ml"}
                ],
                preparation="Compost en agua por 24-48h, agregar melaza, airear regularmente",
                application_method="Aplicar al suelo o asperjar follaje diluido 1:10",
                frequency="Cada 2 semanas",
                safety_notes=["Usar compost sin patógenos", "Aplicar al suelo húmedo"]
            )
        }
    
    def analyze_sensor_data(self, sensor_data: SensorData, crop_type: str = None) -> List[TacticalAlert]:
        """Analyze sensor data and generate tactical alerts"""
        alerts = []
        
        if not sensor_data:
            return alerts
        
        # Humidity analysis
        if sensor_data.humidity is not None:
            if sensor_data.humidity < 10:
                alerts.append(TacticalAlert(
                    severity="CRITICAL",
                    message="PELIGRO DE DESHIDRATACIÓN CRÍTICA",
                    immediate_action="Regar inmediatamente, aplicar mulch orgánico, crear sombra",
                    urgency_hours=2
                ))
            elif sensor_data.humidity < 30:
                alerts.append(TacticalAlert(
                    severity="WARNING", 
                    message="Estrés por sequía inminente",
                    immediate_action="Programar riego urgente, monitorear constantemente",
                    urgency_hours=12
                ))
            elif sensor_data.humidity > 95:
                alerts.append(TacticalAlert(
                    severity="WARNING",
                    message="Riesgo de asfixia radicular",
                    immediate_action="Mejorar drenaje, reducir riego, airear suelo",
                    urgency_hours=6
                ))
        
        # pH analysis
        if sensor_data.ph_level is not None:
            if sensor_data.ph_level < 5.0:
                alerts.append(TacticalAlert(
                    severity="CRITICAL",
                    message="SUELO EXTREMADAMENTE ÁCIDO - Toxicidad inminente",
                    immediate_action="Aplicar cal agrícola 2-3 ton/ha, evaluación profesional urgente",
                    urgency_hours=24
                ))
            elif sensor_data.ph_level > 9.0:
                alerts.append(TacticalAlert(
                    severity="CRITICAL", 
                    message="SUELO EXTREMADAMENTE ALCALINO - Bloqueo nutricional",
                    immediate_action="Aplicar azufre elemental 500kg/ha, ácido húmico",
                    urgency_hours=24
                ))
        
        # Temperature analysis
        if sensor_data.temperature is not None:
            if sensor_data.temperature > 40:
                alerts.append(TacticalAlert(
                    severity="CRITICAL",
                    message="PELIGRO DE MUERTE TÉRMICA",
                    immediate_action="Sombra 100%, riego por aspersión, ventilación forzada",
                    urgency_hours=1
                ))
            elif sensor_data.temperature < 0:
                alerts.append(TacticalAlert(
                    severity="CRITICAL",
                    message="PELIGRO DE HELADA MORTAL", 
                    immediate_action="Cubrir plantas, generar calor, riego antihelada",
                    urgency_hours=4
                ))
        
        # UV radiation analysis
        if sensor_data.uv_index is not None:
            if sensor_data.uv_index > 11:
                alerts.append(TacticalAlert(
                    severity="CRITICAL",
                    message="RADIACIÓN UV PELIGROSA - Daño celular inevitable",
                    immediate_action="Sombra total, bloqueadores UV, aplicación antirradiación",
                    urgency_hours=1
                ))
        
        return alerts
    
    def recommend_organic_treatment(self, condition: str, crop_type: str = None) -> Optional[AgriculturalRecipe]:
        """Recommends organic treatment based on condition"""
        condition = condition.lower()
        
        treatment_map = {
            "plaga": "pesticide_neem",
            "insectos": "pesticide_neem", 
            "hongos": "fungicide_sulfur",
            "deficiencia": "fertilizer_compost_tea",
            "nutrientes": "fertilizer_compost_tea",
            "crecimiento": "fertilizer_compost_tea"
        }
        
        for key, treatment_id in treatment_map.items():
            if key in condition:
                return self.organic_treatments.get(treatment_id)
        
        return None
    
    def analyze_soil_needs(self, soil_analysis: SoilAnalysis) -> Dict[str, Any]:
        """Analyze soil analysis and provide recommendations"""
        recommendations = {}
        
        # pH adjustment
        if soil_analysis.ph < 6.0:
            recommendations["ph_adjustment"] = {
                "need": "raise_ph",
                "treatment": "Aplicar cal agrícola (calcita o dolomita)",
                "quantity": f"{(6.0 - soil_analysis.ph) * 200:.0f} kg/ha aprox."
            }
        elif soil_analysis.ph > 7.5:
            recommendations["ph_adjustment"] = {
                "need": "lower_ph", 
                "treatment": "Aplicar azufre elemental",
                "quantity": f"{(soil_analysis.ph - 7.5) * 100:.0f} kg/ha aprox."
            }
        
        # Nutrient analysis
        if soil_analysis.nitrogen_ppm:
            if soil_analysis.nitrogen_ppm < 20:
                recommendations["nitrogen"] = "Deficiente - Aplicar compost 5t/ha o abono orgánico nitrogenado"
            elif soil_analysis.nitrogen_ppm > 50:
                recommendations["nitrogen"] = "Excesivo - Reducir fertilización nitrogenada"
        
        if soil_analysis.phosphorus_ppm:
            if soil_analysis.phosphorus_ppm < 15:
                recommendations["phosphorus"] = "Deficiente - Aplicar fosforita orgánica o harina de huesos"
            elif soil_analysis.phosphorus_ppm > 40:
                recommendations["phosphorus"] = "Excesivo - Evitar fertilización fosfatada"
        
        if soil_analysis.potassium_ppm:
            if soil_analysis.potassium_ppm < 100:
                recommendations["potassium"] = "Deficiente - Aplicar ceniza de madera o potasa orgánica"
            elif soil_analysis.potassium_ppm > 300:
                recommendations["potassium"] = "Excesivo - Reducir fertilización potásica"
        
        return recommendations
    
    def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Get crop information from Mexican flora database"""
        crop_name = crop_name.lower()
        return self.mexican_flora_database.get(crop_name)