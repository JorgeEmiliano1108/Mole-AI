"""Utility functions for data privacy.

Delega la pseudonimización al componente canónico `Anonymizer`
(`apps.training_data.anonymization`) para garantizar que todos los servicios
usen HMAC-SHA256 con la clave gestionada por `ANONIMIZACION_KEY`.
"""


def anonymize_id(value: str | None) -> str:
    """Retorna pseudónimo HMAC-SHA256 de *value* o 'anonymous' si es vacío.

    La importación se realiza dentro de la función para evitar cargar el
    registro de aplicaciones de Django durante la importación de utilidades.
    """
    if not value:
        return "anonymous"
    from apps.training_data.anonymization import Anonymizer

    return Anonymizer().pseudonymize(str(value))
