"""
Domain Services - Mole-AI Agricultural Intelligence Core
Specialized in Mexican flora, soil chemistry, and organic treatments
"""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CriticalThreshold:
    """Critical safety thresholds for agricultural parameters"""
    parameter: str
    min_safe: Optional[float]
    max_safe: Optional[float]
    critical_min: Optional[float]
    critical_max: Optional[float]
    unit: str
    alert_message: str


@dataclass
class OrganicRecipe:
    """Standardized organic treatment recipe"""
    name: str
    category: str  # pesticide, fertilizer, fungicide
    ingredients: Dict[str, str]  # ingredient: quantity
    preparation: str
    application: str
    frequency: str
    safety_notes: List[str]
    target_pests: List[str]


@dataclass
class MexicanCrop:
    """Mexican crop-specific knowledge"""
    name: str
    scientific_name: str
    optimal_ph_range: Tuple[float, float]
    optimal_humidity_range: Tuple[float, float]
    optimal_temp_range: Tuple[float, float]
    npk_needs: Dict[str, str]  # N: "high/medium/low"
    common_pests: List[str]
    flowering_photoperiod: Optional[str]


class MoleAIAgriculturalCore:
    """
    Core agricultural intelligence system for Mexican crops
    Implements Mole-AI Protocol v3.0
    """
    
    def __init__(self):
        self.critical_thresholds = self._initialize_critical_thresholds()
        self.mexican_crops = self._initialize_mexican_crops()
        self.organic_recipes = self._initialize_organic_recipes()
        logger.info("Mole-AI Agricultural Core initialized")
    
    def _initialize_critical_thresholds(self) -> List[CriticalThreshold]:
        """Define critical safety thresholds for all sensor parameters"""
        return [
            CriticalThreshold(
                parameter="uv_index",
                min_safe=0.0,
                max_safe=10.0,
                critical_min=None,
                critical_max=11.0,
                unit="UVI",
                alert_message="RADIACIÓN UV PELIGROSA - Protección inmediata requerida"
            ),
            CriticalThreshold(
                parameter="humidity",
                min_safe=30.0,
                max_safe=85.0,
                critical_min=10.0,
                critical_max=None,
                unit="%",
                alert_message="DESHIDRATACIÓN CRÍTICA - Riego urgente necesario"
            ),
            CriticalThreshold(
                parameter="temperature",
                min_safe=10.0,
                max_safe=35.0,
                critical_min=None,
                critical_max=40.0,
                unit="°C",
                alert_message="ESTRÉS TÉRMICO SEVERO - Sombra y ventilación urgentes"
            ),
            CriticalThreshold(
                parameter="ph",
                min_safe=5.5,
                max_safe=8.0,
                critical_min=5.0,
                critical_max=9.0,
                unit="pH",
                alert_message="SUELO QUÍMICAMENTE PELIGROSO - Enmiendas urgentes necesarias"
            )
        ]
    
    def _initialize_mexican_crops(self) -> Dict[str, MexicanCrop]:
        """Initialize database of Mexican crops with their specific requirements"""
        return {
            "maiz": MexicanCrop(
                name="Maíz",
                scientific_name="Zea mays",
                optimal_ph_range=(6.0, 7.5),
                optimal_humidity_range=(60, 80),
                optimal_temp_range=(15, 30),
                npk_needs={"N": "high", "P": "medium", "K": "high"},
                common_pests=["pulgones", "cogollero", "palomilla"],
                flowering_photoperiod="12-14 horas luz"
            ),
            "chile": MexicanCrop(
                name="Chile",
                scientific_name="Capsicum annuum",
                optimal_ph_range=(6.5, 7.0),
                optimal_humidity_range=(65, 75),
                optimal_temp_range=(20, 28),
                npk_needs={"N": "medium", "P": "high", "K": "medium"},
                common_pests=["trips", "mosca blanca", "araña roja"],
                flowering_photoperiod="12-13 horas luz"
            ),
            "frijol": MexicanCrop(
                name="Frijol",
                scientific_name="Phaseolus vulgaris",
                optimal_ph_range=(6.0, 6.8),
                optimal_humidity_range=(55, 70),
                optimal_temp_range=(18, 25),
                npk_needs={"N": "low", "P": "medium", "K": "medium"},
                common_pests=["gorgojo", "mosca del frijol", "chicharrita"],
                flowering_photoperiod="11-12 horas luz"
            ),
            "calabaza": MexicanCrop(
                name="Calabaza",
                scientific_name="Cucurbita spp.",
                optimal_ph_range=(6.0, 7.0),
                optimal_humidity_range=(70, 85),
                optimal_temp_range=(18, 28),
                npk_needs={"N": "medium", "P": "high", "K": "high"},
                common_pests=["pulguillas", "gusano cogollero", "mosquita blanca"],
                flowering_photoperiod="12-14 horas luz"
            ),
            "cempasuchil": MexicanCrop(
                name="Cempasúchil",
                scientific_name="Tagetes erecta",
                optimal_ph_range=(6.0, 7.5),
                optimal_humidity_range=(50, 70),
                optimal_temp_range=(15, 25),
                npk_needs={"N": "medium", "P": "high", "K": "medium"},
                common_pests=["pulguillas", "mosca blanca"],
                flowering_photoperiod="12-13 horas luz"
            ),
            "agave": MexicanCrop(
                name="Agave",
                scientific_name="Agave tequilana",
                optimal_ph_range=(6.5, 8.0),
                optimal_humidity_range=(30, 50),
                optimal_temp_range=(20, 35),
                npk_needs={"N": "low", "P": "medium", "K": "low"},
                common_pests=["gusano blanco", "picudo del agave"],
                flowering_photoperiod="12-14 horas luz"
            )
        }
    
    def _initialize_organic_recipes(self) -> Dict[str, OrganicRecipe]:
        """Initialize database of organic treatment recipes for Mexican agriculture"""
        return {
            "insecticida_neem": OrganicRecipe(
                name="Insecticida Orgánico de Neem",
                category="pesticide",
                ingredients={
                    "Hojas de Neem frescas": "500 g",
                    "Agua (sin cloro)": "5 L",
                    "Jabón potásico líquido": "10 ml",
                    "Aceite mineral": "5 ml (opcional, adherente)"
                },
                preparation=(
                    "1. Machacar finamente las hojas de neem\n"
                    "2. Hervir en agua por 15 minutos a fuego lento\n"
                    "3. Dejar reposar 12 horas (fermentación)\n"
                    "4. Colar con tela fina\n"
                    "5. Agregar jabón potásico y aceite mineral\n"
                    "6. Agitar bien antes de usar"
                ),
                application="Asperjar sobre ambas caras de las hojas, preferentemente en horas frescas (mañana temprano o atardecer). Cubrir completamente la planta.",
                frequency="Cada 7 días durante infestación, cada 15 días como preventivo",
                safety_notes=[
                    "No aplicar durante floración para proteger polinizadores",
                    "Mantener alejado de cuerpos de agua",
                    "Usar guantes y mascarilla durante aplicación",
                    "Probar en pequeña área antes de aplicación generalizada"
                ],
                target_pests=["pulgones", "trips", "mosca blanca", "chicharritas", "ácaros"]
            ),
            
            "fungicida_azufre": OrganicRecipe(
                name="Fungicida a Base de Azufre",
                category="fungicide",
                ingredients={
                    "Azufre elemental en polvo": "2 cucharadas soperas",
                    "Agua tibia": "1 L",
                    "Leche fresca": "100 ml (adherente natural)",
                    "Bicarbonato de sodio": "1 cucharadita (potenciador)"
                },
                preparation=(
                    "1. Disolver azufre en agua tibia con constante agitación\n"
                    "2. Agregar leche poco a poco sin dejar de remover\n"
                    "3. Incorporar bicarbonato de sodio\n"
                    "4. Dejar reposar 30 minutos antes de aplicar\n"
                    "5. Agitar vigorosamente antes del uso"
                ),
                application="Asperjar uniformemente sobre follaje afectado, asegurando cobertura completa de hojas y tallos.",
                frequency="Cada 10-14 días durante condiciones de alta humedad o enfermedad activa",
                safety_notes=[
                    "No aplicar con temperaturas superiores a 30°C",
                    "Usar mascarilla durante aplicación",
                    "Evitar inhalación directa del polvo de azufre",
                    "No mezclar con pesticidas a base de cobre"
                ],
                target_pests=["mildeo velloso", "oidio", "roya", "mancha negra"]
            ),
            
            "biofertilizante_compost": OrganicRecipe(
                name="Lixiviado de Composta Aeróbica",
                category="fertilizer",
                ingredients={
                    "Composta madura (preferentemente de estiércol vacuno)": "2 kg",
                    "Agua de lluvia o sin cloro": "10 L",
                    "Melaza de caña": "100 ml",
                    "Roca fosfórica (opcional)": "50 g"
                },
                preparation=(
                    "1. Colocar composta en saco de tela permeable\n"
                    "2. Sumergir en agua, agitar suavemente\n"
                    "3. Añadir melaza como alimento microbiano\n"
                    "4. Dejar en infusión 24-48 horas, agitando cada 6 horas\n"
                    "5. El líquido resultante es el lixiviado (biofertilizante)\n"
                    "6. El sólido restante puede volver a la composta"
                ),
                application=(
                    "FOLIAR: Diluir 1 parte de lixiviado en 10 partes de agua\n"
                    "SUELO: Aplicar directamente al riego, sin diluir\n"
                    "Aplicar al suelo húmedo o al amanecer"
                ),
                frequency="Cada 2-3 semanas durante ciclo vegetativo, semanal durante floración/fructificación",
                safety_notes=[
                    "Usar composta completamente madura (sin patógenos)",
                    "No almacenar más de 48 horas (pierde efectividad)",
                    "Aplicar preferentemente en días nublados",
                    "Combinar con acolchado para mejor retención"
                ],
                target_pests=["deficiencias nutricionales", "suelos compactados", "baja materia orgánica"]
            ),
            
            "repelente_ajo_chile": OrganicRecipe(
                name="Repelente de Ajo y Chile Picante",
                category="pesticide",
                ingredients={
                    "Ajos frescos": "5 dientes grandes",
                    "Chiles habaneros o serranos": "3 unidades",
                    "Cebolla": "1/2 unidad",
                    "Agua": "2 L",
                    "Jabón potásico": "5 ml",
                    "Alcohol etílico (opcional)": "50 ml"
                },
                preparation=(
                    "1. Licuar o machacar finamente ajo, chile y cebolla\n"
                    "2. Mezclar con agua y alcohol si se usa\n"
                    "3. Dejar macerar 24 horas en lugar oscuro\n"
                    "4. Colar y agregar jabón potásico\n"
                    "5. Diluir 1:5 con agua antes de aplicar"
                ),
                application="Asperjar sobre plantas, especialmente zonas de brotes nuevos y envés de hojas donde se concentran las plagas.",
                frequency="Cada 5 días durante alta presión de plagas, cada 15 días como preventivo",
                safety_notes=[
                    "Probar sensibilidad de la planta antes de aplicación general",
                    "No aplicar en horas de máximo sol (puede quemar hojas)",
                    "Rotar con otros pesticidas para evitar resistencia",
                    "Evitar contacto con mucosas y ojos"
                ],
                target_pests=["insectos masticadores", "ninfas", "mosquitas", "chicharritas"]
            )
        }
    
    def check_critical_conditions(self, sensor_data) -> List[str]:
        """
        Check sensor data against critical thresholds
        Returns list of tactical alerts
        """
        alerts = []
        
        if not sensor_data:
            return alerts
        
        for threshold in self.critical_thresholds:
            value = None
            
            # Extract value from sensor_data based on parameter name
            if hasattr(sensor_data, threshold.parameter):
                value = getattr(sensor_data, threshold.parameter)
            
            if value is None:
                continue
            
            # Check critical conditions
            
            if threshold.critical_max and value > threshold.critical_max:
                alerts.append(
                    f"⚠️ ALERTA TÁCTICA: {threshold.alert_message.upper()} - "
                    f"{threshold.parameter.upper()}: {value:.1f}{threshold.unit} "
                    f"(crítico > {threshold.critical_max}{threshold.unit})"
                )
            elif threshold.critical_min and value < threshold.critical_min:
                alerts.append(
                    f"⚠️ ALERTA TÁCTICA: {threshold.alert_message.upper()} - "
                    f"{threshold.parameter.upper()}: {value:.1f}{threshold.unit} "
                    f"(crítico < {threshold.critical_min}{threshold.unit})"
                )
        
        return alerts
    
    def get_crop_recommendations(self, crop_name: str, sensor_data=None) -> Dict[str, Any]:
        """
        Get crop-specific recommendations for Mexican crops
        """
        crop_name_lower = crop_name.lower().replace("á", "a").replace("í", "i")
        
        # Try to find crop by common name
        crop = self.mexican_crops.get(crop_name_lower)
        
        if not crop:
            # Try partial matches
            for key, c in self.mexican_crops.items():
                if crop_name_lower in key or key in crop_name_lower:
                    crop = c
                    break
        
        if not crop:
            return {"error": f"Crop '{crop_name}' not found in Mexican agricultural database"}
        
        recommendations = {
            "crop_info": {
                "name": crop.name,
                "scientific_name": crop.scientific_name,
                "npk_needs": crop.npk_needs
            },
            "optimal_conditions": {
                "ph_range": crop.optimal_ph_range,
                "humidity_range": crop.optimal_humidity_range,
                "temperature_range": crop.optimal_temp_range
            },
            "common_pests": crop.common_pests
        }
        
        # Check current conditions vs optimal
        if sensor_data:
            status_analysis = []
            
            if hasattr(sensor_data, 'ph_level') and sensor_data.ph_level:
                ph = sensor_data.ph_level
                if crop.optimal_ph_range[0] <= ph <= crop.optimal_ph_range[1]:
                    status_analysis.append(f"✅ pH {ph:.1f} dentro del rango óptimo")
                else:
                    status_analysis.append(f"⚠️ pH {ph:.1f} fuera del rango óptimo ({crop.optimal_ph_range[0]}-{crop.optimal_ph_range[1]})")
            
            if hasattr(sensor_data, 'humidity') and sensor_data.humidity:
                hum = sensor_data.humidity
                if crop.optimal_humidity_range[0] <= hum <= crop.optimal_humidity_range[1]:
                    status_analysis.append(f"✅ Humedad {hum:.1f}% dentro del rango óptimo")
                else:
                    status_analysis.append(f"⚠️ Humedad {hum:.1f}% fuera del rango óptimo ({crop.optimal_humidity_range[0]}-{crop.optimal_humidity_range[1]}%)")
            
            if hasattr(sensor_data, 'temperature') and sensor_data.temperature:
                temp = sensor_data.temperature
                if crop.optimal_temp_range[0] <= temp <= crop.optimal_temp_range[1]:
                    status_analysis.append(f"✅ Temperatura {temp:.1f}°C dentro del rango óptimo")
                else:
                    status_analysis.append(f"⚠️ Temperatura {temp:.1f}°C fuera del rango óptimo ({crop.optimal_temp_range[0]}-{crop.optimal_temp_range[1]}°C)")
            
            recommendations["current_status"] = status_analysis
        
        return recommendations
    
    def recommend_organic_treatment(self, problem_type: str, crop_name: str = None) -> List[OrganicRecipe]:
        """
        Recommend organic treatments based on problem type and crop
        """
        problem_type_lower = problem_type.lower()
        recommendations = []
        
        # Mapping of problems to recipe keys
        problem_mapping = {
            "plaga": ["insecticida_neem", "repelente_ajo_chile"],
            "insecto": ["insecticida_neem", "repelente_ajo_chile"],
            "hongo": ["fungicida_azufre"],
            "enfermedad": ["fungicida_azufre"],
            "deficiencia": ["biofertilizante_compost"],
            "nutriente": ["biofertilizante_compost"],
            "fertilizante": ["biofertilizante_compost"],
            "crecimiento": ["biofertilizante_compost"]
        }
        
        # Find matching problem type
        for key, recipe_keys in problem_mapping.items():
            if key in problem_type_lower:
                for recipe_key in recipe_keys:
                    if recipe_key in self.organic_recipes:
                        recommendations.append(self.organic_recipes[recipe_key])
                break
        
        return recommendations
    
    def format_recipe_markdown(self, recipe: OrganicRecipe) -> str:
        """
        Format organic recipe as structured markdown
        """
        markdown = f"""## 🧪 {recipe.name.upper()}

**Categoría**: {recipe.category}

### 📦 Ingredientes:
"""
        for ingredient, quantity in recipe.ingredients.items():
            markdown += f"- **{ingredient}**: {quantity}\n"
        
        markdown += f"""
### 🔬 Preparación:
{recipe.preparation}

### 🌿 Aplicación:
{recipe.application}

### ⏰ Frecuencia:
{recipe.frequency}

### ⚠️ Notas de Seguridad:
"""
        for note in recipe.safety_notes:
            markdown += f"- {note}\n"
        
        return markdown