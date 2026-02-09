"""
Prometheus Metrics Module for GenovaAI
=======================================
Custom application metrics for monitoring DNA analysis platform performance,
prediction accuracy, file processing, database health, and task execution.

Usage:
    from utils.metrics import metrics_collector
    
    # Track a prediction
    metrics_collector.track_prediction('gender', duration=0.5, success=True)
    
    # Track a file upload
    metrics_collector.track_file_upload(file_size=1024000, file_type='csv')
"""

import functools
import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available. Metrics will be no-ops.")


# ============================================================
# Metric Definitions
# ============================================================

if PROMETHEUS_AVAILABLE:

    # --- Request Metrics ---
    REQUEST_COUNT = Counter(
        'genovaai_http_requests_total',
        'Total HTTP requests by endpoint, method, and status',
        ['endpoint', 'method', 'status_code']
    )

    REQUEST_LATENCY = Histogram(
        'genovaai_http_request_duration_seconds',
        'HTTP request latency in seconds',
        ['endpoint', 'method'],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
    )

    REQUESTS_IN_PROGRESS = Gauge(
        'genovaai_http_requests_in_progress',
        'Number of HTTP requests currently in progress',
        ['endpoint']
    )

    # --- Prediction Metrics ---
    PREDICTION_COUNT = Counter(
        'genovaai_predictions_total',
        'Total predictions made by type and outcome',
        ['prediction_type', 'status']
    )

    PREDICTION_DURATION = Histogram(
        'genovaai_prediction_duration_seconds',
        'Time taken to run predictions',
        ['prediction_type'],
        buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
    )

    PREDICTION_CONFIDENCE = Histogram(
        'genovaai_prediction_confidence',
        'Confidence scores of predictions',
        ['prediction_type'],
        buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0)
    )

    # --- File Upload Metrics ---
    FILE_UPLOAD_COUNT = Counter(
        'genovaai_file_uploads_total',
        'Total file uploads by type and status',
        ['file_type', 'status']
    )

    FILE_UPLOAD_SIZE = Histogram(
        'genovaai_file_upload_size_bytes',
        'Size of uploaded files in bytes',
        ['file_type'],
        buckets=(1024, 10240, 102400, 1048576, 10485760, 52428800, 104857600)
    )

    FILE_PROCESSING_DURATION = Histogram(
        'genovaai_file_processing_duration_seconds',
        'Time taken to process uploaded files',
        ['file_type', 'operation'],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
    )

    # --- SNP Analysis Metrics ---
    SNP_ANALYSIS_COUNT = Counter(
        'genovaai_snp_analysis_total',
        'Total SNP analyses performed',
        ['status', 'include_vep']
    )

    SNP_ANALYSIS_DURATION = Histogram(
        'genovaai_snp_analysis_duration_seconds',
        'Time taken for SNP analysis',
        ['include_vep'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
    )

    SNPS_PROCESSED = Counter(
        'genovaai_snps_processed_total',
        'Total number of individual SNPs processed'
    )

    VEP_ANNOTATION_COUNT = Counter(
        'genovaai_vep_annotations_total',
        'Total VEP annotation requests',
        ['status']
    )

    VEP_ANNOTATION_DURATION = Histogram(
        'genovaai_vep_annotation_duration_seconds',
        'Time taken for VEP annotations',
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
    )

    # --- Database Metrics ---
    DB_QUERY_COUNT = Counter(
        'genovaai_db_queries_total',
        'Total database queries by type and database',
        ['database', 'operation']
    )

    DB_QUERY_DURATION = Histogram(
        'genovaai_db_query_duration_seconds',
        'Database query duration in seconds',
        ['database', 'operation'],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 5.0)
    )

    DB_CONNECTION_POOL_SIZE = Gauge(
        'genovaai_db_connection_pool_size',
        'Current database connection pool size',
        ['database']
    )

    DB_CONNECTION_ERRORS = Counter(
        'genovaai_db_connection_errors_total',
        'Total database connection errors',
        ['database']
    )

    # --- Celery Task Metrics ---
    CELERY_TASK_COUNT = Counter(
        'genovaai_celery_tasks_total',
        'Total Celery tasks by name and status',
        ['task_name', 'status']
    )

    CELERY_TASK_DURATION = Histogram(
        'genovaai_celery_task_duration_seconds',
        'Celery task execution duration',
        ['task_name'],
        buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
    )

    CELERY_QUEUE_LENGTH = Gauge(
        'genovaai_celery_queue_length',
        'Current number of tasks in Celery queue',
        ['queue_name']
    )

    # --- AI/Gemini API Metrics ---
    AI_API_CALLS = Counter(
        'genovaai_ai_api_calls_total',
        'Total AI API calls (Gemini)',
        ['endpoint', 'status']
    )

    AI_API_DURATION = Histogram(
        'genovaai_ai_api_duration_seconds',
        'AI API call duration',
        ['endpoint'],
        buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
    )

    AI_API_TOKENS = Counter(
        'genovaai_ai_api_tokens_total',
        'Total AI API tokens consumed',
        ['direction']  # 'input' or 'output'
    )

    # --- ML Model Metrics ---
    MODEL_LOAD_DURATION = Histogram(
        'genovaai_model_load_duration_seconds',
        'Time taken to load ML models',
        ['model_type'],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
    )

    MODEL_LOADED = Gauge(
        'genovaai_model_loaded',
        'Whether an ML model is currently loaded (1=loaded, 0=not loaded)',
        ['model_type']
    )

    # --- User/Auth Metrics ---
    USER_LOGIN_COUNT = Counter(
        'genovaai_user_logins_total',
        'Total user login attempts',
        ['status']  # 'success', 'failed'
    )

    ACTIVE_USERS = Gauge(
        'genovaai_active_users',
        'Number of currently active user sessions'
    )

    USER_REGISTRATIONS = Counter(
        'genovaai_user_registrations_total',
        'Total new user registrations',
        ['status']
    )

    # --- System / Application Metrics ---
    APP_INFO = Info(
        'genovaai_application',
        'GenovaAI application information'
    )

    HEALTH_CHECK_STATUS = Gauge(
        'genovaai_health_check_status',
        'Health check status per service (1=healthy, 0=unhealthy)',
        ['service']
    )

    ERROR_COUNT = Counter(
        'genovaai_errors_total',
        'Total application errors by type',
        ['error_type', 'endpoint']
    )

    # --- PDF Report Metrics ---
    PDF_GENERATION_COUNT = Counter(
        'genovaai_pdf_reports_total',
        'Total PDF reports generated',
        ['status']
    )

    PDF_GENERATION_DURATION = Histogram(
        'genovaai_pdf_generation_duration_seconds',
        'Time taken to generate PDF reports',
        buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
    )

    # --- Agent/Chat Metrics ---
    AGENT_CONVERSATIONS = Counter(
        'genovaai_agent_conversations_total',
        'Total agent chat conversations',
        ['status']
    )

    AGENT_RESPONSE_DURATION = Histogram(
        'genovaai_agent_response_duration_seconds',
        'Time taken for agent responses',
        buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
    )

    # --- Risk Calculator Metrics ---
    RISK_CALCULATIONS = Counter(
        'genovaai_risk_calculations_total',
        'Total genetic risk calculations performed',
        ['risk_type', 'status']
    )

    RISK_CALCULATION_DURATION = Histogram(
        'genovaai_risk_calculation_duration_seconds',
        'Time taken for risk calculations',
        ['risk_type'],
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
    )


