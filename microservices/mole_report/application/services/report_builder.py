import io
import base64
import gc
from datetime import datetime
from collections import defaultdict
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
except ImportError:
    # Stub classes when matplotlib is unavailable; used only in report generation, not in tests.
    class Figure:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise RuntimeError('matplotlib is required for Figure')
    class FigureCanvas:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise RuntimeError('matplotlib is required for FigureCanvas')

from jinja2 import Template

class ReportBuilder:
    def build_trend_image(self, sensor_data: dict):
        # Object-Oriented API for thread-safety (no pyplot state machine)
        fig = Figure(figsize=(7, 3.5))
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        try:
            fig.patch.set_facecolor('#ffffff')
            ax.set_facecolor('#f8f9fa')
            
            colors = ["#27ae60", "#2980b9", "#e67e22", "#8e44ad", "#e74c3c"]
            color_idx = 0
            
            for sensor, data in sensor_data.items():
                x = data["x"]
                y = data["y"]
                if not x or not y:
                    continue
                color = colors[color_idx % len(colors)]
                ax.plot(x, y, color=color, linewidth=2, marker='o', markersize=4, label=str(sensor).capitalize())
                color_idx += 1
            
            ax.set_title("Evolución de Sensores (Últimos 90 días)", fontsize=12, fontweight='bold', color="#2c3e50")
            ax.grid(True, linestyle='--', alpha=0.6, color="#bdc3c7")
            ax.legend(loc="upper right", frameon=False, fontsize=9)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#7f8c8d')
            ax.spines['left'].set_color('#7f8c8d')
            ax.tick_params(colors='#7f8c8d')
            fig.autofmt_xdate()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        finally:
            fig.clear()
            del ax, fig, canvas
            gc.collect()
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

        # Procesar logs reales agrupados por sensor con objetos datetime
        sensor_data = defaultdict(lambda: {"x": [], "y": []})
        has_data = False
        
        if logs:
            sorted_logs = sorted(logs, key=lambda r: r.get("timestamp", ""))
            
            for r in sorted_logs:
                sensor = r.get("sensor")
                timestamp_str = r.get("timestamp")
                val_str = r.get("value")
                
                if not sensor or not timestamp_str or val_str is None:
                    continue
                    
                try:
                    clean_ts = timestamp_str.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(clean_ts)
                    val = float(val_str)
                    
                    sensor_data[sensor]["x"].append(dt)
                    sensor_data[sensor]["y"].append(val)
                    has_data = True
                except (ValueError, TypeError):
                    continue

        if not has_data:
            trends_img = None
        else:
            trends_img = self.build_trend_image(dict(sensor_data))
        
        # Obtenemos la fecha actual para el reporte
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M")

        return template.render(
            trends_img=trends_img, 
            insights=insights, 
            logs=logs,
            date=current_date,
            ref_id="M-AI-2026"
        )