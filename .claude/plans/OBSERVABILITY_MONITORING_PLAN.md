# OpenTelemetry + Grafana Observability Stack Plan

## Overview

This plan outlines the implementation of a comprehensive observability stack for OpenDeck using OpenTelemetry (OTEL), Grafana, Prometheus, Tempo, and Loki. This will provide full visibility into both the FastAPI backend and Angular frontend with distributed tracing, metrics, and logs.

## Current State Analysis

Your application currently has:
- **Backend**: FastAPI with PostgreSQL, Celery workers, Redis
- **Frontend**: Angular 20 with PrimeNG components
- **Infrastructure**: Docker Compose for local development
- **Logging**: Basic Python logging (structured logging mentioned in Ollama plan)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenDeck Application                        │
├──────────────────────┬──────────────────────────────────────────┤
│  Angular Frontend    │         FastAPI Backend                  │
│  (Browser)          │    (API + Celery Workers)                │
│                     │                                           │
│  OTEL JS SDK        │    OTEL Python SDK                       │
│  - Browser traces   │    - HTTP traces                         │
│  - User interactions│    - Database traces                     │
│  - Performance      │    - Celery task traces                  │
│  - Errors           │    - Custom metrics                      │
└──────────┬───────────┴──────────────┬───────────────────────────┘
           │                          │
           │ HTTP/gRPC               │ HTTP/gRPC
           │ (OTLP)                  │ (OTLP)
           │                          │
           └──────────┬───────────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │  OTEL Collector     │
           │  (Aggregation)      │
           └──────────┬──────────┘
                      │
        ┏─────────────┼─────────────┓
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌─────────┐
│  Prometheus  │ │   Tempo  │ │  Loki   │
│  (Metrics)   │ │ (Traces) │ │ (Logs)  │
└──────┬───────┘ └────┬─────┘ └────┬────┘
       │              │            │
       └──────────────┼────────────┘
                      │
                      ▼
              ┌──────────────┐
              │   Grafana    │
              │ (Dashboards) │
              └──────────────┘
```

## Tech Stack for Observability

### Core Components
- **OpenTelemetry Collector**: Central aggregation and routing
- **Grafana**: Visualization and dashboards
- **Prometheus**: Metrics storage and querying
- **Tempo**: Distributed tracing backend
- **Loki**: Log aggregation and querying

### Instrumentation Libraries
- **Backend**: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`
- **Frontend**: `@opentelemetry/api`, `@opentelemetry/sdk-trace-web`, `@opentelemetry/instrumentation`

## Implementation Plan

### Phase 1: Infrastructure Setup

#### 1.1 Update Docker Compose

Create `backend/docker-compose.observability.yml`:

```yaml
version: '3.8'

services:
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.94.0
    container_name: opendeck-otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC receiver
      - "4318:4318"   # OTLP HTTP receiver
      - "8889:8889"   # Prometheus metrics exporter
      - "13133:13133" # Health check
    networks:
      - opendeck-network

  # Prometheus for metrics
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: opendeck-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-remote-write-receiver'
      - '--enable-feature=exemplar-storage'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - opendeck-network

  # Tempo for distributed tracing
  tempo:
    image: grafana/tempo:2.3.1
    container_name: opendeck-tempo
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/tmp/tempo
    ports:
      - "3200:3200"   # Tempo query frontend
      - "4317"        # OTLP gRPC
      - "4318"        # OTLP HTTP
    networks:
      - opendeck-network

  # Loki for logs
  loki:
    image: grafana/loki:2.9.3
    container_name: opendeck-loki
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki
    ports:
      - "3100:3100"
    networks:
      - opendeck-network

  # Grafana for visualization
  grafana:
    image: grafana/grafana:10.2.3
    container_name: opendeck-grafana
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
      - GF_AUTH_DISABLE_LOGIN_FORM=true
      - GF_FEATURE_TOGGLES_ENABLE=traceqlEditor
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - opendeck-network
    depends_on:
      - prometheus
      - tempo
      - loki

volumes:
  prometheus-data:
  tempo-data:
  loki-data:
  grafana-data:

networks:
  opendeck-network:
    external: true
```

#### 1.2 OTEL Collector Configuration

