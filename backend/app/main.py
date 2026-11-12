from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

API_PREFIX = "/api/v1"

app = FastAPI(title="Weather App API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix=API_PREFIX)


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
