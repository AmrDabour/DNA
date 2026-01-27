"""
GenovaAI Async Tasks Module
============================
Contains task definitions for background processing with Celery.

CURRENT STATUS: SCAFFOLDING
---------------------------
These tasks work synchronously when Celery is disabled,
and asynchronously when Celery is enabled.

Available Task Modules:
- snp_analysis: SNP file processing and VEP annotation
- ai_predictions: Gemini AI predictions (physical traits, disease risk)
- maintenance: Cache cleanup and session management
"""

from .snp_analysis import (
    analyze_snp_file_task,
    batch_vep_annotation_task,
)

from .ai_predictions import (
    predict_physical_traits_task,
    predict_disease_risk_task,
    generate_full_report_task,
)

from .maintenance import (
    cleanup_expired_cache_task,
    cleanup_old_sessions_task,
    health_check_task,
    celery_health_check_task,
)

__all__ = [
    # SNP Analysis
    'analyze_snp_file_task',
    'batch_vep_annotation_task',
    # AI Predictions
    'predict_physical_traits_task',
    'predict_disease_risk_task',
    'generate_full_report_task',
    # Maintenance
    'cleanup_expired_cache_task',
    'cleanup_old_sessions_task',
    'health_check_task',
    'celery_health_check_task',
]


