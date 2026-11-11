from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app import models  # importing this creates all tables
from app.routers import sessions, observations, issues, roads, complaints

# Creates all tables from the models
Base.metadata.create_all(bind=engine)

# ONE single app initialization!
app = FastAPI(
    title="RoadGuardian API",
    description="Backend for road-damage detection and complaint reporting",
    version="1.0.0",
)

# Open the gates for the Dashboard and Mobile App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows connections from any device on your Wi-Fi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(sessions.router)
app.include_router(observations.router)
app.include_router(issues.router)
app.include_router(roads.router)
app.include_router(complaints.router)

@app.get("/health", tags=["system"])
def health():
    """No API key needed — used to check the server is alive."""
    return {"status": "ok", "service": "road-guardian"}