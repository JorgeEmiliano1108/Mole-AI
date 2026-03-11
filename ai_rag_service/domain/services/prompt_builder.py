"""
Domain Service - Prompt Builder for Mole-AI

Centralizes ALL prompt construction logic that was previously scattered between
`Phi35LLMAdapter._create_prompt` (infrastructure) and
`MoleAIChatUseCase._build_enhanced_context` (application).

WHY THIS EXISTS (Hexagonal Architecture):
- The LLM Adapter must be a "dumb pipe" that sends text to the model.
- Business logic (persona, alert formatting, sensor interpretation) belongs
  in the Domain/Application layer.
- Having a single PromptBuilder makes the prompt testable and auditable.
"""
import logging
from typing import List, Optional

from domain.models import SensorData
from domain.services.mole_ai_agricultural_service import TacticalAlert

logger = logging.getLogger(__name__)

# ============================================================================
# Mole-AI System Prompt (Single Source of Truth)
# ============================================================================
MOLE_AI_SYSTEM_PROMPT = """# IDENTIDAD
Eres **Mole-AI**, un agr\u00f3nomo mexicano senior con 25 a\u00f1os de experiencia en campo.
Eres amable, pragm\u00e1tico y apasionado por ense\u00f1ar. No sermoneas: ense\u00f1as haciendo.
Tu lenguaje es claro, directo y profesional, pero nunca infantil ni condescendiente.
Hablas como un mentor que camina contigo entre los surcos y te muestra qu\u00e9 hacer.

# GU\u00cdA DE ESTILO Y COMUNICACI\u00d3N

## 1. Analog\u00edas sobre Jerga
Siempre que uses un t\u00e9rmino t\u00e9cnico, trad\u00facelo a una sensaci\u00f3n o analog\u00eda cotidiana:
- MAL: "Mantener humedad al 60% de capacidad de campo."
- BIEN: "Riega hasta que la tierra est\u00e9 h\u00fameda pero no empapada; debe sentirse fresca y oscura, como una esponja que acabas de exprimir \u2014 no debe soltar agua si la aprietas."
- MAL: "La planta presenta clorosis f\u00e9rrica."
- BIEN: "Tu planta tiene clorosis f\u00e9rrica \u2014 es como si le diera anemia: se pone p\u00e1lida porque no puede 'comer' hierro del suelo."

## 2. Traducci\u00f3n Sensorial
Cada dato t\u00e9cnico debe ir acompa\u00f1ado de una se\u00f1al f\u00edsica verificable (color, textura, olor, peso):
- Temperatura: rel\u00e1ciona con sensaci\u00f3n al tocar la tierra o las hojas.
- Humedad: c\u00f3mo se ve y se siente la tierra (oscura/clara, suelta/apelmazada).
- pH: efectos visibles en las hojas (amarillamiento, bordes quemados).
- UV: estado de las hojas (quemaduras, enrollamiento).

## 3. Estructura de Respuesta para Cuidados
Cuando respondas sobre diagn\u00f3sticos o tratamientos, usa este formato:

\U0001f441\ufe0f **Diagn\u00f3stico Visual:** Describe exactamente qu\u00e9 buscar (colores, texturas, patrones).

\U0001fa79 **La Receta (Paso a Paso):** Instrucciones claras y accionables.

\U0001f932 **La Prueba del Tacto (Checkpoint):** C\u00f3mo verificar f\u00edsicamente que va bien.
Ejemplo: "Toca la hoja: si se deshace entre tus dedos es hongo, si cruje como papel es falta de agua."

\U0001f9e0 **El Dato Experto:** La explicaci\u00f3n cient\u00edfica breve (NPK, pH, fitoqu\u00edmica) para quien quiera profundizar.

## 4. Seguridad Primero
- NUNCA recomiendes qu\u00edmicos agresivos sin advertir sobre guantes, mascarilla y protecci\u00f3n.
- Prioriza SIEMPRE remedios org\u00e1nicos y caseros cuando sean viables.
- Si recomiendas un producto qu\u00edmico, indica la dosis exacta y el periodo de carencia.

## 5. Datos de Sensores
- Cuando recibas datos de sensores, NO los repitas como n\u00fameros crudos.
- Interpr\u00e9talos: di qu\u00e9 significan para la planta y qu\u00e9 acci\u00f3n tomar.
- Ejemplo: En vez de "Humedad: 35%", di "Tu suelo est\u00e1 bastante seco \u2014 si tomas un pu\u00f1o de tierra y no se compacta, necesitas regar pronto."

# REGLAS ESTRICTAS
1. Si hay ALERTAS T\u00c1CTICAS, debes mencionarlas PRIMERO antes de cualquier otra informaci\u00f3n.
2. NUNCA recomiendes pesticidas qu\u00edmicos sint\u00e9ticos a menos que el usuario lo solicite expl\u00edcitamente.
3. Basa tus respuestas SIEMPRE en los datos de sensores y el contexto proporcionado.
4. Si no tienes datos suficientes, DILO CLARAMENTE en lugar de inventar informaci\u00f3n.
5. Si los datos de sensores y el an\u00e1lisis visual se contradicen, notifica la discrepancia.
6. Cita tus fuentes cuando uses informaci\u00f3n del contexto RAG.
7. Responde siempre en espa\u00f1ol mexicano.
"""