# ============================================================
# Metrics Collector Class
# ============================================================

class MetricsCollector:
    """
    Centralized metrics collector for GenovaAI.
    
    All methods are safe to call even if prometheus_client is not installed;
    they degrade gracefully to no-ops.
    """

    def __init__(self) -> None:
        self.enabled = PROMETHEUS_AVAILABLE
        if self.enabled:
            APP_INFO.info({
                'version': '1.0.0',
                'environment': 'production',
                'service': 'genovaai'
            })

    # --- Prediction Tracking ---
    def track_prediction(
        self,
        prediction_type: str,
        duration: float,
        success: bool,
        confidence: Optional[float] = None
    ) -> None:
        """Track a prediction event."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        PREDICTION_COUNT.labels(prediction_type=prediction_type, status=status).inc()
        PREDICTION_DURATION.labels(prediction_type=prediction_type).observe(duration)
        if confidence is not None:
            PREDICTION_CONFIDENCE.labels(prediction_type=prediction_type).observe(confidence)

    # --- File Upload Tracking ---
    def track_file_upload(
        self,
        file_size: int,
        file_type: str,
        success: bool = True
    ) -> None:
        """Track a file upload event."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        FILE_UPLOAD_COUNT.labels(file_type=file_type, status=status).inc()
        FILE_UPLOAD_SIZE.labels(file_type=file_type).observe(file_size)

    def track_file_processing(
        self,
        file_type: str,
        operation: str,
        duration: float
    ) -> None:
        """Track file processing time."""
        if not self.enabled:
            return
        FILE_PROCESSING_DURATION.labels(file_type=file_type, operation=operation).observe(duration)

    # --- SNP Analysis Tracking ---
    def track_snp_analysis(
        self,
        duration: float,
        success: bool,
        include_vep: bool = False,
        snp_count: int = 0
    ) -> None:
        """Track an SNP analysis event."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        vep_label = 'true' if include_vep else 'false'
        SNP_ANALYSIS_COUNT.labels(status=status, include_vep=vep_label).inc()
        SNP_ANALYSIS_DURATION.labels(include_vep=vep_label).observe(duration)
        if snp_count > 0:
            SNPS_PROCESSED.inc(snp_count)

    def track_vep_annotation(self, duration: float, success: bool) -> None:
        """Track a VEP annotation request."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        VEP_ANNOTATION_COUNT.labels(status=status).inc()
        VEP_ANNOTATION_DURATION.observe(duration)

    # --- Database Tracking ---
    def track_db_query(
        self,
        database: str,
        operation: str,
        duration: float
    ) -> None:
        """Track a database query."""
        if not self.enabled:
            return
        DB_QUERY_COUNT.labels(database=database, operation=operation).inc()
        DB_QUERY_DURATION.labels(database=database, operation=operation).observe(duration)

    def track_db_error(self, database: str) -> None:
        """Track a database connection error."""
        if not self.enabled:
            return
        DB_CONNECTION_ERRORS.labels(database=database).inc()

    def set_db_pool_size(self, database: str, size: int) -> None:
        """Set current database connection pool size."""
        if not self.enabled:
            return
        DB_CONNECTION_POOL_SIZE.labels(database=database).set(size)

    # --- Celery Task Tracking ---
    def track_celery_task(
        self,
        task_name: str,
        duration: float,
        success: bool
    ) -> None:
        """Track a Celery task execution."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        CELERY_TASK_COUNT.labels(task_name=task_name, status=status).inc()
        CELERY_TASK_DURATION.labels(task_name=task_name).observe(duration)

    def set_celery_queue_length(self, queue_name: str, length: int) -> None:
        """Set current Celery queue length."""
        if not self.enabled:
            return
        CELERY_QUEUE_LENGTH.labels(queue_name=queue_name).set(length)

    # --- AI API Tracking ---
    def track_ai_api_call(
        self,
        endpoint: str,
        duration: float,
        success: bool,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> None:
        """Track an AI API call."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        AI_API_CALLS.labels(endpoint=endpoint, status=status).inc()
        AI_API_DURATION.labels(endpoint=endpoint).observe(duration)
        if input_tokens > 0:
            AI_API_TOKENS.labels(direction='input').inc(input_tokens)
        if output_tokens > 0:
            AI_API_TOKENS.labels(direction='output').inc(output_tokens)

    # --- Auth Tracking ---
    def track_login(self, success: bool) -> None:
        """Track a user login attempt."""
        if not self.enabled:
            return
        status = 'success' if success else 'failed'
        USER_LOGIN_COUNT.labels(status=status).inc()

    def track_registration(self, success: bool) -> None:
        """Track a user registration."""
        if not self.enabled:
            return
        status = 'success' if success else 'failed'
        USER_REGISTRATIONS.labels(status=status).inc()

    def set_active_users(self, count: int) -> None:
        """Set current active user count."""
        if not self.enabled:
            return
        ACTIVE_USERS.set(count)

    # --- Health Check Tracking ---
    def set_health_status(self, service: str, healthy: bool) -> None:
        """Set health status for a service."""
        if not self.enabled:
            return
        HEALTH_CHECK_STATUS.labels(service=service).set(1 if healthy else 0)

    # --- Model Tracking ---
    def track_model_load(self, model_type: str, duration: float, loaded: bool) -> None:
        """Track ML model loading."""
        if not self.enabled:
            return
        MODEL_LOAD_DURATION.labels(model_type=model_type).observe(duration)
        MODEL_LOADED.labels(model_type=model_type).set(1 if loaded else 0)

    # --- Error Tracking ---
    def track_error(self, error_type: str, endpoint: str = 'unknown') -> None:
        """Track an application error."""
        if not self.enabled:
            return
        ERROR_COUNT.labels(error_type=error_type, endpoint=endpoint).inc()

    # --- PDF Reports ---
    def track_pdf_generation(self, duration: float, success: bool) -> None:
        """Track PDF report generation."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        PDF_GENERATION_COUNT.labels(status=status).inc()
        PDF_GENERATION_DURATION.observe(duration)

    # --- Agent/Chat ---
    def track_agent_conversation(self, duration: float, success: bool) -> None:
        """Track an agent conversation."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        AGENT_CONVERSATIONS.labels(status=status).inc()
        AGENT_RESPONSE_DURATION.observe(duration)

    # --- Risk Calculator ---
    def track_risk_calculation(
        self,
        risk_type: str,
        duration: float,
        success: bool
    ) -> None:
        """Track a risk calculation."""
        if not self.enabled:
            return
        status = 'success' if success else 'failure'
        RISK_CALCULATIONS.labels(risk_type=risk_type, status=status).inc()
        RISK_CALCULATION_DURATION.labels(risk_type=risk_type).observe(duration)

    # --- HTTP Request Tracking ---
    def track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float
    ) -> None:
        """Track an HTTP request."""
        if not self.enabled:
            return
        REQUEST_COUNT.labels(
            endpoint=endpoint, method=method, status_code=str(status_code)
        ).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(duration)

    def inc_requests_in_progress(self, endpoint: str) -> None:
        """Increment requests in progress for an endpoint."""
        if not self.enabled:
            return
        REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).inc()

    def dec_requests_in_progress(self, endpoint: str) -> None:
        """Decrement requests in progress for an endpoint."""
        if not self.enabled:
            return
        REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).dec()


