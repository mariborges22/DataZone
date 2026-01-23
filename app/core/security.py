"""
Módulo de Segurança - DataZone Energy
Implementa criptografia, sanitização e proteção contra ataques
"""

import base64
import os
import re
from typing import Any, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


class SecurityManager:
    """Gerenciador de segurança da aplicação"""

    def __init__(self):
        """Inicializa o gerenciador de segurança"""
        self._fernet = None
        self._init_encryption()

    def _init_encryption(self):
        """Inicializa sistema de criptografia"""
        # Derivar chave de criptografia a partir da SECRET_KEY
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"datazone_energy_salt",  # Em produção, usar salt único e seguro
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        self._fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """
        Criptografa dados sensíveis

        Args:
            data: Dados a criptografar

        Returns:
            Dados criptografados em base64
        """
        if not data:
            return data

        encrypted = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Descriptografa dados

        Args:
            encrypted_data: Dados criptografados

        Returns:
            Dados originais
        """
        if not encrypted_data:
            return encrypted_data

        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # Se falhar, retornar vazio (não expor erro)
            return ""

    @staticmethod
    def sanitize_sql_input(value: Any) -> Any:
        """
        Sanitiza entrada para prevenir SQL Injection
        NOTA: SQLAlchemy já protege contra SQL injection quando usado corretamente
        Esta é uma camada adicional de segurança

        Args:
            value: Valor a sanitizar

        Returns:
            Valor sanitizado
        """
        if value is None:
            return None

        if isinstance(value, str):
            # Remover caracteres perigosos
            dangerous_chars = [";", "--", "/*", "*/", "xp_", "sp_", "EXEC", "EXECUTE"]
            sanitized = value

            for char in dangerous_chars:
                sanitized = sanitized.replace(char, "")

            # Limitar tamanho
            return sanitized[:1000]  # Máximo 1000 caracteres

        return value

    @staticmethod
    def sanitize_geojson_output(geojson: dict) -> dict:
        """
        Remove informações sensíveis do GeoJSON antes de enviar ao frontend

        Args:
            geojson: GeoJSON a sanitizar

        Returns:
            GeoJSON sanitizado
        """
        # Campos sensíveis que nunca devem ser expostos
        sensitive_fields = [
            "password",
            "senha",
            "token",
            "secret",
            "api_key",
            "created_at",
            "updated_at",
            "data_source",  # Metadados internos
        ]

        if "features" in geojson:
            for feature in geojson["features"]:
                if "properties" in feature:
                    # Remover campos sensíveis
                    for field in sensitive_fields:
                        feature["properties"].pop(field, None)

                    # Limitar precisão de coordenadas (anti-tracking)
                    if "geometry" in feature and "coordinates" in feature["geometry"]:
                        coords = feature["geometry"]["coordinates"]
                        feature["geometry"]["coordinates"] = round_coordinates(coords)

        return geojson

    @staticmethod
    def validate_bbox(bbox_str: str) -> bool:
        """
        Valida formato de bounding box para prevenir ataques

        Args:
            bbox_str: String de bbox (min_lon,min_lat,max_lon,max_lat)

        Returns:
            True se válido, False caso contrário
        """
        if not bbox_str:
            return False

        try:
            parts = bbox_str.split(",")
            if len(parts) != 4:
                return False

            coords = [float(p) for p in parts]
            min_lon, min_lat, max_lon, max_lat = coords

            # Validar ranges
            if not (-180 <= min_lon <= 180):
                return False
            if not (-90 <= min_lat <= 90):
                return False
            if not (-180 <= max_lon <= 180):
                return False
            if not (-90 <= max_lat <= 90):
                return False

            # Validar lógica
            if min_lon >= max_lon or min_lat >= max_lat:
                return False

            # Validar tamanho máximo (prevenir queries muito grandes)
            if (max_lon - min_lon) > 10 or (max_lat - min_lat) > 10:
                return False  # Máximo 10 graus

            return True

        except (ValueError, TypeError):
            return False

    @staticmethod
    def mask_sensitive_data(data: str, show_chars: int = 4) -> str:
        """
        Mascara dados sensíveis para logs

        Args:
            data: Dados a mascarar
            show_chars: Quantos caracteres mostrar no início/fim

        Returns:
            Dados mascarados
        """
        if not data or len(data) <= show_chars * 2:
            return "***"

        return f"{data[:show_chars]}...{data[-show_chars:]}"


def round_coordinates(coords: Any, precision: int = 6) -> Any:
    """
    Arredonda coordenadas para limitar precisão

    Args:
        coords: Coordenadas (pode ser lista aninhada)
        precision: Casas decimais

    Returns:
        Coordenadas arredondadas
    """
    if isinstance(coords, list):
        return [round_coordinates(c, precision) for c in coords]
    elif isinstance(coords, (int, float)):
        return round(coords, precision)
    return coords


# Instância global
security = SecurityManager()


# Decorador para sanitizar inputs
def sanitize_inputs(func):
    """Decorador para sanitizar inputs de funções"""

    def wrapper(*args, **kwargs):
        # Sanitizar kwargs
        sanitized_kwargs = {k: security.sanitize_sql_input(v) for k, v in kwargs.items()}
        return func(*args, **sanitized_kwargs)

    return wrapper
