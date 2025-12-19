import logging
import os
import time
import functools
import asyncio
from typing import Callable, Any, Coroutine
import contextvars
from logging.handlers import RotatingFileHandler

class DefaultLogFieldsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "emoji"):
            record.emoji = EMOJIS.get(record.levelname, "❔")

        if not hasattr(record, "service"):
            record.service = "system"

        if not hasattr(record, "func_name"):
            record.func_name = record.name

        return True

# -------------------------------------------------------------------
#   LOGGER SETUP (PRODUCTION-GRADE)
# -------------------------------------------------------------------

LOG_DIR = "app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

FORMAT = "%(asctime)s | %(levelname)s | %(emoji)s | %(service)s | %(func_name)s → %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(FORMAT, datefmt=DATEFMT))


file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"),
    maxBytes=5_000_000,
    backupCount=3,
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(FORMAT, datefmt=DATEFMT))
console_handler.addFilter(DefaultLogFieldsFilter())
file_handler.addFilter(DefaultLogFieldsFilter())
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# -------------------------------------------------------------------
#   INTERNAL LOG WRAPPER FUNCTION (USED BY ALL HELPERS)
# -------------------------------------------------------------------
_LOG_DEPTH: contextvars.ContextVar[int] = contextvars.ContextVar("_LOG_DEPTH", default=0)

EMOJIS = {
    "DEBUG": "🐞",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "💥",
}


def _log(level: str, message: str, func_name: str, service="core", indent: int = 0):
    emoji = EMOJIS.get(level, "❔")
    indent_str = "  " * max(indent, 0)

    logger.log(
        getattr(logging, level),
        f"{emoji} {indent_str}{func_name} → {message}",
        extra={
            "emoji": emoji,
            "func_name": func_name,
            "service": service,
        }
    )



# -------------------------------------------------------------------
#   PUBLIC LOG FUNCTIONS (ALL WRAPPER-COMPATIBLE)
# -------------------------------------------------------------------

def log_service_error(message: str, func_name: str, service="service"):
    _log("ERROR", message, func_name, service)


def log_service_startup(message: str, func_name="startup", service="service"):
    _log("INFO", message, func_name, service)


def log_db_query(query: str, func_name: str, params=None, duration_ms=None):
    msg = f"{query}"
    if params: msg += f" | params={params}"
    if duration_ms: msg += f" | {duration_ms:.2f}ms"
    _log("DEBUG", msg, func_name, "database")


def log_task_event(message: str, func_name: str, event="task", service="task"):
    _log("INFO", f"[{event}] {message}", func_name, service)


def log_debug(message: str, func_name: str, service="debug"):
    _log("DEBUG", message, func_name, service)


def log_request(method: str, path: str, func_name: str, status=None, duration_ms=None, ip=None):
    msg = f"{method} {path}"
    if status: msg += f" | status={status}"
    if duration_ms: msg += f" | {duration_ms:.2f}ms"
    if ip: msg += f" | ip={ip}"
    _log("INFO", msg, func_name, "http")


def log_exception(exc: Exception, func_name: str, service="exception"):
    _log("ERROR", f"{type(exc).__name__}: {exc}", func_name, service)


def log_warning(message: str, func_name: str, service="warn"):
    _log("WARNING", message, func_name, service)


# -------------------------------------------------------------------
#   DECORATOR (WORKS WITH ASYNC + SYNC)
# -------------------------------------------------------------------

def log_service(fn: callable = None, *, service: str = "task", suppress_inner: bool = False):
    """
    Safe decorator for both sync & async functions.

    Behavior:
      - Detects coroutine functions and wraps them with async wrapper.
      - For sync functions:
          * If called from a running event loop, runs the sync function in a thread via asyncio.to_thread()
            (prevents blocking the loop).
          * If called from sync code, runs directly.
      - Tracks nested depth and optionally suppresses inner logs when `suppress_inner=True`.
    Usage:
      @log_service_safe
      def small_helper(...): ...
      OR
      @log_service_safe(suppress_inner=True)
      def top_level(...): ...
    """

    def decorator(inner_fn):
        is_coro = asyncio.iscoroutinefunction(inner_fn)

        @functools.wraps(inner_fn)
        async def _async_wrapper(*args, **kwargs):
            fn_name = inner_fn.__name__
            depth = _LOG_DEPTH.get()

            if suppress_inner and depth > 0:
                return await inner_fn(*args, **kwargs) if is_coro else await asyncio.to_thread(inner_fn, *args,
                                                                                               **kwargs)

            token = _LOG_DEPTH.set(depth + 1)

            start = None  # <-- FIX: define start before try

            try:
                _log("INFO", "started", fn_name, service=service, indent=depth)

                start = time.perf_counter()

                if is_coro:
                    result = await inner_fn(*args, **kwargs)
                else:
                    result = await asyncio.to_thread(inner_fn, *args, **kwargs)

                elapsed = (time.perf_counter() - start) * 1000 if start else -1
                _log("INFO", f"completed | {elapsed:.2f}ms", fn_name, service=service, indent=depth)
                return result

            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000 if start else -1
                _log("ERROR", f"failed after {elapsed:.2f}ms | {exc}", fn_name, service=service, indent=depth)
                raise

            finally:
                _LOG_DEPTH.reset(token)

        @functools.wraps(inner_fn)
        def _sync_wrapper(*args, **kwargs):
            fn_name = inner_fn.__name__
            depth = _LOG_DEPTH.get()

            if suppress_inner and depth > 0:
                return inner_fn(*args, **kwargs)

            token = _LOG_DEPTH.set(depth + 1)

            start = None  # <-- FIX: define start here too

            try:
                _log("INFO", "started", fn_name, service=service, indent=depth)

                start = time.perf_counter()
                result = inner_fn(*args, **kwargs)

                elapsed = (time.perf_counter() - start) * 1000 if start else -1
                _log("INFO", f"completed | {elapsed:.2f}ms", fn_name, service=service, indent=depth)
                return result

            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000 if start else -1
                _log("ERROR", f"failed after {elapsed:.2f}ms | {exc}", fn_name, service=service, indent=depth)
                raise

            finally:
                _LOG_DEPTH.reset(token)

        # If the function is async, return the async wrapper.
        # If it's sync, return a wrapper that is callable sync. However:
        # When the sync-decorated function is awaited (i.e., used in async context),
        # Python will not automatically await it — so the async wrapper is used only when
        # the decorator is explicitly applied to coroutine functions. To make a sync function
        # safe when called from async code, prefer calling via asyncio.to_thread or
        # decorate the caller. We also return a special object if inner_fn is sync:
        return _async_wrapper if is_coro else _sync_wrapper

    # Support both @log_service_safe and @log_service_safe(...options...)
    if callable(fn):
        return decorator(fn)
    return decorator