Create `backend/otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
        cors:
          allowed_origins:
            - "http://localhost:4200"
            - "http://localhost:*"

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  memory_limiter:
    check_interval: 1s
    limit_mib: 512

  # Add resource attributes
  resource:
    attributes:
      - key: service.namespace
        value: opendeck
        action: insert

  # Filter out health check endpoints
  filter/healthcheck:
    traces:
      span:
        - 'attributes["http.target"] == "/health"'

exporters:
  # Export metrics to Prometheus
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: opendeck

  # Export traces to Tempo
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  # Export logs to Loki
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    labels:
      resource:
        service.name: "service_name"
      attributes:
        level: "level"

  # Debug exporter (optional, for development)
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, filter/healthcheck, resource, batch]
      exporters: [otlp/tempo, logging]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [prometheus, logging]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [loki, logging]
```

#### 1.3 Prometheus Configuration

Create `backend/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'opendeck-local'
    environment: 'development'

scrape_configs:
  # Scrape OTEL Collector metrics
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']

  # Scrape FastAPI metrics (if exposing Prometheus endpoint)
  - job_name: 'fastapi-backend'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'

  # Scrape Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Scrape Grafana metrics
  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
```

#### 1.4 Tempo Configuration

Create `backend/tempo.yaml`:

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

ingester:
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 1h

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/blocks
    wal:
      path: /tmp/tempo/wal

query_frontend:
  search:
    duration_slo: 5s
    throughput_bytes_slo: 1.073741824e+09
  trace_by_id:
    duration_slo: 5s

metrics_generator:
  registry:
    external_labels:
      source: tempo
      cluster: opendeck-local
  storage:
    path: /tmp/tempo/generator/wal
    remote_write:
      - url: http://prometheus:9090/api/v1/write
        send_exemplars: true

overrides:
  defaults:
    metrics_generator:
      processors: [service-graphs, span-metrics]
```

#### 1.5 Loki Configuration

Create `backend/loki-config.yaml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  instance_addr: 127.0.0.1
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

limits_config:
  retention_period: 744h  # 31 days
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20
```

#### 1.6 Grafana Provisioning

Create `backend/grafana/provisioning/datasources/datasources.yaml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      httpMethod: POST
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: tempo

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: true
    jsonData:
      httpMethod: GET
      tracesToLogs:
        datasourceUid: loki
        tags: ['job', 'instance', 'pod', 'namespace']
        mappedTags: [{ key: 'service.name', value: 'service' }]
        mapTagNamesEnabled: false
        spanStartTimeShift: '1h'
        spanEndTimeShift: '1h'
        filterByTraceID: false
        filterBySpanID: false
      serviceMap:
        datasourceUid: prometheus
      search:
        hide: false
      nodeGraph:
        enabled: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: '$${__value.raw}'
```

Create `backend/grafana/provisioning/dashboards/dashboards.yaml`:

```yaml
apiVersion: 1

providers:
  - name: 'OpenDeck Dashboards'
    orgId: 1
    folder: 'OpenDeck'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

### Phase 2: Backend Instrumentation (FastAPI)

#### 2.1 Install Dependencies

Add to `backend/requirements.txt`:

```python
# OpenTelemetry Core
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-exporter-otlp==1.22.0

# OpenTelemetry Instrumentation
opentelemetry-instrumentation==0.43b0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-sqlalchemy==0.43b0
opentelemetry-instrumentation-redis==0.43b0
opentelemetry-instrumentation-celery==0.43b0
opentelemetry-instrumentation-httpx==0.43b0
opentelemetry-instrumentation-logging==0.43b0

# Prometheus metrics exporter (optional)
opentelemetry-exporter-prometheus==0.43b0
prometheus-client==0.19.0
```

#### 2.2 Create OTEL Configuration Module

Create `backend/app/observability/otel_config.py`:

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from prometheus_client import start_http_server
import structlog
from app.config import settings

logger = structlog.get_logger()