# ============================================================
# Decorators for Easy Instrumentation
# ============================================================

def track_prediction_metric(prediction_type: str) -> Callable:
    """Decorator to automatically track prediction metrics.
    
    Usage:
        @track_prediction_metric('gender')
        def predict_gender(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.track_prediction(
                    prediction_type=prediction_type,
                    duration=duration,
                    success=success
                )
        return wrapper
    return decorator


def track_duration_metric(metric_name: str, **labels) -> Callable:
    """Generic decorator to track function execution duration.
    
    Usage:
        @track_duration_metric('pdf_generation')
        def generate_report():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if PROMETHEUS_AVAILABLE and hasattr(MetricsCollector, f'track_{metric_name}'):
                    tracker = getattr(metrics_collector, f'track_{metric_name}', None)
                    if tracker:
                        tracker(duration=duration, success=True, **labels)
        return wrapper
    return decorator


def track_celery_task_metric(task_name: str) -> Callable:
    """Decorator to automatically track Celery task metrics.
    
    Usage:
        @track_celery_task_metric('snp_analysis')
        def analyze_snp_file_task(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.track_celery_task(
                    task_name=task_name,
                    duration=duration,
                    success=success
                )
        return wrapper
    return decorator


# ============================================================
# Flask Middleware for Request Metrics
# ============================================================

def setup_flask_metrics(app) -> None:
    """
    Register Flask before/after request hooks to collect
    per-endpoint request metrics automatically.
    
    Call this once during app initialization:
        from utils.metrics import setup_flask_metrics
        setup_flask_metrics(app)
    """
    if not PROMETHEUS_AVAILABLE:
        logger.info("Prometheus not available - skipping Flask metrics middleware")
        return

    @app.before_request
    def _before_request():
        from flask import g, request as flask_request
        g._metrics_start_time = time.time()
        endpoint = flask_request.endpoint or 'unknown'
        metrics_collector.inc_requests_in_progress(endpoint)

    @app.after_request
    def _after_request(response):
        from flask import g, request as flask_request
        endpoint = flask_request.endpoint or 'unknown'
        method = flask_request.method
        duration = time.time() - getattr(g, '_metrics_start_time', time.time())

        metrics_collector.track_request(
            endpoint=endpoint,
            method=method,
            status_code=response.status_code,
            duration=duration
        )
        metrics_collector.dec_requests_in_progress(endpoint)
        return response

    @app.teardown_request
    def _teardown_request(exception):
        if exception:
            from flask import request as flask_request
            endpoint = flask_request.endpoint or 'unknown'
            error_type = type(exception).__name__
            metrics_collector.track_error(error_type=error_type, endpoint=endpoint)
            metrics_collector.dec_requests_in_progress(endpoint)

    logger.info("Flask request metrics middleware registered")


# Singleton instance
metrics_collector = MetricsCollector()
