from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger("hebrew_vocab_hub.errors")


def render_error(request: Request, templates: Jinja2Templates, status_code: int, detail):
    return templates.TemplateResponse(request,
        "error.html",
        {
            "status_code": status_code,
            "detail": detail,
        },
        status_code=status_code,
    )


def register_exception_handlers(app, templates: Jinja2Templates):

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):

        logger.warning(
            f"{request.method} {request.url.path} → {exc.status_code}: {exc.detail}"
        )

        # API → JSON
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

        # WEB → HTML
        return render_error(request, templates, exc.status_code, exc.detail)


    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):

        logger.warning(
            f"{request.method} {request.url.path} → 422 validation error"
        )

        # API → JSON
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors()},
            )

        # WEB → HTML
        return render_error(
            request,
            templates,
            422,
            exc.errors()[0]["msg"],
        )