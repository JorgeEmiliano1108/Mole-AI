import cv2
import numpy as np
import logging

logger = logging.getLogger("ms1_vision.colorimetry")

class ColorimetricPHClient:
    def __init__(self):
        # Escala universal de pH a valores RGB (Aproximación para tiras reactivas estándar)
        self.reference_colors = {
            4.0: np.array([237, 134, 44]),   # Naranja
            5.0: np.array([245, 194, 25]),   # Amarillo-naranja
            6.0: np.array([230, 222, 28]),   # Amarillo
            7.0: np.array([144, 194, 58]),   # Verde-amarillo (Neutro)
            8.0: np.array([54, 135, 84]),    # Verde
            9.0: np.array([40, 97, 107])     # Azul-verde
        }

    def estimate_ph_from_strip(self, image_bytes: bytes) -> float:
        try:
            # Decodificar imagen directamente desde los bytes de FastAPI
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Imagen corrupta o formato no soportado")

            # Convertir de BGR (defecto de OpenCV) a RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Para MVP: Recortamos el centro exacto de la imagen (20% del área)
            # asumiendo que el agricultor centró la tira reactiva en la foto.
            h, w, _ = img_rgb.shape
            center_crop = img_rgb[int(h*0.4):int(h*0.6), int(w*0.4):int(w*0.6)]
            
            # Calcular el color promedio de esa zona central
            avg_color = np.mean(center_crop, axis=(0, 1))

            # Encontrar el color más cercano usando Distancia Euclidiana
            min_dist = float('inf')
            estimated_ph = 7.0

            for ph_val, ref_color in self.reference_colors.items():
                dist = np.linalg.norm(avg_color - ref_color)
                if dist < min_dist:
                    min_dist = dist
                    estimated_ph = ph_val

            logger.info("Análisis colorimétrico exitoso. Color RGB promedio detectado: %s -> pH estimado: %s", avg_color, estimated_ph)
            return estimated_ph

        except Exception as e:
            logger.error("Fallo crítico en el motor de colorimetría: %s", e, exc_info=True)
            raise RuntimeError("No se pudo analizar la tira reactiva.")