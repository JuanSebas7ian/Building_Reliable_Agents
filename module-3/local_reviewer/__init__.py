"""
Local Trace Reviewer Package
============================
Plataforma local de evaluación y observabilidad de trazas para agentes (Módulo 3).
"""

from .trace_reviewer import (
    LocalTrace,
    LocalTraceEvaluator,
    LocalTraceReviewer,
    AUTHORIZED_DEPARTMENTS
)

__all__ = [
    "LocalTrace",
    "LocalTraceEvaluator",
    "LocalTraceReviewer",
    "AUTHORIZED_DEPARTMENTS"
]