def setup_opentelemetry():
    """
    Configure OpenTelemetry instrumentation for FastAPI application.

    Sets up:
    - Distributed tracing with OTLP exporter
    - Metrics collection with Prometheus
    - Automatic instrumentation for FastAPI, SQLAlchemy, Redis, Celery
    """

    # Define resource attributes
    resource = Resource(attributes={
        SERVICE_NAME: "opendeck-backend",
        SERVICE_VERSION: "1.0.0",
        "deployment.environment": settings.env,
        "service.namespace": "opendeck",
    })

    # ===== TRACING SETUP =====

    # Configure trace provider
    trace_provider = TracerProvider(resource=resource)

    # OTLP exporter for traces (to Tempo via OTEL Collector)
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint=settings.otel_collector_endpoint,
        insecure=True  # Use TLS in production
    )

    # Add batch processor for efficient export
    trace_provider.add_span_processor(
        BatchSpanProcessor(otlp_trace_exporter)
    )

    # Set global trace provider
    trace.set_tracer_provider(trace_provider)

    logger.info("otel_tracing_configured",
                endpoint=settings.otel_collector_endpoint)

    # ===== METRICS SETUP =====

    # Prometheus metric reader (exposes /metrics endpoint)
    prometheus_reader = PrometheusMetricReader()

    # OTLP metric exporter (to Prometheus via OTEL Collector)
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=settings.otel_collector_endpoint,
        insecure=True
    )

    otlp_metric_reader = PeriodicExportingMetricReader(
        otlp_metric_exporter,
        export_interval_millis=15000  # 15 seconds
    )

    # Configure meter provider with both readers
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[prometheus_reader, otlp_metric_reader]
    )

    # Set global meter provider
    metrics.set_meter_provider(meter_provider)

    # Start Prometheus metrics server on separate port
    start_http_server(port=8001, addr="0.0.0.0")

    logger.info("otel_metrics_configured",
                prometheus_port=8001)

    # ===== AUTOMATIC INSTRUMENTATION =====

    # Note: FastAPI instrumentation should be done in main.py after app creation
    # SQLAlchemy instrumentation
    SQLAlchemyInstrumentor().instrument(
        enable_commenter=True,
        commenter_options={"db_driver": True}
    )

    # Redis instrumentation
    RedisInstrumentor().instrument()

    # Celery instrumentation
    CeleryInstrumentor().instrument()

    # HTTP client instrumentation
    HTTPXClientInstrumentor().instrument()

    # Logging instrumentation (adds trace context to logs)
    LoggingInstrumentor().instrument(set_logging_format=True)

    logger.info("otel_auto_instrumentation_complete",
                instrumentors=["fastapi", "sqlalchemy", "redis", "celery", "httpx", "logging"])

    return trace_provider, meter_provider


def instrument_fastapi(app):
    """
    Instrument FastAPI application with OpenTelemetry.
    Call this after creating the FastAPI app instance.
    """
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="/health,/metrics",  # Don't trace health checks
        http_capture_headers_server_request=["content-type", "user-agent"],
        http_capture_headers_server_response=["content-type"]
    )
    logger.info("fastapi_instrumented")


def get_tracer(name: str):
    """Get a tracer instance for manual instrumentation."""
    return trace.get_tracer(name)


def get_meter(name: str):
    """Get a meter instance for custom metrics."""
    return metrics.get_meter(name)
```

#### 2.3 Update Configuration

Add to `backend/app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # OpenTelemetry Configuration
    otel_enabled: bool = True
    otel_collector_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "opendeck-backend"
    otel_service_version: str = "1.0.0"
```

#### 2.4 Update Main Application

Update `backend/app/main.py`:

```python
from app.observability.otel_config import setup_opentelemetry, instrument_fastapi
from app.config import settings
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize OpenTelemetry BEFORE creating FastAPI app
if settings.otel_enabled:
    setup_opentelemetry()
    logger.info("opentelemetry_initialized")

# Create FastAPI app
app = FastAPI(
    title="OpenDeck API",
    version="1.0.0",
    # ... other settings ...
)

# Instrument FastAPI with OpenTelemetry AFTER app creation
if settings.otel_enabled:
    instrument_fastapi(app)

# ... rest of your app setup ...
```

#### 2.5 Add Custom Metrics

Create `backend/app/observability/custom_metrics.py`:

```python
from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram, UpDownCounter
from typing import Dict
import structlog

logger = structlog.get_logger()