class PromptBuilder:
    """Builds structured prompts for the Mole-AI LLM.

    The prompt is assembled in a strict priority order:
    1. System Prompt (persona + rules + communication style)
    2. Tactical Alerts (CRITICAL first)
    3. Sensor Data (interpreted, not raw)
    4. RAG Context (expert knowledge)
    5. User-provided context
    6. User Query
    """

    @staticmethod
    def build_chat_prompt(
        query: str,
        context: Optional[List[str]] = None,
        rag_context: Optional[List[str]] = None,
        sensor_data: Optional[SensorData] = None,
        tactical_alerts: Optional[List[TacticalAlert]] = None,
        crop_context: Optional[str] = None,
    ) -> str:
        """Build the full prompt string ready to send to the LLM adapter.

        Returns:
            A single string with all sections concatenated.
        """
        sections: List[str] = [MOLE_AI_SYSTEM_PROMPT]

        # --- Tactical Alerts (highest priority) ---
        if tactical_alerts:
            sorted_alerts = sorted(
                tactical_alerts,
                key=lambda a: {"CRITICAL": 0, "WARNING": 1, "INFO": 2}.get(a.severity, 3),
            )
            alert_lines = []
            for alert in sorted_alerts:
                alert_lines.append(
                    f"{'🚨' if alert.severity == 'CRITICAL' else '⚠️'} "
                    f"[{alert.severity}] {alert.message} — "
                    f"Acción: {alert.immediate_action} (urgencia: {alert.urgency_hours}h)"
                )
            sections.append(
                "---\n## ⚡ ALERTAS TÁCTICAS (ATENDER PRIMERO)\n" + "\n".join(alert_lines)
            )

        # --- Sensor Data (interpreted, not raw) ---
        if sensor_data:
            sensor_section = PromptBuilder._format_sensor_data(sensor_data)
            if sensor_section:
                sections.append(sensor_section)

        # --- RAG Context (expert knowledge from vector store) ---
        if rag_context:
            sections.append(
                "---\n## 📚 BASE DE CONOCIMIENTOS (RAG)\n"
                + "\n".join(f"• {ctx}" for ctx in rag_context)
            )

        # --- User-provided context ---
        if context:
            sections.append(
                "---\n## CONTEXTO ADICIONAL\n"
                + "\n".join(f"• {ctx}" for ctx in context)
            )

        # --- Crop-specific info ---
        if crop_context:
            sections.append(f"---\n## 🌱 CULTIVO DETECTADO\n{crop_context}")

        # --- User Query ---
        sections.append(
            f"---\n## 💬 CONSULTA DEL USUARIO\n{query}\n\n"
            "Recuerda: responde usando analogías sensoriales, no como libro de texto. "
            "Sé práctico, directo y cálido."
        )

        return "\n\n".join(sections)

    @staticmethod
    def _format_sensor_data(sensor_data: SensorData) -> Optional[str]:
        """Format sensor readings with sensory interpretations."""
        parts: List[str] = []

        if sensor_data.humidity is not None:
            h = sensor_data.humidity
            if h < 30:
                interp = "Ambiente muy seco — las hojas pueden deshidratarse rápido."
            elif h < 50:
                interp = "Humedad moderada — aceptable para la mayoría de cultivos."
            elif h < 70:
                interp = "Buena humedad ambiental — condiciones favorables."
            else:
                interp = "Muy húmedo — cuidado con hongos, revisa ventilación."
            parts.append(f"- 💧 Humedad ambiental: {h:.1f}% → {interp}")

        if sensor_data.soil_humidity is not None:
            sh = sensor_data.soil_humidity
            if sh < 25:
                interp = "Suelo seco — si tomas un puño de tierra y no se compacta, riega ya."
            elif sh < 45:
                interp = "Humedad baja — la tierra se siente tibia y suelta, necesita agua pronto."
            elif sh < 65:
                interp = "Buen nivel — la tierra debe sentirse fresca y oscura, como esponja exprimida."
            else:
                interp = "Suelo muy húmedo — si aprietas la tierra y escurre agua, deja de regar."
            parts.append(f"- 🌍 Humedad del suelo: {sh:.1f}% → {interp}")

        if sensor_data.temperature is not None:
            t = sensor_data.temperature
            if t < 10:
                interp = "Frío — riesgo de heladas, protege las plantas con acolchado o manta."
            elif t < 20:
                interp = "Fresco — bueno para hortalizas de clima templado."
            elif t < 30:
                interp = "Cálido — rango ideal para la mayoría de cultivos tropicales."
            elif t < 38:
                interp = "Caliente — riega temprano y al atardecer, las hojas pueden quemarse al mediodía."
            else:
                interp = "Estrés térmico severo — sombra urgente y riego abundante."
            parts.append(f"- 🌡️ Temperatura: {t:.1f}°C → {interp}")

        if sensor_data.ph_level is not None:
            ph = sensor_data.ph_level
            if ph < 5.5:
                interp = "Suelo ácido — las hojas pueden ponerse amarillas por falta de nutrientes. Considera cal agrícola."
            elif ph < 6.5:
                interp = "Ligeramente ácido — ideal para la mayoría de cultivos (tomate, maíz, frijol)."
            elif ph < 7.5:
                interp = "Neutro — excelente disponibilidad de nutrientes."
            else:
                interp = "Suelo alcalino — puede bloquear hierro y zinc, hojas con nervaduras verdes y lámina amarilla."
            parts.append(f"- ⚗️ pH del suelo: {ph:.1f} → {interp}")

        if sensor_data.uv_index is not None:
            uv = sensor_data.uv_index
            if uv < 3:
                interp = "UV bajo — poca luz, considera si tu planta necesita más sol."
            elif uv < 6:
                interp = "UV moderado — buenas condiciones de luz para la mayoría de cultivos."
            elif uv < 8:
                interp = "UV alto — revisa que las hojas no se enrollen ni presenten manchas blancas."
            else:
                interp = "UV extremo — las hojas pueden quemarse, usa malla sombra si es posible."
            parts.append(f"- ☀️ Índice UV: {uv:.1f} mW/cm² → {interp}")

        if not parts:
            return None

        return (
            "---\n## 📊 LECTURA DE SENSORES (en tiempo real)\n"
            "Interpreta estos datos para el usuario con analogías sensoriales:\n"
            + "\n".join(parts)
        )
