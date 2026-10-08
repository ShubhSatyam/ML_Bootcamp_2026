import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.meetings import router as meetings_router
from app.core.config import cors_origins

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="AI Meeting Assistant API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(meetings_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