class OpenDeckMetrics:
    """Custom metrics for OpenDeck application."""

    def __init__(self):
        meter = metrics.get_meter("opendeck.custom")

        # === USER METRICS ===
        self.user_registrations = meter.create_counter(
            name="opendeck.users.registrations.total",
            description="Total number of user registrations",
            unit="1"
        )

        self.user_logins = meter.create_counter(
            name="opendeck.users.logins.total",
            description="Total number of user logins",
            unit="1"
        )

        self.active_users = meter.create_up_down_counter(
            name="opendeck.users.active",
            description="Number of currently active users",
            unit="1"
        )

        # === DECK METRICS ===
        self.decks_created = meter.create_counter(
            name="opendeck.decks.created.total",
            description="Total number of decks created",
            unit="1"
        )

        self.decks_deleted = meter.create_counter(
            name="opendeck.decks.deleted.total",
            description="Total number of decks deleted",
            unit="1"
        )

        self.deck_count = meter.create_up_down_counter(
            name="opendeck.decks.count",
            description="Current number of decks",
            unit="1"
        )

        # === FLASHCARD METRICS ===
        self.cards_created = meter.create_counter(
            name="opendeck.cards.created.total",
            description="Total number of flashcards created",
            unit="1"
        )

        self.cards_studied = meter.create_counter(
            name="opendeck.cards.studied.total",
            description="Total number of flashcards studied",
            unit="1"
        )

        self.study_sessions = meter.create_counter(
            name="opendeck.study_sessions.total",
            description="Total number of study sessions",
            unit="1"
        )

        self.study_session_duration = meter.create_histogram(
            name="opendeck.study_sessions.duration",
            description="Duration of study sessions in seconds",
            unit="s"
        )

        # === DOCUMENT PROCESSING METRICS ===
        self.documents_uploaded = meter.create_counter(
            name="opendeck.documents.uploaded.total",
            description="Total number of documents uploaded",
            unit="1"
        )

        self.documents_processed = meter.create_counter(
            name="opendeck.documents.processed.total",
            description="Total number of documents processed successfully",
            unit="1"
        )

        self.documents_failed = meter.create_counter(
            name="opendeck.documents.failed.total",
            description="Total number of documents that failed processing",
            unit="1"
        )

        self.document_processing_duration = meter.create_histogram(
            name="opendeck.documents.processing_duration",
            description="Time to process documents in seconds",
            unit="s"
        )

        # === CELERY TASK METRICS ===
        self.celery_tasks_started = meter.create_counter(
            name="opendeck.celery.tasks.started.total",
            description="Total number of Celery tasks started",
            unit="1"
        )

        self.celery_tasks_completed = meter.create_counter(
            name="opendeck.celery.tasks.completed.total",
            description="Total number of Celery tasks completed",
            unit="1"
        )

        self.celery_tasks_failed = meter.create_counter(
            name="opendeck.celery.tasks.failed.total",
            description="Total number of Celery tasks failed",
            unit="1"
        )

        self.celery_queue_length = meter.create_up_down_counter(
            name="opendeck.celery.queue.length",
            description="Current Celery queue length",
            unit="1"
        )

        # === DATABASE METRICS ===
        self.db_queries = meter.create_counter(
            name="opendeck.db.queries.total",
            description="Total number of database queries",
            unit="1"
        )

        self.db_query_duration = meter.create_histogram(
            name="opendeck.db.query.duration",
            description="Database query duration in milliseconds",
            unit="ms"
        )

        self.db_connection_pool_size = meter.create_up_down_counter(
            name="opendeck.db.connection_pool.size",
            description="Database connection pool size",
            unit="1"
        )

        logger.info("custom_metrics_initialized")

    def record_user_registration(self, attributes: Dict[str, str] = None):
        """Record a user registration event."""
        self.user_registrations.add(1, attributes or {})

    def record_user_login(self, attributes: Dict[str, str] = None):
        """Record a user login event."""
        self.user_logins.add(1, attributes or {})

    def record_deck_created(self, topic: str = None):
        """Record deck creation."""
        attrs = {"topic": topic} if topic else {}
        self.decks_created.add(1, attrs)

    def record_card_studied(self, deck_id: str, card_id: str):
        """Record a flashcard study event."""
        self.cards_studied.add(1, {"deck_id": deck_id, "card_id": card_id})

    def record_study_session(self, duration_seconds: float, cards_studied: int):
        """Record a study session."""
        self.study_sessions.add(1)
        self.study_session_duration.record(duration_seconds, {"cards_studied": str(cards_studied)})

    def record_document_upload(self, file_type: str, size_mb: float):
        """Record document upload."""
        self.documents_uploaded.add(1, {"file_type": file_type, "size_mb": str(size_mb)})

    def record_document_processed(self, file_type: str, duration_seconds: float, cards_generated: int):
        """Record successful document processing."""
        attrs = {
            "file_type": file_type,
            "cards_generated": str(cards_generated)
        }
        self.documents_processed.add(1, attrs)
        self.document_processing_duration.record(duration_seconds, attrs)

    def record_document_failed(self, file_type: str, error_type: str):
        """Record failed document processing."""
        self.documents_failed.add(1, {"file_type": file_type, "error_type": error_type})


