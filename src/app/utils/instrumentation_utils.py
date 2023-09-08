import logging
import traceback

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import get_current_span, set_tracer_provider
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.utils.constants import TRACE_ID_RESPONSE_HEADER
from app.utils.exceptions import populate_exception_details

settings = get_settings()


def configure_instrumentation():
    if settings.APPLICATIONINSIGHTS_CONNECTION_STRING:
        # https://github.com/microsoft/ApplicationInsights-Python/tree/main/azure-monitor-opentelemetry
        configure_azure_monitor(
            disable_logging=settings.DISABLE_LOG_INSTRUMENTATION,
            disable_metrics=settings.DISABLE_METRICS_INSTRUMENTATION,
            disable_tracing=settings.DISABLE_TRACING_INSTRUMENTATION,
            logger_name="app",  # This will always be root package name
            connection_string=settings.APPLICATIONINSIGHTS_CONNECTION_STRING
        )
    else:
        tracer = TracerProvider()
        set_tracer_provider(tracer)
        FastAPIInstrumentor().instrument()

    # Suppress logs from below to reduce noise
    logging.getLogger("azure.monitor.opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


class TraceIdInjectionMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response = await call_next(request)
        except Exception as e:
            # Response object is required always so that headers can be set. In case of exception the middleware
            # seems to be called before the exception is converted to JsonResponse. However this works as expected in
            # case of validation issues
            response = await populate_exception_details(request, e)
            traceback.print_exc()
        finally:
            currentspan = get_current_span()
            response.headers[TRACE_ID_RESPONSE_HEADER] = "{:032x}".format(currentspan.get_span_context().trace_id)
            return response
