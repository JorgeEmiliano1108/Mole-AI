import os
import sys
import httpx
from dotenv import load_dotenv

# 1. Cargar el .env maestro
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
if os.path.exists(env_path):
    load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "tu_correo@ejemplo.com") 
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "tu_password123")  

API_URL = "http://localhost:8002/api/v1/knowledge/ingest-pdf"

def run_test():
    print("🚀 1. Obteniendo token fresco de Supabase...")
    auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    
    with httpx.Client() as client:
        # A. Autenticación
        auth_resp = client.post(auth_url, headers=headers, json=payload)
        if auth_resp.status_code != 200:
            print(f"❌ Error de autenticación: {auth_resp.text}")
            return
        
        token = auth_resp.json().get("access_token")
        print("✅ Token obtenido exitosamente.\n")

        # B. Creación del PDF
        print("📄 2. Generando PDF de prueba...")
        pdf_path = "manual_tomates_test.pdf"
        try:
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(pdf_path)
            c.drawString(100, 750, "Manual de Plagas del Tomate:")
            c.drawString(100, 730, "Si la planta de tomate tiene manchas negras con un halo amarillo")
            c.drawString(100, 710, "y las hojas se caen, se trata del hongo Tizon Temprano (Alternaria solani).")
            c.drawString(100, 690, "Tratamiento: Aplicar fungicida a base de cobre y reducir la humedad.")
            c.save()
        except ImportError:
            print("❌ ERROR: Falta la librería 'reportlab' para generar el PDF.")
            print("Ejecuta esto en tu terminal primero: docker exec -it ms2_chat_standalone pip install reportlab")
            sys.exit(1)

        # C. Subida al Microservicio
        print("🧠 3. Subiendo PDF al cerebro de Mole.AI...")
        upload_headers = {"Authorization": f"Bearer {token}"}
        
        # httpx requiere abrir el archivo en modo binario para enviarlo como form-data
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            response = client.post(API_URL, headers=upload_headers, files=files, timeout=30.0)
            
            if response.status_code == 200:
                print("✅ ÉXITO: PDF Ingestado y Vectorizado.")
                print(response.text)
            else:
                print(f"❌ Falló la subida (HTTP {response.status_code}): {response.text}")

        # D. Limpieza
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    run_test()