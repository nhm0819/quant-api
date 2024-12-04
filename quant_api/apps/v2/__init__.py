"""NOT IMPLEMENTED."""

from fastapi import FastAPI

from quant_api.assemble.middleware import cors_middleware

app = FastAPI(
    docs_url="/docs",
    middleware=[
        cors_middleware,
    ],
)
