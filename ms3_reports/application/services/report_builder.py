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
            <footer>Disclaimer COFEPRIS</footer>
            </body>
            </html>
            """
        )

        # fake trend for placeholder
        x = list(range(10))
        y = [i * 1.1 for i in x]
        trends_img = self.build_trend_image(x, y)

        return template.render(trends_img=trends_img, insights=insights, logs=logs)
