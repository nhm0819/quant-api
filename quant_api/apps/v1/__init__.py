from http.client import HTTPException
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.staticfiles import StaticFiles

from quant_api import apis
from quant_api.assemble import event
from quant_api.assemble import exception
from quant_api.assemble.middleware import cors_middleware


app = FastAPI(
    docs_url="/docs",
    middleware=[
        cors_middleware,
    ],
)

# add static files
current_path = Path(__file__).resolve().parent
static_path = current_path.parent.parent.joinpath("static")
static_files = StaticFiles(directory=static_path)
app.mount("/static", static_files, name="static")

# add events
app.add_event_handler("startup", event.startup_event_1)
app.add_event_handler("startup", event.startup_event_2)
app.add_event_handler("shutdown", event.shutdown_event)

# add exception handlers
app.add_exception_handler(Exception, exception.exception_handler)
app.add_exception_handler(HTTPException, exception.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, exception.validation_exception_handler
)

# add routers
app.include_router(apis.router, tags=["test"])
app.include_router(apis.v1.index.router, prefix="/v1")
app.include_router(apis.v1.klines.router, prefix="/v1")
app.include_router(apis.v1.klines_ws.router, prefix="/v1")
app.include_router(apis.v1.trades.router, prefix="/v1")
app.include_router(apis.v1.trades_ws.router, prefix="/v1")
