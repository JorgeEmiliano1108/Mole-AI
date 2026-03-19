import io
import base64
import matplotlib.pyplot as plt
import gc
from jinja2 import Template


class ReportBuilder:
    def build_trend_image(self, x, y):
        fig, ax = plt.subplots(figsize=(6, 3))
        try:
            ax.plot(x, y)
            ax.set_title("Sensor trend")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        finally:
            # Always close and release figure resources to avoid worker memory leaks
            try:
                plt.close(fig)
            except Exception:
                pass
            try:
                del fig, ax
            except Exception:
                pass
            try:
                gc.collect()
            except Exception:
                pass
        return img_b64

    def build_report_html(self, logs, insights):
        # Minimal HTML composition using Jinja2 template
        template = Template(
            """
            <html>
            <head><meta charset='utf-8'><title>Report</title></head>
            <body>
            <h1>Analytical Report</h1>
            <h2>Summary</h2>
            <p>{{ insights.summary }}</p>
            <h2>Tendencias</h2>
            {% if trends_img %}
            <img src="data:image/png;base64,{{ trends_img }}" />
            {% endif %}
            <h2>IA Insights</h2>
            <p>{{ insights.text }}</p>
            <footer style="border-top:1px solid #ccc;margin-top:20px;padding-top:10px;font-size:10px;">
            <strong>AVISO LEGAL — COFEPRIS:</strong> La información contenida en este reporte es de carácter
            estrictamente informativo y no constituye una recomendación profesional, receta agronómica ni
            prescripción de uso de plaguicidas o agroquímicos. Cualquier aplicación de productos
            fitosanitarios debe realizarse bajo la supervisión de un profesional certificado y conforme a
            las disposiciones de la Comisión Federal para la Protección contra Riesgos Sanitarios (COFEPRIS),
            la Ley General de Salud, el Reglamento en Materia de Registros, Autorizaciones de Importación y
            Exportación y Certificados de Exportación de Plaguicidas, Nutrientes Vegetales y Sustancias y
            Materiales Tóxicos o Peligrosos, y demás normativa aplicable. Mole.AI no se hace responsable
            por el uso indebido de la información aquí presentada.
            </footer>
            </body>
            </html>
            """
        )

        # fake trend for placeholder
        x = list(range(10))
        y = [i * 1.1 for i in x]
        trends_img = self.build_trend_image(x, y)

        return template.render(trends_img=trends_img, insights=insights, logs=logs)
