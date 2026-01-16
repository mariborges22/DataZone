"""
SQLAlchemy Models para dados geográficos
"""

from app.models.fibra_optica import FibraOptica
from app.models.linha_transmissao import LinhaTransmissao
from app.models.subestacao import Subestacao

__all__ = ["Subestacao", "LinhaTransmissao", "FibraOptica"]
