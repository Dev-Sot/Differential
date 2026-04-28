"""
Modelos Pydantic para validar entradas y salidas de MEDI-IA.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class NivelGravedad(str, Enum):
    leve = "leve"
    moderada = "moderada"
    grave = "grave"
    emergencia = "emergencia"


class ConsultaRequest(BaseModel):
    message: str = Field(..., min_length=5, max_length=2000)


class CondicionRelacionada(BaseModel):
    nombre: str
    gravedad: NivelGravedad
    relevancia: float


class DiagnosticoResponse(BaseModel):
    success: bool = True
    respuesta: str
    condicion_principal: str
    gravedad: NivelGravedad
    gravedad_label: str
    gravedad_color: str
    gravedad_icon: str
    gravedad_descripcion: str
    recomendacion: str
    condiciones_relacionadas: list[CondicionRelacionada] = []
    urgencia: str
    confianza: float
    fuentes: list[str] = []
    modo: str = "FAISS + Reranker + Claude"
    disclaimer: str = (
        "MEDI-IA no reemplaza la consulta medica profesional. "
        "Esta es una evaluacion preliminar orientativa basada en libros medicos."
    )


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


class HealthResponse(BaseModel):
    status: str
    modo: str
    chunks_indexados: int
    claude_activo: bool
    libros: list[str] = []
