import io
import base64
import matplotlib.pyplot as plt
import gc
from datetime import datetime
from jinja2 import Template

class ReportBuilder:
    def build_trend_image(self, x, y):
        # Estilo de Mole.AI para la gráfica
        fig, ax = plt.subplots(figsize=(7, 3.5))
        try:
            # Fondo limpio, línea verde gruesa y estilo moderno
            fig.patch.set_facecolor('#ffffff')
            ax.set_facecolor('#f8f9fa')
            ax.plot(x, y, color="#27ae60", linewidth=3, marker='o', markersize=5)
            
            ax.set_title("Evolución de Sensores (Últimos 90 días)", fontsize=12, fontweight='bold', color="#2c3e50")
            ax.grid(True, linestyle='--', alpha=0.6, color="#bdc3c7")
            
            # Quitar los bordes de arriba y la derecha
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#7f8c8d')
            ax.spines['left'].set_color('#7f8c8d')
            ax.tick_params(colors='#7f8c8d')

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=150) # Mayor DPI para nitidez
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        finally:
            try:
                plt.close(fig)
                del fig, ax
                gc.collect()
            except Exception:
                pass
        return img_b64

    def build_report_html(self, logs, insights):
        # Plantilla HTML con CSS inyectado para WeasyPrint
        template = Template(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <title>Reporte Agronómico - Mole.AI</title>
                <style>
                    @page {
                        size: A4;
                        margin: 2cm;
                        @bottom-right {
                            content: "Página " counter(page) " de " counter(pages);
                            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                            font-size: 9pt;
                            color: #7f8c8d;
                        }
                    }
                    body {
                        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        color: #333333;
                        line-height: 1.6;
                        margin: 0;
                    }
                    .header {
                        border-bottom: 3px solid #27ae60;
                        padding-bottom: 10px;
                        margin-bottom: 30px;
                        display: flex;
                        justify-content: space-between;
                    }
                    .header h1 {
                        color: #2c3e50;
                        margin: 0;
                        font-size: 28px;
                    }
                    .header .date {
                        color: #7f8c8d;
                        font-size: 12px;
                        text-align: right;
                    }
                    h2 {
                        color: #27ae60;
                        font-size: 20px;
                        margin-top: 30px;
                        border-bottom: 1px solid #ecf0f1;
                        padding-bottom: 5px;
                    }
                    .summary-box {
                        background-color: #f8f9fa;
                        border-left: 5px solid #3498db;
                        padding: 15px 20px;
                        margin-bottom: 25px;
                        border-radius: 4px;
                    }
                    .insights-box {
                        background-color: #eafaf1;
                        border: 1px solid #d5f5e3;
                        padding: 15px 20px;
                        border-radius: 4px;
                    }
                    .chart-container {
                        text-align: center;
                        margin: 25px 0;
                    }
                    .chart-container img {
                        max-width: 100%;
                        border: 1px solid #ecf0f1;
                        border-radius: 4px;
                        padding: 10px;
                    }
                    .footer {
                        border-top: 1px solid #bdc3c7;
                        margin-top: 50px;
                        padding-top: 15px;
                        font-size: 9px;
                        color: #7f8c8d;
                        text-align: justify;
                        line-height: 1.4;
                    }
                    .footer strong {
                        color: #2c3e50;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Mole.AI <span style="font-weight: 300; color: #7f8c8d;">| Reporte Analítico</span></h1>
                    <div class="date">Generado el: {{ date }}<br>ID: {{ ref_id }}</div>
                </div>

                <h2>Resumen Ejecutivo</h2>
                <div class="summary-box">
                    <p style="margin: 0;">{{ insights.summary }}</p>
                </div>

                <h2>Análisis de Tendencias</h2>
                <div class="chart-container">
                    {% if trends_img %}
                    <img src="data:image/png;base64,{{ trends_img }}" alt="Gráfica de Tendencias" />
                    {% else %}
                    <p>No hay suficientes datos para generar la gráfica.</p>
                    {% endif %}
                </div>

                <h2>Recomendaciones (IA Agronómica)</h2>
                <div class="insights-box">
                    <p style="margin: 0;">{{ insights.text }}</p>
                </div>

                <div class="footer">
                    <strong>AVISO LEGAL — COFEPRIS:</strong> La información contenida en este reporte es de carácter
                    estrictamente informativo y no constituye una recomendación profesional, receta agronómica ni
                    prescripción de uso de plaguicidas o agroquímicos. Cualquier aplicación de productos
                    fitosanitarios debe realizarse bajo la supervisión de un profesional certificado y conforme a
                    las disposiciones de la Comisión Federal para la Protección contra Riesgos Sanitarios (COFEPRIS),
                    la Ley General de Salud, el Reglamento en Materia de Registros, Autorizaciones de Importación y
                    Exportación y Certificados de Exportación de Plaguicidas, Nutrientes Vegetales y Sustancias y
                    Materiales Tóxicos o Peligrosos, y demás normativa aplicable. Mole.AI no se hace responsable
                    por el uso indebido de la información aquí presentada.
                </div>
            </body>
            </html>
            """
        )

        # fake trend for placeholder (se mantiene para la prueba mock)
        x = list(range(10))
        y = [i * 1.1 for i in x]
        trends_img = self.build_trend_image(x, y)
        
        # Obtenemos la fecha actual para el reporte
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")

        return template.render(
            trends_img=trends_img, 
            insights=insights, 
            logs=logs,
            date=current_date,
            ref_id="M-AI-2026"
        )