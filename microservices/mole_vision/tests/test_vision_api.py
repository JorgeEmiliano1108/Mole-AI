import httpx
import json
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_KEY") # o SUPABASE_ANON_KEY

# Credenciales de acceso
TEST_EMAIL = "jorgee.gf27816@gmail.com"
TEST_PASSWORD = "harvest08"

# URL local dentro de la red de Docker
MOLE_VISION_API = "http://127.0.0.1:8001/api/v1/vision/analyze"
IMAGE_PATH = "/app/plnt1.webp"

def run_test():
    # Validación estricta
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("❌ Error Fatal: Docker no inyectó SUPABASE_URL o SUPABASE_KEY.")
        print("Asegúrate de haber reiniciado el contenedor con 'docker compose up -d'.")
        return

    print(f"🚀 1. Iniciando Autenticación en: {SUPABASE_URL}")
    
    auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    
    with httpx.Client() as client:
        try:
            r = client.post(auth_url, headers=headers, json=payload)
            if r.status_code != 200:
                print(f"❌ Error Auth: {r.text}"); return
            
            token = r.json()["access_token"]
            print("✅ Token obtenido exitosamente.")

            # --- FASE DE DIAGNÓSTICO (Opcional, pero útil) ---
            try:
                import jwt
                header = jwt.get_unverified_header(token)
                print(f"🔍 Algoritmo del token de Supabase: {header.get('alg')}")
            except Exception:
                pass
            # -----------------------------------------------

            print("\n🔄 2. Enviando imagen al microservicio...")
            api_headers = {"Authorization": f"Bearer {token}"}
            
            with open(IMAGE_PATH, "rb") as f:
                files = {"file": ("planta.webp", f, "image/webp")}
                res = client.post(MOLE_VISION_API, headers=api_headers, files=files, timeout=60)
                
                if res.status_code == 200:
                    print("✅ ÉXITO: Inferencia completada.\n")
                    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Error {res.status_code} en la API Vision:")
                    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
                    
        except Exception as e:
            print(f"❌ Fallo crítico en el flujo: {e}")

if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print(f"⚠️  No se encontró la imagen de prueba en {IMAGE_PATH}")
    else:
        run_test()