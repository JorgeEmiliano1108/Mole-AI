#!/usr/bin/env python3
"""
Validador de arquitectura hexagonal Mole AI v2.0
Valida la implementación completa sin dependencias externas
"""

import sys
import os
import asyncio
import json
import base64
import io
from datetime import datetime
from PIL import Image

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class MockValidator:
    """Validador usando mocks para no depender de bibliotecas externas"""
    
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Registra resultado de test"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"     {message}")
    
    def validate_domain_models(self):
        """Valida modelos del dominio"""
        try:
            # Importar y validar modelos
            from mole_ai.domain.models.plant import (
                PlantDiagnosis, 
                SensorData, 
                PlantImage, 
                PlantState
            )
            
            # Test de datos de sensores
            sensor_data = SensorData(
                ph=6.2,
                humedad=75.0,
                temp=25.5,
                uv=0.8
            )
            assert sensor_data.ph == 6.2
            assert sensor_data.humedad == 75.0
            
            # Test de imagen
            image = PlantImage(
                image_base64="dGVzdA==",  # "test" en base64
                filename="test.jpg"
            )
            assert image.filename == "test.jpg"
            
            # Test de diagnóstico
            diagnosis = PlantDiagnosis(
                estado=PlantState.ATENCION,
                confianza=0.85,
                diagnostico="Diagnóstico de prueba",
                sensores=sensor_data,
                imagen=image,
                modelo_utilizado="Phi-3.5 Vision-Instruct Q4"
            )
            assert diagnosis.es_confiable == True
            assert diagnosis.nivel_riesgo == "MEDIO"
            
            self.log_test("Domain Models", True, "Modelos del dominio validados")
            return True
            
        except Exception as e:
            self.log_test("Domain Models", False, f"Error: {str(e)}")
            return False
    
    def validate_ports_exist(self):
        """Valida que los puertos existan"""
        try:
            # Verificar que el archivo de puertos exista
            ports_file = 'mole_ai/domain/ports/__init__.py'
            if os.path.exists(ports_file):
                with open(ports_file, 'r') as f:
                    content = f.read()
                
                # Verificar puertos clave
                required_ports = [
                    'VisionProviderPort',
                    'KnowledgeRetrievalPort',
                    'SensorDataPort',
                    'DiagnosticPersistencePort',
                    'ModelManagementPort'
                ]
                
                missing_ports = []
                for port in required_ports:
                    if port not in content:
                        missing_ports.append(port)
                
                if missing_ports:
                    self.log_test("Ports Interface", False, f"Missing ports: {missing_ports}")
                    return False
                else:
                    self.log_test("Ports Interface", True, "Puertos hexagonales definidos correctamente")
                    return True
            else:
                self.log_test("Ports Interface", False, "Ports file not found")
                return False
                
        except Exception as e:
            self.log_test("Ports Interface", False, f"Error: {str(e)}")
            return False
    
    def validate_use_cases(self):
        """Valida casos de uso"""
        try:
            # Verificar que el archivo de casos de uso exista
            use_cases_file = 'mole_ai/use_cases/unified_diagnostic.py'
            if os.path.exists(use_cases_file):
                with open(use_cases_file, 'r') as f:
                    content = f.read()
                
                # Verificar clase y métodos clave
                required_components = [
                    'class UnifiedDiagnosticUseCase',
                    'def execute_complete_diagnosis',
                    'def execute_vision_only_diagnosis',
                    'VisionProviderPort',
                    'KnowledgeRetrievalPort'
                ]
                
                missing_components = []
                for component in required_components:
                    if component not in content:
                        missing_components.append(component)
                
                if missing_components:
                    self.log_test("Use Cases", False, f"Missing: {missing_components}")
                    return False
                else:
                    self.log_test("Use Cases", True, "Casos de uso hexagonales implementados")
                    return True
            else:
                self.log_test("Use Cases", False, "Use cases file not found")
                return False
                
        except Exception as e:
            self.log_test("Use Cases", False, f"Error: {str(e)}")
            return False
    
    def validate_adapters_structure(self):
        """Valida estructura de adaptadores"""
        try:
            # Verificar archivos de adaptadores
            adapter_files = [
                'mole_ai/adapters/outbound/phi3_vision_adapter.py',
                'mole_ai/adapters/outbound/unified_rag_adapter.py',
                'mole_ai/adapters/outbound/postgresql_adapter.py'
            ]
            
            for adapter_file in adapter_files:
                if os.path.exists(adapter_file):
                    self.log_test(f"Adapter: {adapter_file.split('/')[-1]}", True)
                else:
                    self.log_test(f"Adapter: {adapter_file.split('/')[-1]}", False)
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("Adapters Structure", False, f"Error: {str(e)}")
            return False
    
    def validate_api_structure(self):
        """Valida estructura de API FastAPI"""
        try:
            # Verificar archivo main
            main_file = 'mole_ai/main.py'
            if os.path.exists(main_file):
                with open(main_file, 'r') as f:
                    content = f.read()
                
                # Verificar componentes clave
                required_components = [
                    'FastAPI',
                    'UnifiedDiagnosticUseCase',
                    'Phi3VisionAdapter',
                    'UnifiedRAGAdapter',
                    'PostgreSQLAdapter',
                    '@asynccontextmanager',
                    'Depends'
                ]
                
                missing_components = []
                for component in required_components:
                    if component not in content:
                        missing_components.append(component)
                
                if missing_components:
                    self.log_test("API Structure", False, f"Missing: {missing_components}")
                    return False
                else:
                    self.log_test("API Structure", True, "API FastAPI con inyección de dependencias")
                    return True
            else:
                self.log_test("API Structure", False, "Main file not found")
                return False
                
        except Exception as e:
            self.log_test("API Structure", False, f"Error: {str(e)}")
            return False
    
    def validate_docker_configuration(self):
        """Valida configuración Docker"""
        try:
            # Verificar Dockerfile principal (ahora es el hexagonal)
            dockerfile = 'Dockerfile'
            if os.path.exists(dockerfile):
                with open(dockerfile, 'r') as f:
                    content = f.read()
                
                required_components = [
                    'python:3.12-slim',
                    'mole_ai/',
                    'Phi-3.5',
                    'requirements.txt'
                ]
                
                missing_components = []
                for component in required_components:
                    if component not in content:
                        missing_components.append(component)
                
                if missing_components:
                    self.log_test("Dockerfile", False, f"Missing: {missing_components}")
                else:
                    self.log_test("Dockerfile", True, "Dockerfile optimizado")
            else:
                self.log_test("Dockerfile", False, "Dockerfile hexagonal not found")
            
            # Verificar docker-compose
            compose_file = 'docker-compose.yml'
            if os.path.exists(compose_file):
                with open(compose_file, 'r') as f:
                    content = f.read()
                
                required_components = [
                    'postgres:',
                    'mole-ai-api:',
                    'Dockerfile',
                    '172.21.0.0/16'  # Red hexagonal dedicada
                ]
                
                missing_components = []
                for component in required_components:
                    if component not in content:
                        missing_components.append(component)
                
                if missing_components:
                    self.log_test("Docker Compose", False, f"Missing: {missing_components}")
                else:
                    self.log_test("Docker Compose", True, "Docker Compose hexagonal")
            else:
                self.log_test("Docker Compose", False, "Docker Compose hexagonal not found")
                
            return True
            
        except Exception as e:
            self.log_test("Docker Configuration", False, f"Error: {str(e)}")
            return False
    
    def validate_legacy_removal(self):
        """Valida que servicios legacy han sido eliminados"""
        try:
            # Verificar que los servicios legacy hayan sido eliminados
            legacy_services = [
                'app-legacy',
                'backend_core-legacy', 
                'ai_rag_service-legacy',
                'ai_vision_service-legacy',
                'infrastructure-legacy'
            ]
            
            for service in legacy_services:
                if not os.path.exists(service):
                    self.log_test(f"Legacy: {service}", True, f"Legacy service eliminated correctly")
                else:
                    self.log_test(f"Legacy: {service}", False, f"Legacy service still exists")
            
            # Verificar que no haya servicios activos legacy en root
            active_services = ['app', 'backend_core', 'ai_rag_service', 'ai_vision_service']
            legacy_found = []
            
            for service in active_services:
                if os.path.exists(service):
                    legacy_found.append(service)
            
            if legacy_found:
                self.log_test("Legacy Removal", False, f"Legacy still active: {legacy_found}")
                return False
            else:
                self.log_test("Legacy Removal", True, "All legacy services eliminated")
                return True
                
        except Exception as e:
            self.log_test("Legacy Removal", False, f"Error: {str(e)}")
            return False
    
    def validate_requirements_file(self):
        """Valida archivo de requisitos principal"""
        try:
            requirements_file = 'requirements.txt'
            if os.path.exists(requirements_file):
                with open(requirements_file, 'r') as f:
                    content = f.read()
                
                required_packages = [
                    'fastapi',
                    'torch',
                    'transformers',
                    'langchain',
                    'psycopg2-binary',
                    'chromadb',
                    'faiss-cpu'
                ]
                
                missing_packages = []
                for package in required_packages:
                    if package not in content:
                        missing_packages.append(package)
                
                if missing_packages:
                    self.log_test("Requirements", False, f"Missing packages: {missing_packages}")
                    return False
                else:
                    self.log_test("Requirements", True, "Requirements principales completos")
                    return True
            else:
                self.log_test("Requirements", False, "Requirements principales not found")
                return False
                
        except Exception as e:
            self.log_test("Requirements", False, f"Error: {str(e)}")
            return False
    
    def generate_report(self):
        """Genera reporte final de validación"""
        print("\n" + "="*80)
        print("📋 REPORTE DE VALIDACIÓN - ARQUITECTURA HEXAGONAL MOLE AI v2.0")
        print("="*80)
        
        passed = sum(1 for test in self.test_results if "PASS" in test["status"])
        total = len(self.test_results)
        
        print(f"\n📊 RESUMEN: {passed}/{total} tests exitosos ({passed/total*100:.1f}%)")
        
        print("\n📝 DETALLE:")
        for test in self.test_results:
            print(f"  {test['status']}: {test['test']}")
            if test['message']:
                print(f"    → {test['message']}")
        
        if passed == total:
            print("\n🎉 ¡ARQUITECTURA HEXAGONAL VALIDADA CON ÉXITO!")
            print("✅ Sistema listo para despliegue en producción")
            return True
        else:
            print(f"\n⚠️ {total-passed} tests fallaron - Revisar problemas antes de despliegue")
            return False

def main():
    """Función principal de validación"""
    print("🔍 Iniciando validación de arquitectura hexagonal Mole AI v2.0...")
    
    validator = MockValidator()
    
    # Ejecutar todas las validaciones
    validations = [
        ("Domain Models", validator.validate_domain_models),
        ("Ports Interface", validator.validate_ports_exist),
        ("Use Cases", validator.validate_use_cases),
        ("Adapters Structure", validator.validate_adapters_structure),
        ("API Structure", validator.validate_api_structure),
        ("Docker Configuration", validator.validate_docker_configuration),
        ("Legacy Removal", validator.validate_legacy_removal),
        ("Requirements", validator.validate_requirements_file),
    ]
    
    for name, validation_func in validations:
        try:
            validation_func()
        except Exception as e:
            validator.log_test(name, False, f"Exception: {str(e)}")
    
    # Generar reporte
    return validator.generate_report()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)