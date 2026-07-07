"""Manual E2E smoke test — reads credentials from env only."""

import httpx
import json
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_KEY")
TEST_EMAIL = os.environ.get("TEST_EMAIL")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD")

MOLE_VISION_API = "http://127.0.0.1:8001/api/v1/vision/analyze"
IMAGE_PATH = "/app/plnt1.webp"

def run_test():
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY, TEST_EMAIL, TEST_PASSWORD]):
        print("Missing env vars: SUPABASE_URL, SUPABASE_KEY, TEST_EMAIL, TEST_PASSWORD")
        return

    auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}

    with httpx.Client() as client:
        try:
            r = client.post(auth_url, headers=headers, json=payload)
            if r.status_code != 200:
                print(f"Auth error: {r.text}"); return
            token = r.json()["access_token"]
            print("Token obtained.")

            api_headers = {"Authorization": f"Bearer {token}"}
            with open(IMAGE_PATH, "rb") as f:
                files = {"file": ("planta.webp", f, "image/webp")}
                res = client.post(MOLE_VISION_API, headers=api_headers, files=files, timeout=60)
                if res.status_code == 200:
                    print("Success:", json.dumps(res.json(), indent=2, ensure_ascii=False))
                else:
                    print(f"Error {res.status_code}:", json.dumps(res.json(), indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Fatal: {e}")

if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print(f"Test image not found: {IMAGE_PATH}")
    else:
        run_test()