# Global metrics instance
opendeck_metrics = OpenDeckMetrics()
```

#### 2.6 Add Custom Tracing

Create `backend/app/observability/tracing.py`:

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from functools import wraps
import structlog
from typing import Callable, Any

logger = structlog.get_logger()
tracer = trace.get_tracer("opendeck.custom")


def trace_operation(operation_name: str = None, attributes: dict = None):
    """
    Decorator to add custom tracing to functions.

    Usage:
        @trace_operation("process_document")
        def process_document(doc_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function arguments as attributes
                if args:
                    span.set_attribute("args", str(args))
                if kwargs:
                    span.set_attribute("kwargs", str(kwargs))

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    logger.error("traced_operation_failed",
                                operation=span_name,
                                error=str(e))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                if args:
                    span.set_attribute("args", str(args))
                if kwargs:
                    span.set_attribute("kwargs", str(kwargs))

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    logger.error("traced_operation_failed",
                                operation=span_name,
                                error=str(e))
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attributes(attributes: dict):
    """Add attributes to the current span."""
    span = trace.get_current_span()
    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict = None):
    """Add an event to the current span."""
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes or {})
```

#### 2.7 Update Celery Worker

Update `backend/app/workers/celery_app.py`:

```python
from celery.signals import task_prerun, task_postrun, task_failure
from app.observability.custom_metrics import opendeck_metrics
import structlog

logger = structlog.get_logger()

# ... existing celery_app setup ...

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Record task start."""
    opendeck_metrics.celery_tasks_started.add(1, {"task_name": task.name})
    logger.info("celery_task_started", task_id=task_id, task_name=task.name)

@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    """Record task completion."""
    opendeck_metrics.celery_tasks_completed.add(1, {"task_name": task.name})
    logger.info("celery_task_completed", task_id=task_id, task_name=task.name)

@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    """Record task failure."""
    opendeck_metrics.celery_tasks_failed.add(1, {"task_name": kwargs.get('task', {}).name})
    logger.error("celery_task_failed", task_id=task_id, error=str(exception))
```

### Phase 3: Frontend Instrumentation (Angular)

#### 3.1 Install Dependencies

```bash
cd opendeck-portal
npm install --save \
  @opentelemetry/api \
  @opentelemetry/sdk-trace-web \
  @opentelemetry/sdk-metrics \
  @opentelemetry/instrumentation \
  @opentelemetry/instrumentation-document-load \
  @opentelemetry/instrumentation-user-interaction \
  @opentelemetry/instrumentation-fetch \
  @opentelemetry/instrumentation-xml-http-request \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/exporter-metrics-otlp-http \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

#### 3.2 Create OTEL Service

Create `opendeck-portal/src/app/services/otel.service.ts`:

```typescript
import { Injectable } from '@angular/core';
import { WebTracerProvider, BatchSpanProcessor } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';
import { trace, context, Span } from '@opentelemetry/api';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class OtelService {
  private tracer: any;
  private provider: WebTracerProvider | null = null;

  constructor() {
    this.initializeOpenTelemetry();
  }

  private initializeOpenTelemetry(): void {
    if (!environment.otelEnabled) {
      console.log('OpenTelemetry is disabled');
      return;
    }

    // Configure resource
    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'opendeck-frontend',
      [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: environment.production ? 'production' : 'development',
      'service.namespace': 'opendeck',
    });

    // Create trace provider
    this.provider = new WebTracerProvider({
      resource: resource,
    });

    // Configure OTLP exporter
    const otlpExporter = new OTLPTraceExporter({
      url: `${environment.otelCollectorUrl}/v1/traces`,
      headers: {},
    });

    // Add batch processor
    this.provider.addSpanProcessor(new BatchSpanProcessor(otlpExporter, {
      maxQueueSize: 100,
      maxExportBatchSize: 10,
      scheduledDelayMillis: 500,
      exportTimeoutMillis: 30000,
    }));

    // Register provider
    this.provider.register({
      contextManager: new ZoneContextManager(),
    });

    // Get tracer
    this.tracer = trace.getTracer('opendeck-frontend', '1.0.0');

    // Register automatic instrumentations
    registerInstrumentations({
      instrumentations: [
        new DocumentLoadInstrumentation(),
        new UserInteractionInstrumentation({
          eventNames: ['click', 'submit', 'keypress'],
        }),
        new FetchInstrumentation({
          propagateTraceHeaderCorsUrls: [
            environment.apiBaseUrl,
          ],
          clearTimingResources: true,
        }),
        new XMLHttpRequestInstrumentation({
          propagateTraceHeaderCorsUrls: [
            environment.apiBaseUrl,
          ],
        }),
      ],
    });

    console.log('OpenTelemetry initialized successfully');
  }

  /**
   * Start a custom span for manual instrumentation
   */
  startSpan(name: string, attributes?: Record<string, any>): Span {
    const span = this.tracer.startSpan(name, {
      attributes: attributes || {},
    });
    return span;
  }

  /**
   * Execute a function within a span context
   */
  async traceAsync<T>(name: string, fn: () => Promise<T>, attributes?: Record<string, any>): Promise<T> {
    const span = this.startSpan(name, attributes);

    try {
      const result = await fn();
      span.setStatus({ code: 1 }); // OK
      span.end();
      return result;
    } catch (error) {
      span.setStatus({ code: 2, message: String(error) }); // ERROR
      span.recordException(error as Error);
      span.end();
      throw error;
    }
  }

  /**
   * Execute a synchronous function within a span context
   */
  trace<T>(name: string, fn: () => T, attributes?: Record<string, any>): T {
    const span = this.startSpan(name, attributes);

    try {
      const result = fn();
      span.setStatus({ code: 1 }); // OK
      span.end();
      return result;
    } catch (error) {
      span.setStatus({ code: 2, message: String(error) }); // ERROR
      span.recordException(error as Error);
      span.end();
      throw error;
    }
  }

  /**
   * Add custom attributes to current span
   */
  addSpanAttributes(attributes: Record<string, any>): void {
    const span = trace.getActiveSpan();
    if (span) {
      Object.entries(attributes).forEach(([key, value]) => {
        span.setAttribute(key, value);
      });
    }
  }

  /**
   * Add event to current span
   */
  addSpanEvent(name: string, attributes?: Record<string, any>): void {
    const span = trace.getActiveSpan();
    if (span) {
      span.addEvent(name, attributes);
    }
  }

  /**
   * Record an exception in the current span
   */
  recordException(error: Error): void {
    const span = trace.getActiveSpan();
    if (span) {
      span.recordException(error);
      span.setStatus({ code: 2, message: error.message });
    }
  }
}
```

#### 3.3 Create Custom Metrics Service

Create `opendeck-portal/src/app/services/metrics.service.ts`:

```typescript
import { Injectable } from '@angular/core';

