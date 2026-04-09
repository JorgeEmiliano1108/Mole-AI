import re

file_path = 'apps/core/views.py'
with open(file_path, 'r') as f:
    content = f.read()

# Parche para sensor_data_view
security_patch_single = """    v_data = cast(Dict[str, Any], serializer.validated_data)
    
    # [RF-IOTSEC-001] Protección Anti-Replay (ETSI EN 303 645)
    recorded_at = v_data.get('recorded_at')
    if recorded_at:
        delta_seconds = abs((timezone.now() - recorded_at).total_seconds())
        if delta_seconds > 300:
            logger.warning(f"Bloqueo Anti-Replay: Delta de {delta_seconds}s detectado en ESP32.")
            return Response({"error": "Replay attack protection: Timestamp out of sync (> 300s)"}, status=403)
"""
content = re.sub(r"    v_data = cast\(Dict\[str, Any\], serializer\.validated_data\)", security_patch_single, content, count=1)

# Parche para sensor_batch_view
security_patch_batch = """    batch = cast(List[Dict[str, Any]], v_data['batch'])
    
    # [RF-IOTSEC-001] Protección Anti-Replay para Lotes
    if batch and 'recorded_at' in batch[0]:
        delta_seconds = abs((timezone.now() - batch[0]['recorded_at']).total_seconds())
        if delta_seconds > 300:
            logger.warning(f"Bloqueo Anti-Replay en Lote: Delta de {delta_seconds}s detectado.")
            return Response({"error": "Replay attack protection in batch: Timestamp out of sync (> 300s)"}, status=403)
"""
content = re.sub(r"    batch = cast\(List\[Dict\[str, Any\]\], v_data\['batch'\]\)", security_patch_batch, content, count=1)

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Parche Anti-Replay inyectado correctamente en apps/core/views.py")
