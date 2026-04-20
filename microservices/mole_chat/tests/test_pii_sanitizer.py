import pytest
from app.core.pii_sanitizer import PIISanitizer

def test_sanitize_emails():
    texto_original = "Hola, mi correo es agricultor.juan@gmail.com, ¿qué plaga es esta?"
    texto_limpio = PIISanitizer.sanitize(texto_original)
    
    assert "agricultor.juan@gmail.com" not in texto_limpio
    assert "[EMAIL_OCULTO]" in texto_limpio

def test_sanitize_phones():
    textos_con_telefonos = [
        "Llamame al 55-1234-5678 por favor.",
        "Mi cel es +52 55 9876 5432.",
        "Contacto: 5512345678"
    ]
    
    for texto in textos_con_telefonos:
        texto_limpio = PIISanitizer.sanitize(texto)
        assert "[TEL_OCULTO]" in texto_limpio
        # Asegura que no queden rastros del número (más de 9 dígitos seguidos)
        assert not any(char.isdigit() for char in texto_limpio if texto_limpio.count(char) > 5)

def test_hash_user_id():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    hashed = PIISanitizer.hash_user_id(user_id)
    
    assert hashed != user_id
    assert len(hashed) == 64  # SHA-256 length
    assert PIISanitizer.hash_user_id(None) == "anonymous"