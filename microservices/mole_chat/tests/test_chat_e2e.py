import os
import sys
import json
import httpx
import jwt
from dotenv import load_dotenv

# 1. Intentamos cargar el .env maestro si existe (por si lo corres fuera de Docker)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
if os.path.exists(env_path):
    load_dotenv(env_path)

# Variables de entorno requeridas
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY")  
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "tu_correo@ejemplo.com") 
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "tu_password123")  

# 🛡️ GUARDIA DE SEGURIDAD: Verificar que las variables existan antes de llamar a la API
missing_vars = []
if not SUPABASE_URL: missing_vars.append("SUPABASE_URL")
if not SUPABASE_ANON_KEY: missing_vars.append("SUPABASE_ANON_KEY")
if not TEST_EMAIL: missing_vars.append("TEST_USER_EMAIL")
if not TEST_PASSWORD: missing_vars.append("TEST_USER_PASSWORD")

if missing_vars:
    print(f"\n❌ ERROR FATAL: Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")
    print("Asegúrate de agregarlas a tu archivo .env maestro ubicado en la raíz de Mole-AI.\n")
    sys.exit(1)

API_URL = "http://localhost:8002/api/v1/mole-ai/chat"

def run_test():
    print(f"\n🚀 1. Iniciando Autenticación en: {SUPABASE_URL}")
    
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
        auth_resp = client.post(auth_url, headers=headers, json=payload)
        
        if auth_resp.status_code != 200:
            print(f"❌ Error de autenticación: {auth_resp.text}")
            return
            
        token_data = auth_resp.json()
        access_token = token_data.get("access_token")
        print("✅ Token obtenido exitosamente.")
        
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
        user_id = decoded_token.get("sub")
        print(f"🔍 Identidad detectada (UUID): {user_id}")
        
        print("\n🔄 2. Consultando al Agente Agrónomo (LLM)...")
        chat_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        chat_payload = {
            "user_id": user_id,
            "message": "Mis plantas de tomate tienen manchas negras con un halo amarillo y las hojas se caen. Mi correo es agricultor@finca.com, ¿puedes ayudarme?"
        }
        
        chat_resp = client.post(API_URL, headers=chat_headers, json=chat_payload, timeout=60.0)
        
        if chat_resp.status_code == 200:
            print("✅ ÉXITO: Respuesta generada.\n")
            print(json.dumps(chat_resp.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error en la API de Chat (HTTP {chat_resp.status_code}): {chat_resp.text}")

if __name__ == "__main__":
    run_test()