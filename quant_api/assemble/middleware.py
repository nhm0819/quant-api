from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

allow_origins = ["*"]
allow_methods = ["*"]
allow_headers = ["*"]

cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
    allow_credentials=True,
)