export interface StudySessionMetrics {
  sessionId: string;
  startTime: number;
  cardsStudied: number;
  correctAnswers: number;
  deckId: string;
}

@Injectable({
  providedIn: 'root'
})
export class MetricsService {
  private currentSession: StudySessionMetrics | null = null;

  /**
   * Start a new study session
   */
  startStudySession(deckId: string): void {
    this.currentSession = {
      sessionId: this.generateSessionId(),
      startTime: Date.now(),
      cardsStudied: 0,
      correctAnswers: 0,
      deckId: deckId,
    };
  }

  /**
   * Record a card study event
   */
  recordCardStudied(wasCorrect: boolean): void {
    if (this.currentSession) {
      this.currentSession.cardsStudied++;
      if (wasCorrect) {
        this.currentSession.correctAnswers++;
      }
    }
  }

  /**
   * End the current study session and return metrics
   */
  endStudySession(): StudySessionMetrics | null {
    if (!this.currentSession) {
      return null;
    }

    const duration = Date.now() - this.currentSession.startTime;
    const metrics = {
      ...this.currentSession,
      duration: duration,
    };

    this.currentSession = null;
    return metrics;
  }

  /**
   * Send metrics to backend
   */
  async sendMetrics(metrics: any): Promise<void> {
    // In a real implementation, send to backend API
    console.log('Sending metrics:', metrics);
    // await this.http.post('/api/v1/metrics', metrics).toPromise();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

#### 3.4 Update Environment Configuration

Update `opendeck-portal/src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000',

  // OpenTelemetry configuration
  otelEnabled: true,
  otelCollectorUrl: 'http://localhost:4318',
};
```

#### 3.5 Initialize OTEL in App

Update `opendeck-portal/src/main.ts`:

```typescript
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { OtelService } from './app/services/otel.service';

// Initialize OpenTelemetry before bootstrapping
const otelService = new OtelService();

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
```

#### 3.6 Add Tracing to Components

Update `opendeck-portal/src/app/pages/deck-view/deck-view.component.ts`:

```typescript
import { OtelService } from '../../services/otel.service';
import { MetricsService } from '../../services/metrics.service';

export class DeckViewComponent implements OnInit {
  constructor(
    // ... existing dependencies
    private otelService: OtelService,
    private metricsService: MetricsService
  ) {}

  async ngOnInit(): Promise<void> {
    // Trace the initialization
    await this.otelService.traceAsync('deck-view.init', async () => {
      const deckId = this.route.snapshot.paramMap.get('id');
      if (deckId) {
        this.otelService.addSpanAttributes({ 'deck.id': deckId });
        await this.loadDeck(deckId);
      }
    });
  }

  async loadDeck(deckId: string): Promise<void> {
    await this.otelService.traceAsync('deck-view.loadDeck', async () => {
      this.loading = true;
      try {
        this.deck = await this.deckService.getDeck(deckId).toPromise();
        this.cards = await this.cardService.getCards(deckId).toPromise();

        this.otelService.addSpanAttributes({
          'deck.cardCount': this.cards.length,
          'deck.topic': this.deck.topic,
        });

        this.otelService.addSpanEvent('deck.loaded', {
          cardCount: this.cards.length,
        });
      } catch (error) {
        this.otelService.recordException(error as Error);
        throw error;
      } finally {
        this.loading = false;
      }
    });
  }

  startStudySession(): void {
    this.otelService.addSpanEvent('study_session.started', {
      'deck.id': this.deck.id,
    });
    this.metricsService.startStudySession(this.deck.id);
  }

  onCardAnswered(wasCorrect: boolean): void {
    this.metricsService.recordCardStudied(wasCorrect);
    this.otelService.addSpanEvent('card.answered', {
      correct: wasCorrect,
    });
  }
}
```

### Phase 4: Grafana Dashboards

#### 4.1 Backend Dashboard

Create `backend/grafana/dashboards/opendeck-backend.json`:

```json
{
  "dashboard": {
    "title": "OpenDeck Backend",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_server_requests_total{service_name=\"opendeck-backend\"}[5m])",
            "legendFormat": "{{method}} {{route}}"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_server_duration_bucket[5m]))",
            "legendFormat": "{{method}} {{route}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_server_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "{{method}} {{route}} - {{status_code}}"
          }
        ]
      },
      {
        "title": "Database Query Duration",
        "targets": [
          {
            "expr": "rate(opendeck_db_query_duration_sum[5m]) / rate(opendeck_db_query_duration_count[5m])",
            "legendFormat": "Avg Query Time"
          }
        ]
      },
      {
        "title": "Celery Queue Length",
        "targets": [
          {
            "expr": "opendeck_celery_queue_length",
            "legendFormat": "Queue: {{queue}}"
          }
        ]
      },
      {
        "title": "Document Processing",
        "targets": [
          {
            "expr": "rate(opendeck_documents_processed_total[5m])",
            "legendFormat": "Processed"
          },
          {
            "expr": "rate(opendeck_documents_failed_total[5m])",
            "legendFormat": "Failed"
          }
        ]
      }
    ]
  }
}
```

#### 4.2 Frontend Dashboard

Create `backend/grafana/dashboards/opendeck-frontend.json`:

```json
{
  "dashboard": {
    "title": "OpenDeck Frontend",
    "panels": [
      {
        "title": "Page Load Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(document_load_duration_bucket[5m]))",
            "legendFormat": "p95"
          }
        ]
      },
      {
        "title": "API Request Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_client_duration_bucket{service_name=\"opendeck-frontend\"}[5m]))",
            "legendFormat": "{{method}} {{url}}"
          }
        ]
      },
      {
        "title": "User Interactions",
        "targets": [
          {
            "expr": "rate(user_interaction_total[5m])",
            "legendFormat": "{{event_type}}"
          }
        ]
      },
      {
        "title": "Frontend Errors",
        "targets": [
          {
            "expr": "rate(exceptions_total{service_name=\"opendeck-frontend\"}[5m])",
            "legendFormat": "{{exception_type}}"
          }
        ]
      }
    ]
  }
}
```

#### 4.3 Business Metrics Dashboard

Create `backend/grafana/dashboards/opendeck-business.json`:

```json
{
  "dashboard": {
    "title": "OpenDeck Business Metrics",
    "panels": [
      {
        "title": "User Registrations",
        "targets": [
          {
            "expr": "increase(opendeck_users_registrations_total[1h])",
            "legendFormat": "Hourly Registrations"
          }
        ]
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "opendeck_users_active",
            "legendFormat": "Active Users"
          }
        ]
      },
      {
        "title": "Decks Created",
        "targets": [
          {
            "expr": "rate(opendeck_decks_created_total[5m])",
            "legendFormat": "{{topic}}"
          }
        ]
      },
      {
        "title": "Study Sessions",
        "targets": [
          {
            "expr": "rate(opendeck_study_sessions_total[5m])",
            "legendFormat": "Sessions per minute"
          }
        ]
      },
      {
        "title": "Cards Studied",
        "targets": [
          {
            "expr": "rate(opendeck_cards_studied_total[5m])",
            "legendFormat": "Cards per minute"
          }
        ]
      }
    ]
  }
}
```

### Phase 5: Deployment & Testing

#### 5.1 Start the Observability Stack

```bash
cd backend

# Start the observability stack
docker-compose -f docker-compose.observability.yml up -d

# Verify all services are running
docker-compose -f docker-compose.observability.yml ps

# Check OTEL Collector health
curl http://localhost:13133/

# Check Grafana
open http://localhost:3000
```

#### 5.2 Update Main Docker Compose

Update `backend/docker-compose.yml` to include observability endpoints:

```yaml
services:
  app:
    # ... existing config ...
    environment:
      - OTEL_ENABLED=true
      - OTEL_COLLECTOR_ENDPOINT=http://otel-collector:4317
    ports:
      - "8000:8000"
      - "8001:8001"  # Prometheus metrics endpoint
    depends_on:
      - otel-collector
```

#### 5.3 Testing Checklist

1. **Verify Tracing**:
   - Make API requests
   - Check traces in Grafana → Explore → Tempo
   - Verify traces span from frontend to backend

2. **Verify Metrics**:
   - Check Prometheus targets at http://localhost:9090/targets
   - Query metrics in Grafana → Explore → Prometheus
   - Verify custom metrics appear

3. **Verify Logs**:
   - Check logs in Grafana → Explore → Loki
   - Verify log correlation with traces
   - Test log filtering and searching

4. **Verify Dashboards**:
   - Import dashboards into Grafana
   - Check all panels display data
   - Verify time ranges and refresh rates

## Key Features

### Distributed Tracing
- End-to-end request tracing from browser to database
- Trace context propagation across services
- Automatic instrumentation for FastAPI, SQLAlchemy, Redis, Celery
- Custom span annotations for business logic

### Metrics Collection
- System metrics (CPU, memory, disk)
- Application metrics (requests, errors, latency)
- Business metrics (users, decks, study sessions)
- Custom metrics for specific features

### Log Aggregation
- Structured JSON logging
- Correlation with traces via trace IDs
- Log levels and filtering
- Search and analysis in Grafana

### Alerting
- Prometheus Alertmanager integration
- Grafana alerts on metrics thresholds
- Notification channels (email, Slack, PagerDuty)

## Best Practices

### Performance
- Use sampling for high-volume traces (e.g., 10% sampling in production)
- Batch span exports to reduce overhead
- Set appropriate timeout and buffer sizes
- Monitor OTEL Collector resource usage

### Security
- Enable TLS for OTLP exports in production
- Restrict Grafana access with authentication
- Sanitize sensitive data in spans and logs
- Use network policies to isolate observability stack

### Data Retention
- Configure appropriate retention periods:
  - Prometheus: 15 days
  - Tempo: 7 days
  - Loki: 31 days
- Set up long-term storage (S3) for important metrics
- Archive old data periodically

### Monitoring the Monitors
- Set up alerts for OTEL Collector failures
- Monitor Prometheus, Tempo, Loki health
- Track data ingestion rates and storage usage
- Regular backup of Grafana dashboards

## Production Deployment

### Scaling Considerations
1. **OTEL Collector**: Deploy as sidecar or centralized service
2. **Prometheus**: Use federation for multi-cluster setups
3. **Tempo**: Configure S3 backend for scalability
4. **Loki**: Use object storage (S3) for chunks
5. **Grafana**: Set up HA with shared database

### Cloud Deployment (AWS)
- Use AWS ECS/EKS for containerized deployment
- Store metrics/traces in S3
- Use AWS Load Balancer for Grafana
- Set up CloudWatch integration as backup

### Alternative: Managed Services
Consider managed alternatives for production:
- **Grafana Cloud**: Fully managed Grafana, Prometheus, Loki, Tempo
- **Datadog**: Comprehensive APM solution
- **New Relic**: Full-stack observability platform
- **Honeycomb**: Distributed tracing specialist

## Cost Optimization

1. **Use sampling**: 10-20% trace sampling in production
2. **Filter noisy endpoints**: Exclude health checks, static assets
3. **Compress data**: Enable compression for OTLP exports
4. **Set retention limits**: Don't store data indefinitely
5. **Use tiered storage**: Hot/warm/cold storage strategy

## Next Steps

1. Install OTEL dependencies (backend and frontend)
2. Configure OTEL Collector and observability stack
3. Instrument backend with OpenTelemetry
4. Instrument frontend with OpenTelemetry
5. Start observability stack with Docker Compose
6. Create Grafana dashboards
7. Set up alerts and notifications
8. Test end-to-end tracing
9. Document runbooks for common issues
10. Train team on using Grafana for debugging

## Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI OpenTelemetry Guide](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [Angular OpenTelemetry](https://github.com/open-telemetry/opentelemetry-js)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
