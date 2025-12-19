# app/exception_handlers.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.schemas.responses import ErrorResponse
from app.utils.logger import log_warning, log_exception


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    log_warning(
        message=f"{request.method} {request.url.path} | {exc.detail}",
        func_name="http_exception_handler",
        service = "http"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content = ErrorResponse(
            error=str(exc.detail),
        ).model_dump(),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    log_warning(
        message=f"{request.method} {request.url.path} | validation failed | {exc.errors()}",
        func_name="validation_exception_handler",
        service="http",
    )

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Invalid request payload",
        ).model_dump(),
    )

async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    log_exception(
        exc=exc,
        func_name="unhandled_exception_handler",
        service="exception",
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
        ).model_dump(),
    )