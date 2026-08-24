"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(title="RouteFlux", description="Dynamic traffic routing & rerouting engine", version="0.1.0")

# permissive CORS: local dev project, no auth/cookies involved
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.graph = None

app.include_router(router)
