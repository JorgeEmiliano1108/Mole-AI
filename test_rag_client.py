#!/usr/bin/env python3
"""
Test client para RAG Service con Control de Acceso
"""

import httpx
import json
import asyncio
from typing import Optional


class RAGTestClient:
    def __init__(self, base_url: str = "http://localhost:8002"):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.base_url = base_url
        self.admin_key = os.getenv("ADMIN_API_KEY", "admin_key_12345")
        self.farmer_key = os.getenv("FARMER_API_KEY", "farmer_key_67890")
    
    async def test_admin_ask(self):
        """Prueba: ADMIN pregunta al RAG"""
        print("\n" + "="*60)
        print("TEST 1: ADMIN pregunta al RAG")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rag/ask",
                    params={"question": "¿Qué es tizón tardío?"},
                    headers={"X-API-Key": self.admin_key}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Respuesta exitosa")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Error: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def test_farmer_ask(self):
        """Prueba: AGRICULTOR pregunta al RAG"""
        print("\n" + "="*60)
        print("TEST 2: AGRICULTOR pregunta al RAG")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rag/ask",
                    params={"question": "¿Cómo prevenir enfermedades?"},
                    headers={"X-API-Key": self.farmer_key}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Respuesta exitosa")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Error: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def test_farmer_upload_denied(self):
        """Prueba: AGRICULTOR intenta subir PDF (debe ser denegado)"""
        print("\n" + "="*60)
        print("TEST 3: AGRICULTOR intenta subir PDF (DEBE SER DENEGADO)")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rag/admin/upload-pdf",
                    headers={"X-API-Key": self.farmer_key}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 403:
                    print(f"✅ ACCESO DENEGADO (esperado)")
                    print(f"Mensaje: {response.json()['detail']}")
                else:
                    print(f"❌ Error: debería ser 403, recibido {response.status_code}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def test_admin_upload(self):
        """Prueba: ADMIN sube PDF"""
        print("\n" + "="*60)
        print("TEST 4: ADMIN sube PDF")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rag/admin/upload-pdf",
                    headers={"X-API-Key": self.admin_key}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ PDF subido exitosamente")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Error: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def test_admin_ingest_public(self):
        """Prueba: ADMIN ingesta desde repositorios públicos"""
        print("\n" + "="*60)
        print("TEST 5: ADMIN ingesta desde repositorios públicos")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rag/admin/ingest-public",
                    headers={"X-API-Key": self.admin_key}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Ingesta exitosa desde repositorios")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Error: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def test_admin_sources(self):
        """Prueba: ADMIN ve todas las fuentes"""
        print("\n" + "="*60)
        print("TEST 6: ADMIN ve todas las fuentes")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/rag/admin/sources",
                    headers={"X-API-Key": self.admin_key}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Fuentes recuperadas")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Error: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def test_no_auth(self):
        """Prueba: Sin autenticación (debe ser denegado)"""
        print("\n" + "="*60)
        print("TEST 7: Sin autenticación (DEBE SER DENEGADO)")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rag/ask",
                    params={"question": "test"}
                )
                
                print(f"Status: {response.status_code}")
                if response.status_code in [401, 403]:
                    print(f"✅ ACCESO DENEGADO (esperado)")
                    print(f"Mensaje: {response.json()['detail']}")
                else:
                    print(f"❌ Error: debería ser 401/403, recibido {response.status_code}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def test_health(self):
        """Prueba: Health check"""
        print("\n" + "="*60)
        print("TEST 8: Health check (sin autenticación)")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/rag/health")
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Servicio healthy")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Error: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
    
    async def run_all_tests(self):
        """Ejecuta todos los tests"""
        print("\n\n")
        print("╔" + "="*58 + "╗")
        print("║" + " " * 10 + "RAG SERVICE - TEST SUITE")  + " " * 24 + "║")
        print("║" + " " * 10 + "Control de Acceso por Roles" + " " * 21 + "║")
        print("╚" + "="*58 + "╝")
        
        await self.test_health()
        await self.test_admin_ask()
        await self.test_farmer_ask()
        await self.test_farmer_upload_denied()
        await self.test_admin_upload()
        await self.test_admin_ingest_public()
        await self.test_admin_sources()
        await self.test_no_auth()
        
        print("\n\n")
        print("╔" + "="*58 + "╗")
        print("║" + " " * 18 + "TESTS COMPLETADOS" + " " * 23 + "║")
        print("╚" + "="*58 + "╝")
        print("\nCredenciales:")
        print(f"  ADMIN:      X-API-Key: {self.admin_key}")
        print(f"  AGRICULTOR: X-API-Key: {self.farmer_key}")


async def main():
    client = RAGTestClient()
    await client.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
