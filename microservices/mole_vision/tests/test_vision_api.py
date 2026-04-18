import httpx
import json
import os

# ==========================================
# 1. CONFIGURACIÓN (Reemplaza con tus datos)
# ==========================================
SUPABASE_URL = "https://TU_PROYECTO.supabase.co"
SUPABASE_ANON_KEY = "TU_LLAVE_ANON_PUBLICA"

TEST_EMAIL = "tu_usuario_de_prueba@correo.com"
TEST_PASSWORD = "tu_password_seguro"

MOLE_VISION_API = "http://localhost:8001/api/v1/vision/analyze"
IMAGE_PATH = "./plnt1.webp" # Ruta a tu imagen de prueba

def run_test():
    print("🔄 1. Autenticando con Supabase...")
    
    # Endpoint nativo de GoTrue (Supabase Auth)
    auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    with httpx.Client() as client:
        auth_response = client.post(auth_url, headers=headers, json=payload)
        
        if auth_response.status_code != 200:
            print(f"❌ Error de Autenticación: {auth_response.text}")
            return
            
        auth_data = auth_response.json()
        access_token = auth_data.get("access_token")
        print("✅ Token JWT obtenido exitosamente.")
        
        print("\n🔄 2. Enviando imagen a mole_vision_standalone...")
        
        # Preparamos la petición a nuestro microservicio local
        api_headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Abrimos la imagen en modo binario
        with open(IMAGE_PATH, "rb") as image_file:
            files = {"file": ("imagen.webp", image_file, "image/webp")}
            
            api_response = client.post(MOLE_VISION_API, headers=api_headers, files=files, timeout=30.0)
            
            if api_response.status_code == 200:
                print("✅ ¡Análisis Completado Exitosamente!\n")
                print(json.dumps(api_response.json(), indent=2, ensure_ascii=False))
            else:
                print(f"❌ Error en la API Vision (Status {api_response.status_code}):")
                print(api_response.text)

if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print(f"⚠️  No se encontró la imagen en {IMAGE_PATH}")
    else:
        run_test()
        