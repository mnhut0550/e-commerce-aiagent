from dotenv import load_dotenv
from pathlib import Path

# Load .env from root (parent of backend folder)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    load_dotenv()
    print("⚠️ Using .env from current directory")

import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

from pydantic_settings import BaseSettings
from backend.database.db_models import Base, engine
from backend.routes.products import router as product_router
from backend.routes.orders import router as order_router
from backend.routes.assisstant import router as asisstant_router


# ==========================
# Settings
# ==========================
class Settings(BaseSettings):
    APP_NAME: str = "E-commerce Agent Demo "
    APP_VERSION: str = "0.0.0-alpha"
    DEBUG: bool = False
    CORS_ALLOW_CREDENTIALS: bool = False
    
    # String fields - read directly from .env without JSON parsing
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_METHODS_STR: str = "*"
    CORS_ALLOW_HEADERS_STR: str = "*"
    TRUSTED_HOSTS_STR: str = "*"

    # Properties to convert strings to lists
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [url.strip() for url in self.CORS_ORIGINS.split(',') if url.strip()]
    
    @property
    def CORS_ALLOW_METHODS(self) -> List[str]:
        return [m.strip() for m in self.CORS_ALLOW_METHODS_STR.split(',') if m.strip()]
    
    @property
    def CORS_ALLOW_HEADERS(self) -> List[str]:
        return [h.strip() for h in self.CORS_ALLOW_HEADERS_STR.split(',') if h.strip()]
    
    @property
    def TRUSTED_HOSTS(self) -> List[str]:
        return [h.strip() for h in self.TRUSTED_HOSTS_STR.split(',') if h.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env that aren't defined

settings = Settings()

print(f"✅ Settings initialized: CORS_ORIGINS={settings.CORS_ORIGINS_LIST}")


# ==========================
# Logger
# ==========================
logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# ==========================
# Lifespan hook
# ==========================
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    Base.metadata.create_all(engine, checkfirst=True)

    yield

    logger.info(f"🛑 Stopping {settings.APP_NAME}")


# ==========================
# FastAPI App
# ==========================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## 📘 API Documentation - E-commerce AI Agent Platform
    
    Đây là nền tảng cho phép:
    
    - 💬 **Sessions & Messages**: Tạo phiên làm việc, gửi/nhận tin nhắn.   
    
    """,
    contact={
        "name": "Nhut Nguyen Minh",
        "email": "nhutnhi@gmail.com",
    },
    debug=settings.DEBUG,
    lifespan=lifespan,
)


# ==========================
# Middleware
# ==========================
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# ==========================
# Exception handlers
# ==========================
@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status_code": 422, "message": "Validation Error", "data": None},
    )


# ==========================
# Health check & root
# ==========================

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        {
            "status_code": 200,
            "message": f"Welcome to {settings.APP_NAME}",
            "data": {"version": settings.APP_VERSION},
        }
    )


# ==========================
# Include routers
# ==========================
app.include_router(product_router, prefix="/api/products")
app.include_router(order_router, prefix="/api/orders")
app.include_router(asisstant_router, prefix= "/api/chat")